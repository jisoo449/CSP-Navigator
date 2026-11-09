"""출처별 후보 찾기와 본문 가져오기: CSP 공식 웹 문서 / PDF / 한국어 위키백과. (F2004, F2016, NF2006, NF2007)

출처마다 수집 방식이 다르다.
- web  : web_catalog.json(공식 요금 페이지·법령 원문)에서 검색어와 겹치는 후보를 고르고, robots.txt 확인 후 HTML을 받아 본문 텍스트만 뽑는다.
- pdf  : data/pdf/catalog.json에 등록한 파일만 쓴다(이용 조건을 사람이 확인하고 등록). 쪽 단위로 텍스트를 뽑는다.
- wiki : MediaWiki API 검색(list=search)으로 후보를, 평문 추출(prop=extracts)로 본문을 받는다. 라이선스 CC BY-SA 4.0.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from cspnav import settings
from cspnav.data_prep.http_client import PoliteClient
from cspnav.data_prep.products import load_json

logger = logging.getLogger("cspnav.sources")

WIKI_API = "https://ko.wikipedia.org/w/api.php"
WIKI_LICENSE = "CC BY-SA 4.0 (한국어 위키백과, 출처·라이선스 표기 필요)"


@dataclass
class Candidate:
    """선별 프롬프트(프롬프트2)에 보여 줄 후보. 제목·요약만 쓴다. (F2004)"""

    cid: str
    source_type: str          # web / pdf / wiki
    title: str
    summary: str
    ref: str                  # URL / PDF 파일명 / 위키 문서 제목
    csp: str = ""
    sectors: list[str] = field(default_factory=lambda: ["public", "private", "learning"])
    license: str = ""
    official: bool = False    # 선택 상품의 공식 문서 여부 (선별·길이 규칙 무시)


@dataclass
class CollectedDoc:
    """수집한 문서 1개. 색인 전 단계. (F2004)"""

    doc_id: str
    source_type: str
    title: str
    source: str               # URL 또는 파일명
    body: str = ""
    pages: list[tuple[int, str]] = field(default_factory=list)   # PDF 전용
    csp: str = ""
    sectors: list[str] = field(default_factory=list)
    license: str = ""
    collected_at: str = field(default_factory=lambda: date.today().isoformat())

    @property
    def length(self) -> int:
        return len(self.body) if not self.pages else sum(len(t) for _, t in self.pages)


def doc_id_for(source_type: str, ref: str) -> str:
    """출처 종류 + 참조값으로 문서 ID를 고정한다. 같은 문서는 항상 같은 ID. (F2005, NF2002)"""
    return f"{source_type}-{hashlib.sha1(ref.encode('utf-8')).hexdigest()[:10]}"


# ── HTML → 본문 텍스트 ───────────────────────────────────
class _TextExtractor(HTMLParser):
    """script·style·nav·footer 등을 빼고 본문 텍스트만 모은다."""

    SKIP = {"script", "style", "noscript", "svg", "nav", "footer", "header", "form", "button", "iframe"}
    BLOCK = {"p", "div", "li", "tr", "br", "h1", "h2", "h3", "h4", "h5", "h6", "section", "article", "table", "dd", "dt"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.title = ""
        self._skip = 0
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip += 1
        elif tag == "title":
            self._in_title = True
        elif tag in self.BLOCK:
            self.parts.append("\n")
        elif tag in ("td", "th"):
            self.parts.append(" | ")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self._skip:
            self._skip -= 1
        elif tag == "title":
            self._in_title = False
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif not self._skip:
            self.parts.append(data)


def html_to_text(html: str) -> tuple[str, str]:
    """HTML → (제목, 본문). 공백을 정리한다."""
    parser = _TextExtractor()
    parser.feed(html)
    text = "".join(parser.parts)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    text = "\n".join(ln.strip(" |") for ln in text.split("\n"))
    return re.sub(r"\s+", " ", parser.title).strip(), re.sub(r"\n{3,}", "\n\n", text).strip()


# ── 검색어 겹침 점수 ─────────────────────────────────────
def _tokens(text: str) -> set[str]:
    return {t for t in re.split(r"[^0-9A-Za-z가-힣]+", text.lower()) if len(t) >= 2}


def overlap_score(keyword: str, text: str) -> float:
    kw = _tokens(keyword)
    if not kw:
        return 0.0
    return len(kw & _tokens(text)) / len(kw)


# ── web ─────────────────────────────────────────────────
def web_candidates(keyword: str, limit: int, exclude_urls: set[str]) -> list[Candidate]:
    """web_catalog.json에서 검색어와 겹치는 후보. (F2004)"""
    scored = []
    for entry in load_json("web_catalog.json"):
        if entry["url"] in exclude_urls:
            continue
        score = overlap_score(keyword, f"{entry['title']} {entry['summary']} {entry.get('csp', '')}")
        if score > 0:
            scored.append((score, entry))
    scored.sort(key=lambda x: -x[0])
    return [
        Candidate(cid="", source_type="web", title=e["title"], summary=e["summary"], ref=e["url"],
                  csp=e.get("csp", ""), sectors=e.get("sectors") or ["public", "private", "learning"],
                  license=e.get("license", ""))
        for _, e in scored[:limit]
    ]


def fetch_web(client: PoliteClient, cand: Candidate) -> Optional[CollectedDoc]:
    """robots.txt 확인 → HTML 수집 → 본문 추출. 허용되지 않거나 실패하면 None. (F2004, NF2006)"""
    url = cand.ref
    if not client.allowed(url):
        logger.info("robots.txt 불허 또는 확인 불가: %s", url)
        return None
    resp = client.get(url)
    ctype = resp.headers.get("Content-Type", "")
    if "html" not in ctype and "text" not in ctype:
        return None
    resp.encoding = resp.encoding or resp.apparent_encoding
    page_title, body = html_to_text(resp.text)
    return CollectedDoc(doc_id=doc_id_for("web", url), source_type="web", title=cand.title or page_title,
                        source=url, body=body, csp=cand.csp, sectors=cand.sectors, license=cand.license)


# ── wiki ────────────────────────────────────────────────
def wiki_candidates(client: PoliteClient, keyword: str, limit: int) -> list[Candidate]:
    """MediaWiki 검색 API로 후보(제목·요약 스니펫). (F2004, F2016)

    전문 검색은 본문에 단어가 한 번만 나와도 걸려 '유튜브'·'기후변화' 같은 무관한 문서가 섞인다
    (2026-10-23 실제 검증에서 확인). 그래서 limit의 3배를 받아 검색어와 제목·스니펫의 단어 겹침으로
    다시 순위를 매기고, 제목이 겹치지 않으면서 스니펫 겹침도 절반 미만인 문서는 버린다.
    """
    data = client.get(WIKI_API, params={
        "action": "query", "list": "search", "srsearch": keyword, "srlimit": limit * 3,
        "format": "json", "formatversion": 2,
    }).json()
    scored = []
    for hit in data.get("query", {}).get("search", []):
        snippet = re.sub(r"<[^>]+>", "", hit.get("snippet", ""))
        title_score = overlap_score(keyword, hit["title"])
        snip_score = overlap_score(keyword, snippet)
        if title_score == 0 and snip_score < 0.5:
            continue
        scored.append((title_score * 2 + snip_score, hit["title"], snippet))
    scored.sort(key=lambda x: -x[0])
    return [Candidate(cid="", source_type="wiki", title=title, summary=snippet, ref=title, license=WIKI_LICENSE)
            for _, title, snippet in scored[:limit]]


def fetch_wiki(client: PoliteClient, cand: Candidate) -> Optional[CollectedDoc]:
    """위키백과 문서 평문 추출. 절 제목은 '== 제목 ==' 형태로 남는다. (F2016)"""
    data = client.get(WIKI_API, params={
        "action": "query", "prop": "extracts", "explaintext": 1, "titles": cand.ref,
        "format": "json", "formatversion": 2, "redirects": 1,
    }).json()
    pages = data.get("query", {}).get("pages", [])
    if not pages or "extract" not in pages[0]:
        return None
    title = pages[0].get("title", cand.ref)
    url = "https://ko.wikipedia.org/wiki/" + quote(title.replace(" ", "_"))
    return CollectedDoc(doc_id=doc_id_for("wiki", title), source_type="wiki", title=f"위키백과: {title}",
                        source=url, body=pages[0]["extract"], sectors=cand.sectors, license=WIKI_LICENSE)


# ── pdf ─────────────────────────────────────────────────
def pdf_dir() -> Path:
    return settings.resolve_path("pdf_dir")


def load_pdf_catalog() -> list[dict]:
    """data/pdf/catalog.json — 사람이 이용 조건을 확인하고 등록한 PDF만 쓴다. (NF2007)"""
    path = pdf_dir() / "catalog.json"
    if not path.exists():
        return []
    items = json.loads(path.read_text(encoding="utf-8")).get("items", [])
    return [i for i in items if (pdf_dir() / i.get("file", "")).exists() and i.get("use", True)]


def extract_pdf_pages(path: Path) -> list[tuple[int, str]]:
    """PDF → [(쪽 번호(1부터), 텍스트)]. 텍스트가 없는 쪽(스캔본)은 건너뛴다. (F2016)"""
    from pypdf import PdfReader  # 지연 import: PDF를 안 쓰면 설치하지 않아도 된다

    reader = PdfReader(str(path))
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append((i, text))
    return pages


def _pdf_text_cache(entry: dict) -> list[tuple[int, str]]:
    """PDF 쪽 텍스트를 data/cache/pdf_text/에 저장해 두고 다시 쓴다. (NF2002)"""
    cache_dir = settings.resolve_path("cache_dir") / "pdf_text"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache = cache_dir / (entry["file"] + ".json")
    if cache.exists():
        return [tuple(x) for x in json.loads(cache.read_text(encoding="utf-8"))]
    pages = extract_pdf_pages(pdf_dir() / entry["file"])
    cache.write_text(json.dumps(pages, ensure_ascii=False), encoding="utf-8")
    return pages


def pdf_candidates(keyword: str, limit: int) -> list[Candidate]:
    """등록된 PDF 중 제목·요약·본문 앞부분에 검색어가 겹치는 것. (F2004)"""
    scored = []
    for entry in load_pdf_catalog():
        try:
            pages = _pdf_text_cache(entry)
        except Exception:  # noqa: BLE001 — 깨진 PDF는 후보에서 뺀다
            logger.exception("PDF 텍스트 추출 실패: %s", entry.get("file"))
            continue
        head = " ".join(t for _, t in pages[:5])[:4000]
        summary = entry.get("summary") or head[:200]
        score = overlap_score(keyword, f"{entry.get('title', '')} {summary} {head}")
        if score > 0:
            scored.append((score, entry, summary))
    scored.sort(key=lambda x: -x[0])
    return [
        Candidate(cid="", source_type="pdf", title=e.get("title", e["file"]), summary=s, ref=e["file"],
                  sectors=e.get("sectors") or ["public"], license=e.get("license", "확인 필요"))
        for _, e, s in scored[:limit]
    ]


def fetch_pdf(cand: Candidate) -> Optional[CollectedDoc]:
    """등록된 PDF의 쪽 텍스트. (F2016)"""
    entry = next((e for e in load_pdf_catalog() if e["file"] == cand.ref), None)
    if entry is None:
        return None
    pages = _pdf_text_cache(entry)
    return CollectedDoc(doc_id=doc_id_for("pdf", cand.ref), source_type="pdf", title=cand.title,
                        source=cand.ref, pages=pages, sectors=cand.sectors, license=cand.license)
