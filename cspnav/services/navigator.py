"""실제 RAG 서비스. UI 프로토타입의 NavigatorService 인터페이스(get_status / list_products / get_product /
ask / recommend / explore)를 그대로 구현한다. (NF2005)

오래 걸리는 메서드는 on_progress(문구)로 진행 상태를 알린다. (F2012)
화면에 보내는 오류는 ServiceError의 사용자용 문구뿐이다. (NF2004)
"""

from __future__ import annotations

import logging
import threading
from typing import Callable, Optional

from cspnav import settings
from cspnav.data_prep import domain
from cspnav.data_prep.collector import Collector
from cspnav.data_prep.prices import load_servers, load_storages
from cspnav.data_prep.products import index_text, load_json, load_products
from cspnav.data_prep.sources import Candidate
from cspnav.errors import ServiceError
from cspnav.formatting import krw, support_text
from cspnav.rag import prompts
from cspnav.rag.citations import extract_cited
from cspnav.rag.graph import build_graph, generate_answer, retrieve_evidences
from cspnav.rag.llm import get_embeddings, invoke_json
from cspnav.schemas import (
    Answer,
    CspCandidate,
    Evidence,
    ExploreResult,
    Product,
    ProductHit,
    Recommendation,
    Requirement,
    ServerPrice,
    StoragePrice,
    SystemStatus,
)
from cspnav.services.cost import hours_per_month, monthly_estimate
from cspnav.services.design import DesignData, DesignResult, build_candidate, choose_best
from cspnav.services.filters import check_product, meta_where, needs_from
from cspnav.vectorstore.indexer import index_document
from cspnav.vectorstore.store import VectorStore

logger = logging.getLogger("cspnav.service")
Progress = Optional[Callable[[str], None]]

MSG_KEY = "LLM·임베딩 연결 설정(.env)이 비어 있어 답변을 만들 수 없습니다. 관리자에게 .env 설정을 요청하세요."
MSG_INDEX = "색인된 상품 데이터가 없습니다. 데이터 준비·색인 절차(README 3장)를 먼저 실행하세요."


