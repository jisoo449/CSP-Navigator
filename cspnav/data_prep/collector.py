"""외부 문서 수집 흐름(프롬프트2 선별 포함)과 수집 캐시. (F2003, F2004, F2016, NF2002, NF2006)

흐름
1. 선택 상품의 공식 문서(source_url)는 선별·길이 규칙과 관계없이 항상 수집한다(이미 색인돼 있으면 건너뜀).
2. 아직 수집하지 않은 검색어마다 출처별(web/pdf/wiki) 후보를 모은다.
3. 선별 프롬프트(프롬프트2)가 제목·요약만 보고 색인할 문서를 고른다.
4. 고른 문서의 본문과 원문 출처를 저장하고 색인한다. 검색어·문서는 캐시에 남겨 다시 수집하지 않는다.

캐시
- data/cache/collect_cache.json : {"keywords": {"항목ID|검색어": [문서ID, ...]}, "failures": {URL: 사유}}
- data/cache/docs/<문서ID>.json : 문서 본문(다른 상품에서 같은 문서를 고르면 네트워크 없이 다시 쓴다)
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Optional

from cspnav import settings
from cspnav.data_prep import sources
from cspnav.data_prep.http_client import PoliteClient
from cspnav.data_prep.sources import Candidate, CollectedDoc
from cspnav.schemas import Product

logger = logging.getLogger("cspnav.collector")
Progress = Optional[Callable[[str], None]]


@dataclass
class CollectReport:
    """수집 결과 요약. 화면 안내(F2012)와 점검에 쓴다."""

    official: str = ""                       # indexed / cached / failed / skipped
    new_keywords: list[str] = field(default_factory=list)
    cached_keywords: list[str] = field(default_factory=list)
    candidates: int = 0
    selected: list[str] = field(default_factory=list)
    indexed_docs: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


class CollectCache:
    """검색어·문서 캐시 파일. (NF2002)"""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.dir = cache_dir or settings.resolve_path("cache_dir")
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / "docs").mkdir(exist_ok=True)
        self.path = self.dir / "collect_cache.json"
        self.data = {"keywords": {}, "questions": {}, "failures": {}}
        if self.path.exists():
            try:
                self.data.update(json.loads(self.path.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                logger.warning("수집 캐시 파일이 깨져 새로 시작합니다: %s", self.path)

    def save(self) -> None:
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=1), encoding="utf-8")

    @staticmethod
    def _key(item_id: str, keyword: str) -> str:
        return f"{item_id}|{keyword.strip().lower()}"

    def has_keyword(self, item_id: str, keyword: str) -> bool:
        return self._key(item_id, keyword) in self.data["keywords"]

    def mark_keyword(self, item_id: str, keyword: str, doc_ids: list[str]) -> None:
        self.data["keywords"][self._key(item_id, keyword)] = doc_ids

    # 같은 상품·부문·질문이면 프롬프트1이 뽑았던 검색어를 그대로 다시 쓴다. LLM이 매번 검색어를 조금씩
    # 다르게 뽑아 재질문 때 수집이 다시 일어나던 문제(2026-10-23 실제 검증)를 막는다. (NF2002, F2003)
    @staticmethod
    def _qkey(item_id: str, sector: str, question: str) -> str:
        return f"{item_id}|{sector}|{' '.join(question.split()).lower()}"

    def question_keywords(self, item_id: str, sector: str, question: str) -> Optional[list[str]]:
        return self.data.setdefault("questions", {}).get(self._qkey(item_id, sector, question))

    def remember_question(self, item_id: str, sector: str, question: str, keywords: list[str]) -> None:
        self.data.setdefault("questions", {})[self._qkey(item_id, sector, question)] = list(keywords)

    def load_doc(self, doc_id: str) -> Optional[CollectedDoc]:
        path = self.dir / "docs" / f"{doc_id}.json"
        if not path.exists():
            return None
        raw = json.loads(path.read_text(encoding="utf-8"))
        raw["pages"] = [tuple(p) for p in raw.get("pages", [])]
        return CollectedDoc(**raw)

    def store_doc(self, doc: CollectedDoc) -> None:
        path = self.dir / "docs" / f"{doc.doc_id}.json"
        path.write_text(json.dumps(asdict(doc), ensure_ascii=False), encoding="utf-8")

    def mark_failure(self, ref: str, reason: str) -> None:
        self.data["failures"][ref] = reason


class Collector:
    """출처 3종(web/pdf/wiki) 수집기. 색인 함수와 선별 함수는 밖에서 받는다(모듈 분리, NF2005)."""

    def __init__(self, contact: str, index_fn: Callable[[str, CollectedDoc, str], int],
                 has_doc_fn: Callable[[str, str], bool]):
        self.client = PoliteClient(contact)
        self.cache = CollectCache()
        self.index_fn = index_fn
        self.has_doc_fn = has_doc_fn
        self.enabled = set(settings.get("collection.sources", ["web", "pdf", "wiki"]))

    # ── 문서 가져오기(캐시 우선) ──────────────────────────
    def _fetch(self, cand: Candidate) -> Optional[CollectedDoc]:
        doc_id = sources.doc_id_for(cand.source_type, cand.ref)
        cached = self.cache.load_doc(doc_id)
        if cached:
            return cached
        if settings.offline_mode() and cand.source_type != "pdf":
            return None
        try:
            if cand.source_type == "web":
                doc = sources.fetch_web(self.client, cand)
            elif cand.source_type == "wiki":
                doc = sources.fetch_wiki(self.client, cand)
            else:
                doc = sources.fetch_pdf(cand)
        except Exception as exc:  # noqa: BLE001 — 한 문서 실패로 전체를 멈추지 않는다
            logger.warning("문서 수집 실패 %s: %s", cand.ref, type(exc).__name__)
            self.cache.mark_failure(cand.ref, type(exc).__name__)
            return None
        if doc is None:
            self.cache.mark_failure(cand.ref, "본문 없음 또는 robots.txt 불허")
            return None
        max_chars = int(settings.get("collection.max_body_chars", 30000))
        if doc.body and len(doc.body) > max_chars:
            doc.body = doc.body[:max_chars]
        self.cache.store_doc(doc)
        return doc

    # ── 후보 모으기 ──────────────────────────────────────
    def _candidates(self, keyword: str, exclude_urls: set[str]) -> list[Candidate]:
        limit = int(settings.get("collection.candidates_per_source", 4))
        out: list[Candidate] = []
        if "web" in self.enabled:
            out += sources.web_candidates(keyword, limit, exclude_urls)
        if "pdf" in self.enabled:
            out += sources.pdf_candidates(keyword, limit)
        if "wiki" in self.enabled and not settings.offline_mode():
            try:
                out += sources.wiki_candidates(self.client, keyword, limit)
            except Exception as exc:  # noqa: BLE001
                logger.warning("위키백과 검색 실패(%s): %s", keyword, type(exc).__name__)
        return out

    # ── 전체 흐름 ────────────────────────────────────────
    def collect(self, product: Product, keywords: list[str], select_fn: Callable[[list[Candidate]], list[str]],
                on_progress: Progress = None) -> CollectReport:
        """선택 상품 기준으로 외부 문서를 수집·색인한다. select_fn은 프롬프트2 선별 함수. (F2004)"""
        report = CollectReport()
        say = on_progress or (lambda _m: None)

        # 1) 선택 상품의 공식 문서 — 선별·길이 규칙 없이 항상 (F2004)
        if product.source_url:
            official = Candidate(cid="official", source_type="web", title=f"{product.csp} 공식 문서: {product.name}",
                                 summary="선택 상품의 공식 요금·상품 페이지", ref=product.source_url, csp=product.csp,
                                 official=True, license="CSP 이용약관·robots.txt 확인 필요(미결 #3)")
            official_id = sources.doc_id_for("web", product.source_url)
            if self.has_doc_fn(product.item_id, official_id):
                report.official = "cached"
            else:
                say("선택 상품의 공식 문서를 가져오고 있습니다.")
                doc = self._fetch(official)
                if doc and doc.length > 0:
                    doc.title = official.title
                    self.index_fn(product.item_id, doc, "(공식 문서)")
                    report.official = "indexed"
                    report.indexed_docs.append(doc.doc_id)
                else:
                    report.official = "failed"

        # 2) 새 검색어만 후보 수집 (NF2002)
        for kw in keywords:
            (report.cached_keywords if self.cache.has_keyword(product.item_id, kw) else report.new_keywords).append(kw)
        if not report.new_keywords:
            self.cache.save()
            return report

        say(f"새 검색어 {len(report.new_keywords)}개로 외부 문서 후보를 모으고 있습니다.")
        pool: dict[str, tuple[Candidate, str]] = {}
        for kw in report.new_keywords:
            for cand in self._candidates(kw, exclude_urls={product.source_url}):
                key = f"{cand.source_type}:{cand.ref}"
                if key not in pool:
                    pool[key] = (cand, kw)
        cands = []
        for i, (cand, kw) in enumerate(pool.values(), start=1):
            cand.cid = f"c{i}"
            cands.append((cand, kw))
        report.candidates = len(cands)

        # 3) 프롬프트2 선별 (제목·요약만)
        selected_ids: list[str] = []
        if cands:
            say(f"후보 {len(cands)}건 중 색인할 문서를 고르고 있습니다.")
            selected_ids = select_fn([c for c, _ in cands])
        by_cid = {c.cid: (c, kw) for c, kw in cands}
        report.selected = [cid for cid in selected_ids if cid in by_cid]

        # 4) 본문 수집·길이 규칙·색인
        min_chars = int(settings.get("collection.min_body_chars", 300))
        kw_docs: dict[str, list[str]] = {kw: [] for kw in report.new_keywords}
        if report.selected:
            say(f"선택한 문서 {len(report.selected)}건의 본문을 수집·색인하고 있습니다.")
        for cid in report.selected:
            cand, kw = by_cid[cid]
            doc = self._fetch(cand)
            if doc is None:
                report.skipped.append(f"{cand.title}: 수집 실패")
                continue
            if doc.length < min_chars:
                report.skipped.append(f"{cand.title}: 본문이 너무 짧음({doc.length}자)")
                continue
            if not self.has_doc_fn(product.item_id, doc.doc_id):
                self.index_fn(product.item_id, doc, kw)
                report.indexed_docs.append(doc.doc_id)
            kw_docs[kw].append(doc.doc_id)

        for kw, ids in kw_docs.items():
            self.cache.mark_keyword(product.item_id, kw, ids)
        self.cache.save()
        return report
