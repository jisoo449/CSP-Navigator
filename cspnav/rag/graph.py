"""LangGraph 파이프라인: retrieve → generate 두 노드. (F2006, F2007, F2008)

retrieve
  1) 선택 상품의 메타 청크는 검색 없이 ID로 항상 넣는다.
  2) 선택 상품을 다룬 문서(항목ID가 같은 외부 문서 청크)도 질문 유사도 상위 own_doc_k개를 항상 넣는다.
  3) 외부 문서 전체에서 질문과 의미가 가까운 청크 top_k개를 찾는다. 부문 태그로 거른다(F2017).
  4) 합친 뒤 청크 ID로 중복을 없애고, 1)·2)를 앞에 두어 어떤 개수 제한보다 우선한다.
generate
  프롬프트3에 번호 붙은 근거를 넣어 답을 만들고, 실제로 인용된 번호만 골라 둔다.
"""

from __future__ import annotations

from datetime import date
from typing import Optional, TypedDict

from langchain_core.documents import Document
from langgraph.graph import END, START, StateGraph

from cspnav import settings
from cspnav.rag import prompts
from cspnav.rag.citations import drop_on_not_found, extract_cited, strip_invalid
from cspnav.rag.llm import invoke_text
from cspnav.schemas import Evidence
from cspnav.vectorstore.store import VectorStore, where_all


class AskState(TypedDict, total=False):
    """그래프 상태."""

    item_id: str
    question: str
    sector: str
    extra_context: str
    evidences: list[Evidence]
    answer: str
    cited: list[int]


def _date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return date.today()


def doc_to_evidence(number: int, doc: Document, chunk_id: str) -> Evidence:
    """Chroma 문서 → 근거. 화면용 snippet은 제목 줄을 뺀 앞부분. (F2008, F2019)"""
    meta = doc.metadata or {}
    body = doc.page_content
    if body.startswith("[") and "]\n" in body:
        body = body.split("]\n", 1)[1]
    limit = int(settings.get("retrieval.snippet_chars", 280))
    is_meta = meta.get("source_type") == "meta"
    return Evidence(
        number=number,
        source_type=meta.get("source_type", "web"),
        title=(f"{meta.get('csp', '')} {meta.get('name', '')}".strip() if is_meta else meta.get("title", "")),
        source=meta.get("source_url", "") if is_meta else meta.get("source", ""),
        checked_at=_date(meta.get("checked_at") if is_meta else meta.get("collected_at")),
        csp=meta.get("csp", ""),
        item_id=meta.get("item_id", ""),
        snippet=body[:limit] + ("…" if len(body) > limit else ""),
        chunk_id=chunk_id,
        content=doc.page_content,
    )


def sector_filter(sector: str) -> Optional[dict]:
    """외부 문서 부문 태그 필터. (F2017)"""
    return {f"sector_{sector}": True} if sector in ("public", "private", "learning") else None


def retrieve_evidences(store: VectorStore, question: str, sector: str, item_id: Optional[str] = None,
                       start_number: int = 1, top_k: Optional[int] = None,
                       pinned: Optional[list[Evidence]] = None) -> list[Evidence]:
    """근거 검색·병합·중복 제거. pinned는 검색 없이 앞에 고정할 근거(추천 화면의 설계안 상품 등). (F2006)"""
    top_k = int(top_k or settings.get("retrieval.top_k", 5))
    own_k = int(settings.get("retrieval.own_doc_k", 2))
    max_ev = int(settings.get("retrieval.max_evidences", 8))

    ordered: list[tuple[str, Document]] = []
    if item_id:
        meta_doc = store.get_meta(item_id)
        if meta_doc is not None:
            ordered.append((item_id, meta_doc))
        for doc, _ in store.search("docs", question, own_k, where=where_all(item_id=item_id), search_type="similarity"):
            ordered.append((doc.id or "", doc))
    for doc, _ in store.search("docs", question, top_k, where=sector_filter(sector)):
        ordered.append((doc.id or "", doc))

    evidences: list[Evidence] = list(pinned or [])
    seen = {e.chunk_id for e in evidences if e.chunk_id}
    number = start_number + len(evidences)
    for chunk_id, doc in ordered:
        if chunk_id and chunk_id in seen:
            continue
        seen.add(chunk_id)
        evidences.append(doc_to_evidence(number, doc, chunk_id))
        number += 1
    # 고정 근거(pinned)·선택 상품 메타·상품 문서는 앞쪽에 있으므로 뒤에서부터 자른다.
    protected = len(pinned or []) + (1 + own_k if item_id else 0)
    return evidences[:max(max_ev, protected)]


def generate_answer(question: str, sector: str, evidences: list[Evidence], extra_context: str = "") -> tuple[str, list[int]]:
    """프롬프트3으로 답을 만든다. 근거가 하나도 없으면 LLM을 부르지 않는다. (F2007, F2008)"""
    if not evidences:
        return f"{prompts.NOT_FOUND}. 색인된 근거에서 질문과 관련된 내용을 찾지 못했습니다.", []
    text = invoke_text(prompts.answer_messages(question, sector, evidences, extra_context))
    text = drop_on_not_found(strip_invalid(text, evidences))
    return text, extract_cited(text, evidences)


def build_graph(store: VectorStore):
    """retrieve / generate 두 노드짜리 그래프를 만든다. (F2007)"""

    def retrieve(state: AskState) -> AskState:
        return {"evidences": retrieve_evidences(store, state["question"], state["sector"], state.get("item_id"))}

    def generate(state: AskState) -> AskState:
        text, cited = generate_answer(state["question"], state["sector"], state.get("evidences", []),
                                      state.get("extra_context", ""))
        return {"answer": text, "cited": cited}

    graph = StateGraph(AskState)
    graph.add_node("retrieve", retrieve)
    graph.add_node("generate", generate)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)
    return graph.compile()