class NavigatorService:
    """CSP Navigator 서비스 본체."""

    def __init__(self):
        self.env = settings.load_env()
        self.products: tuple[Product, ...] = load_products()
        self.by_id = {p.item_id: p for p in self.products}
        self.design_data = DesignData(self.products, load_servers(), load_storages(), load_json("csap.json"))
        self.store = VectorStore(embeddings=None)
        self._graph = None
        self._collector: Optional[Collector] = None
        self._lock = threading.Lock()   # 수집·색인은 한 번에 하나씩 (캐시 파일 보호)

    # ── 준비 상태 ────────────────────────────────────────
    def _ensure_ready(self) -> None:
        """키·색인이 없으면 사용자용 문구로 오류를 낸다. (F2012, NF2004)"""
        if not self.env.ready:
            raise ServiceError(MSG_KEY)
        if self.store.count(self.store.meta_name) == 0:
            raise ServiceError(MSG_INDEX)
        if self.store.embeddings is None:
            self.store.embeddings = get_embeddings()

    def _get_graph(self):
        if self._graph is None:
            self._graph = build_graph(self.store)
        return self._graph

    def _get_collector(self) -> Collector:
        if self._collector is None:
            self._collector = Collector(
                contact=self.env.contact,
                index_fn=lambda item_id, doc, kw: index_document(self.store, item_id, doc, kw),
                has_doc_fn=self.store.has_doc,
            )
        return self._collector

    def get_status(self) -> SystemStatus:
        """색인 건수와 API 키 상태. 키 값은 다루지 않고 비어 있는 항목 이름만 돌려준다. (F2002, F2012)"""
        meta, docs = self.store.counts()
        return SystemStatus(meta_count=meta, doc_chunk_count=docs, api_key_ready=self.env.ready,
                            missing_env=self.env.missing(), fake_mode=settings.fake_mode(),
                            product_count=len(self.products))

    def list_products(self, csp: Optional[str] = None, category: Optional[str] = None) -> list[Product]:
        """CSP·분류로 좁힌 상품 목록. (F2009)"""
        return [p for p in self.products
                if (csp is None or p.csp == csp) and (category is None or p.category == category)]

    def get_product(self, item_id: str) -> Optional[Product]:
        """상품 1건. (F2009)"""
        return self.by_id.get(item_id)

    # ── 상품 질의응답 ─────────────────────────────────────
    def ask(self, item_id: str, question: str, sector: str, on_progress: Progress = None) -> Answer:
        """선택 상품 근거 기반 답변. 검색어 추출 → 수집·색인 → retrieve → generate. (F2003~F2008, F2017)"""
        say = on_progress or (lambda _m: None)
        self._ensure_ready()
        product = self.by_id.get(item_id)
        if product is None:
            raise ServiceError("선택한 상품을 찾을 수 없습니다. 사이드바에서 다시 선택하세요.")
        question = (question or "").strip()
        if not question:
            raise ServiceError("질문을 입력하세요.")
        product_text = index_text(product)

        # ① 검색어 추출 (프롬프트1) — 같은 질문이면 이전 검색어를 다시 쓴다 (NF2002)
        cache = self._get_collector().cache
        keywords = cache.question_keywords(item_id, sector, question)
        if keywords:
            say("이전에 같은 질문으로 뽑은 검색어를 다시 사용합니다.")
        else:
            say("질문에서 외부 문서 검색어를 뽑고 있습니다.")
            max_kw = int(settings.get("collection.max_keywords", 4))
            raw = invoke_json(prompts.keyword_messages(product_text, sector, question, max_kw), "array") or []
            keywords = [k.strip() for k in raw if isinstance(k, str) and k.strip()][:max_kw] or [f"{product.csp} {product.name}"]
            cache.remember_question(item_id, sector, question, keywords)

        # ② 수집·선별·색인 (프롬프트2)
        def select(cands: list[Candidate]) -> list[str]:
            rows = [(c.cid, c.source_type, c.title, c.summary) for c in cands]
            max_sel = int(settings.get("collection.max_selected_docs", 3))
            picked = invoke_json(prompts.select_messages(question, product_text, rows, max_sel), "array") or []
            return [str(x) for x in picked][:max_sel]

        notices: list[str] = []
        with self._lock:
            report = self._get_collector().collect(product, keywords, select, on_progress=say)
        if report.cached_keywords and not report.new_keywords:
            say("이미 수집한 검색어라 캐시된 문서를 다시 사용합니다.")
            notices.append(f"이미 수집한 검색어 {len(report.cached_keywords)}개는 다시 수집하지 않고 캐시를 사용했습니다.")
        if report.official == "failed":
            notices.append("선택 상품의 공식 문서를 가져오지 못해(접속 제한·본문 없음 등) 상품 메타데이터와 기존 색인 문서로 답했습니다.")
        if report.skipped:
            notices.append("수집하지 않은 문서: " + "; ".join(report.skipped[:3]))

        # ③ retrieve → generate (LangGraph)
        say("상품 메타데이터와 외부 문서에서 근거를 찾아 합치고 있습니다.")
        state = self._get_graph().invoke({"item_id": item_id, "question": question, "sector": sector,
                                          "extra_context": self._product_cost_context(product)})
        say("근거를 바탕으로 답변을 만들었습니다.")
        return Answer(text=state["answer"], evidences=state.get("evidences", []), cited=state.get("cited", []),
                      notices=notices)

    @staticmethod
    def _product_cost_context(product: Product) -> str:
        """선택 상품의 예상 월 비용을 코드로 계산해 프롬프트3에 넘긴다. LLM이 환산·곱셈을 직접 하다
        틀린 사례(37.96 USD → '약 50,075원', 실제 50,640원)를 2026-10-23 검증에서 확인해 추가했다. (F2018)"""
        est, basis = monthly_estimate(product)
        if est is None:
            return f"선택 상품 예상 월 비용: 코드로 계산할 수 없음({basis}). 금액을 새로 계산하지 말 것."
        unit = {"hour": "원/시간", "gb_month": "원/GB·월"}.get(product.billing_unit, "원")
        formula = (f"{product.unit_price:,.2f}{unit} × {hours_per_month()}시간 = {krw(est)}"
                   if product.billing_unit == "hour" and basis != "공식 월 요금" else f"{krw(est)} ({basis})")
        return (f"선택 상품 예상 월 비용(코드 계산, VAT 별도): {formula}. 기준: {basis}, 환율·단가는 [근거 1]의 값. "
                "원화 금액이 필요하면 이 값만 쓴다.")

    # ── CSP 추천·설계 ─────────────────────────────────────
    def recommend(self, req: Requirement, sector: str, on_progress: Progress = None) -> Recommendation:
        """CSP 추천·인프라 설계. 후보 비교·부문 필터·비용은 코드, 이유 문장은 프롬프트3. (F2010, F2017, F2018)"""
        say = on_progress or (lambda _m: None)
        self._ensure_ready()
        say("요구사항을 상품 구성으로 바꾸고 CSP별 후보 상품을 찾고 있습니다.")
        results: list[DesignResult] = [build_candidate(csp, req, sector, self.design_data) for csp in domain.CSPS]
        candidates = [r.candidate for r in results]
        say("부문 조건을 적용하고 예상 월 비용을 비교하고 있습니다.")
        best = choose_best(candidates, sector)
        if best is None:
            text = (f"{prompts.NOT_FOUND}. 입력한 조건을 모두 만족하는 CSP 후보를 색인된 근거에서 찾지 못했습니다. "
                    "'CSP 후보 비교' 탭의 제외 사유를 확인하고 조건을 조정해 보세요.")
            return Recommendation(req, sector, candidates, None, Answer(text=text))

        chosen = next(r for r in results if r.candidate.csp == best.csp)
        pinned, line_refs = self._line_evidences(chosen)
        say("부문 요건 문서에서 근거를 찾고 있습니다.")
        query = (f"{domain.SECTORS.get(sector, sector)} 부문 {req.workload} {' '.join(req.security)} "
                 f"{best.csp} 클라우드 요금 보안인증 폐쇄망 {req.note}")
        evidences = retrieve_evidences(self.store, query, sector, item_id=None, pinned=pinned)
        context = self._cost_context(candidates, best, line_refs, req)
        question = (
            f"요구사항: 워크로드 {req.workload}, 서버 {req.instances}대 × {req.vcpu}vCPU/{req.memory_gb}GB, "
            f"DB {'포함' if req.need_db else '없음'}, 오브젝트 스토리지 {req.storage_gb}GB, 월 {req.hours}시간, "
            f"월 예산 {krw(req.budget)}, 보안·연결 조건 {', '.join(req.security) or '없음'}"
            + (f", 공공 시스템 등급 {req.data_grade}" if sector == "public" else "")
            + (f", 추가 요구사항 {req.note}" if req.note else "") + ".\n"
            f"계산 결과 추천 CSP는 {best.csp}다. 왜 {best.csp}인지, 설계안 구성(상품별 역할과 월 비용), "
            "다른 후보와의 비용 차이, '확인 필요' 항목과 부문 요건 주의점을 근거 번호와 함께 설명하라."
        )
        say("추천 이유를 근거와 함께 정리하고 있습니다.")
        notices: list[str] = []
        try:
            text, cited = generate_answer(question, sector, evidences, context)
        except ServiceError as err:
            logger.warning("추천 이유 생성 실패: %s", err.user_message)
            text = self._fallback_reason(best, line_refs)
            cited = extract_cited(text, evidences)
            notices.append("추천 이유 문장을 LLM으로 만들지 못해 계산 결과만 정리했습니다.")
        return Recommendation(req, sector, candidates, best.csp, Answer(text, evidences, cited, notices))

    def _line_evidences(self, chosen: DesignResult) -> tuple[list[Evidence], dict[str, int]]:
        """설계안 각 줄의 단가 출처를 근거로 만든다. (줄 item_id → 근거 번호). (F2008, F2018)"""
        evidences: list[Evidence] = []
        refs: dict[str, int] = {}
        servers = {s.price_id: s for s in chosen.servers_used}
        storages = {s.storage_id: s for s in chosen.storages_used}
        products = {p.item_id: p for p in chosen.products_used}
        for line in chosen.candidate.lines:
            if line.item_id in refs:
                continue
            n = len(evidences) + 1
            if line.item_id in products:
                p = products[line.item_id]
                content = index_text(p)
                ev = Evidence(n, "meta", f"{p.csp} {p.name}", p.source_url, p.checked_at, p.csp, p.item_id,
                              snippet=line.formula, chunk_id=p.item_id, content=content)
            elif line.item_id in servers:
                ev = Evidence(n, "price", f"서버 가격표 {line.item_id}", line.source_url, line.checked_at,
                              chosen.candidate.csp, line.item_id, snippet=line.formula,
                              content=_server_text(servers[line.item_id]))
            else:
                s = storages.get(line.item_id)
                ev = Evidence(n, "price", f"Block Storage 단가표 {line.item_id}", line.source_url, line.checked_at,
                              chosen.candidate.csp, line.item_id, snippet=line.formula,
                              content=_storage_text(s) if s else line.formula)
            evidences.append(ev)
            refs[line.item_id] = n
        return evidences, refs

    @staticmethod
    def _cost_context(candidates: list[CspCandidate], best: CspCandidate, refs: dict[str, int], req: Requirement) -> str:
        """프롬프트3에 넣는 코드 계산 결과. LLM은 이 숫자만 쓴다. (F2018)"""
        rows = [f"추천 CSP: {best.csp} / 예상 월 합계 {krw(best.monthly_total)} / 월 예산 {krw(req.budget)} / "
                f"예산 {'이내' if best.within_budget else '초과'}",
                "설계안(추천 CSP):"]
        for line in best.lines:
            rows.append(f"- {line.product_name}: {line.formula} [근거 {refs.get(line.item_id, '?')}]")
        if best.unknown_items:
            rows.append("확인 필요 항목: " + ", ".join(best.unknown_items))
        for note in best.notes:
            rows.append(f"참고: {note}")
        rows.append("다른 후보:")
        for c in sorted(candidates, key=lambda c: (not c.eligible, c.monthly_total)):
            if c.csp == best.csp:
                continue
            if c.eligible:
                rows.append(f"- {c.csp}: 예상 월 {krw(c.monthly_total)} (추천안 대비 {krw(c.monthly_total - best.monthly_total)} 차이)")
            else:
                rows.append(f"- {c.csp}: 제외 — {'; '.join(c.excluded_reasons)}")
        return "\n".join(rows)

    @staticmethod
    def _fallback_reason(best: CspCandidate, refs: dict[str, int]) -> str:
        """LLM 실패 시 코드로 만드는 요약(근거 번호 포함). (F2010, F2012)"""
        lines = [f"조건을 만족하는 후보 중 예상 월 비용이 가장 낮은 **{best.csp}**를 추천합니다(계산 결과)."]
        for line in best.lines:
            lines.append(f"- {line.product_name}: 월 {krw(line.subtotal)} [근거 {refs.get(line.item_id, 1)}]")
        if best.unknown_items:
            lines.append("- 확인 필요: " + ", ".join(best.unknown_items))
        return "\n".join(lines)

    # ── 조건 탐색 ─────────────────────────────────────────
    def explore(self, query: str, sector: str, on_progress: Progress = None) -> ExploreResult:
        """자연어 조건 → 메타 색인 검색(부문 필터 적용) → LLM이 조건에 맞는 상품만 선택 → 금액 조건은 코드로 비교. (F2011, F2017)"""
        say = on_progress or (lambda _m: None)
        self._ensure_ready()
        query = (query or "").strip()
        if not query:
            raise ServiceError("찾는 조건을 입력하세요.")
        say("상품 메타데이터에서 후보를 찾고 있습니다.")
        k = int(settings.get("explore.candidate_k", 30))
        hits = self.store.search("meta", query, k, where=meta_where(sector), search_type="similarity")
        cand_products = [self.by_id[d.metadata.get("item_id")] for d, _ in hits if d.metadata.get("item_id") in self.by_id]
        sector_conditions = [f"부문: {domain.SECTORS.get(sector, sector)}"]
        if not cand_products:
            return ExploreResult(conditions=sector_conditions, hits=[])

        say("조건에 맞는 상품을 고르고 있습니다.")
        rows = []
        for p in cand_products:
            est, basis = monthly_estimate(p)
            rows.append(
                f"- item_id: {p.item_id} | {p.csp} | {p.name} | {domain.CATEGORIES.get(p.category)} | 사양 {p.spec} | "
                f"요금 {p.price_text} | 예상 월 {krw(est)}({basis}) | 리전 {p.region} | "
                f"공공 {support_text(p.public_support)} | 폐쇄망 {support_text(p.closed_network_support)} | "
                f"무료 {support_text(p.free_tier)}"
            )
        result = invoke_json(prompts.explore_messages(query, sector, "\n".join(rows)), "object") or {}
        conditions = [str(c) for c in result.get("conditions", []) if str(c).strip()]
        limit = _num(result.get("max_monthly_krw"))
        min_vcpu = _num(result.get("min_vcpu"))          # 사양 조건도 코드로 비교한다(2026-10-23 검증에서
        min_mem = _num(result.get("min_memory_gb"))      # LLM이 '제외'라고 적은 상품을 matches에 넣은 사례 확인)

        need_public, need_closed = needs_from(sector, [])
        allowed = {p.item_id for p in cand_products}
        out: list[ProductHit] = []
        for m in result.get("matches", []) or []:
            item_id = str(m.get("item_id", "")) if isinstance(m, dict) else str(m)
            if item_id not in allowed or any(h.product.item_id == item_id for h in out):
                continue
            p = self.by_id[item_id]
            status = check_product(p, need_public, need_closed)
            if status == "fail":
                continue
            if min_vcpu is not None and (p.vcpu is None or p.vcpu < min_vcpu):
                continue
            if min_mem is not None and (p.memory_gb is None or p.memory_gb < min_mem):
                continue
            est, basis = monthly_estimate(p)
            if limit is not None and (est is None or est > limit):
                continue
            reason = str(m.get("reason", "")) if isinstance(m, dict) else ""
            out.append(ProductHit(p, est, basis, status, reason))
        out.sort(key=lambda h: (h.monthly_estimate is None, h.monthly_estimate or 0))
        if limit is not None:
            conditions.append(f"월 {krw(limit)} 이하(코드로 비교)")
        if min_vcpu is not None:
            conditions.append(f"vCPU {min_vcpu:g}개 이상(코드로 비교)")
        if min_mem is not None:
            conditions.append(f"메모리 {min_mem:g}GB 이상(코드로 비교)")
        return ExploreResult(conditions=conditions + sector_conditions,
                             hits=out[: int(settings.get("explore.max_hits", 12))])


