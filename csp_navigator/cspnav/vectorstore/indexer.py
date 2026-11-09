"""색인: 상품 메타(RAG 1)와 외부 문서(RAG 2). (F2002, F2005, F2016)"""

from __future__ import annotations

from datetime import date
from typing import Iterable

from langchain_core.documents import Document

from cspnav.data_prep.products import index_text, meta_metadata
from cspnav.data_prep.sources import CollectedDoc
from cspnav.schemas import Product
from cspnav.vectorstore.chunking import split_pages, split_text
from cspnav.vectorstore.store import COMMON_ITEM, VectorStore

SECTOR_CODES = ("public", "private", "learning")


def index_products(store: VectorStore, products: Iterable[Product]) -> int:
    """상품 메타데이터를 항목당 1청크로 색인한다. 청크 ID = 항목ID라 재실행해도 중복이 없다. (F2002)"""
    products = list(products)
    docs = [Document(page_content=index_text(p), metadata=meta_metadata(p)) for p in products]
    ids = [p.item_id for p in products]
    batch = 50
    for i in range(0, len(docs), batch):
        store.upsert_meta(docs[i:i + batch], ids[i:i + batch])
    return len(docs)


def _sector_meta(sectors: list[str]) -> dict:
    """부문 태그. Chroma 메타데이터에 목록을 넣지 않고 불리언 3개 + 문자열로 둔다. (F2005, F2017)"""
    sectors = [s for s in sectors if s in SECTOR_CODES] or list(SECTOR_CODES)
    meta = {f"sector_{s}": (s in sectors) for s in SECTOR_CODES}
    meta["sectors"] = ",".join(sectors)
    return meta


def index_document(store: VectorStore, item_id: str, doc: CollectedDoc, keyword: str = "") -> int:
    """수집 문서 1개를 청킹해 색인한다. 청크 ID = 항목ID:문서ID:순번. (F2005, F2016)

    메타데이터: 문서 제목·원문 출처(URL 또는 파일명·쪽)·문서ID·항목ID·CSP·부문 태그·출처 종류·검색어·수집일·이용 조건
    """
    if doc.pages:
        pieces = [(page, chunk) for page, chunk in split_pages(doc.pages)]
    else:
        pieces = [(-1, chunk) for chunk in split_text(doc.source_type, doc.body)]
    docs, ids = [], []
    for n, (page, chunk) in enumerate(pieces):
        source = f"{doc.source} · {page}쪽" if page > 0 else doc.source
        meta = {
            "title": doc.title,
            "source": source,
            "doc_id": doc.doc_id,
            "item_id": item_id,
            "csp": doc.csp or "",
            "source_type": doc.source_type,
            "keyword": keyword,
            "collected_at": doc.collected_at,
            "license": doc.license or "",
            "page": page,
            "chunk_no": n,
            **_sector_meta(doc.sectors),
        }
        docs.append(Document(page_content=f"[{doc.title}]\n{chunk}", metadata=meta))
        ids.append(f"{item_id}:{doc.doc_id}:{n}")
    batch = 64
    for i in range(0, len(docs), batch):
        store.upsert_doc_chunks(docs[i:i + batch], ids[i:i + batch])
    return len(docs)


def index_common_docs(store: VectorStore, common_docs: list[dict]) -> int:
    """수집 결과 요약(CSAP 현황, 제도 변경, 무료 티어 등)을 항목ID 'COMMON'으로 색인한다. (F2016, F2017)"""
    total = 0
    for d in common_docs:
        doc = CollectedDoc(
            doc_id=d["doc_id"], source_type=d.get("source_type", "summary"), title=d["title"], source=d["source"],
            body=d["body"], csp=d.get("csp", ""), sectors=d.get("sectors", []), license=d.get("license", ""),
            collected_at=d.get("collected_at") or date.today().isoformat(),
        )
        total += index_document(store, COMMON_ITEM, doc, keyword="(공통 문서)")
    return total
