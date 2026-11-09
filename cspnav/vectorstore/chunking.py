"""출처 종류별 청킹. (F2005, F2016)

출처마다 문서 구조가 달라 구분자를 다르게 둔다. 크기·중복 길이는 settings.json(chunking.<종류>)에서 읽는다.
- web     : 웹 본문에서 뽑은 텍스트. 빈 줄·줄바꿈·문장 끝 순으로 자른다.
- wiki    : 위키백과 평문(explaintext). '== 절 제목 ==' 경계를 먼저 존중한다.
- pdf     : 쪽 단위로 먼저 나눈 뒤 쪽 안에서 자른다. 청크가 두 쪽에 걸치지 않아 '파일명 · n쪽' 출처가 정확하다.
- summary : 수집 결과 요약(공통 문서). 줄 단위 사실 나열이라 줄바꿈을 먼저 쓴다.
"""

from __future__ import annotations

from langchain_text_splitters import RecursiveCharacterTextSplitter

from cspnav import settings

_SEPARATORS = {
    "web": ["\n\n", "\n", ". ", "다. ", " ", ""],
    "wiki": ["\n== ", "\n=== ", "\n\n", "\n", ". ", "다. ", " ", ""],
    "pdf": ["\n\n", "\n", ". ", "다. ", " ", ""],
    "summary": ["\n", ". ", " ", ""],
}


def splitter_for(source_type: str) -> RecursiveCharacterTextSplitter:
    """출처 종류에 맞는 분할기. (F2005)"""
    conf = settings.get(f"chunking.{source_type}") or settings.get("chunking.web") or {}
    return RecursiveCharacterTextSplitter(
        chunk_size=int(conf.get("chunk_size", 1000)),
        chunk_overlap=int(conf.get("chunk_overlap", 200)),
        separators=_SEPARATORS.get(source_type, _SEPARATORS["web"]),
        keep_separator=True,
    )


def split_text(source_type: str, text: str) -> list[str]:
    """본문 1개 → 청크 목록. 공백뿐인 청크는 버린다."""
    return [c.strip() for c in splitter_for(source_type).split_text(text or "") if c.strip()]


def split_pages(pages: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """PDF 쪽 목록 [(쪽 번호, 텍스트)] → [(쪽 번호, 청크)]. (F2016)"""
    splitter = splitter_for("pdf")
    out = []
    for page_no, text in pages:
        for chunk in splitter.split_text(text or ""):
            if chunk.strip():
                out.append((page_no, chunk.strip()))
    return out