def _num(value) -> Optional[float]:
    """LLM JSON의 숫자 칸을 float로 읽는다. 없거나 숫자가 아니면 None. (F2011)"""
    try:
        return float(value) if value not in (None, "", "null") else None
    except (TypeError, ValueError):
        return None


def _server_text(s: ServerPrice) -> str:
    price = f"시간당 {s.hourly_orig:g} {s.currency}" if s.hourly_orig is not None else "시간 단가 없음"
    monthly = f", 공식 월 요금 {s.monthly_orig:,.0f} {s.currency}" if s.monthly_orig is not None else ""
    return (f"서버 가격표 {s.price_id}: {s.csp} {s.platform} {s.server_type}, {s.vcpu:g}vCPU / {s.memory_gb:g}GB, "
            f"{price}{monthly}, 디스크 {s.included_disk}, 비고 {s.note or '-'}, 온디맨드·Linux·VAT 별도, "
            f"출처 {s.source_url}, 확인일 {s.checked_at.isoformat()}")


def _storage_text(s: StoragePrice) -> str:
    return (f"Block Storage 단가표 {s.storage_id}: {s.csp} {s.storage_type}, 원문 {s.unit_text}, "
            f"GB-월 환산 {s.per_gb_month_orig:g} {s.currency}, 비고 {s.note or '-'}, 출처 {s.source_url}, "
            f"확인일 {s.checked_at.isoformat()}")
