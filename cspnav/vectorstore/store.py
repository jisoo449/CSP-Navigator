"""Chroma 컬렉션 2개 관리. (F2002, F2005, F2006, NF2002)

- csp_product_meta  : 상품 메타데이터. 항목당 1청크, 청크 ID = 항목ID
- csp_external_docs : 외부 문서. 청크 ID = "항목ID:문서ID:순번" (공통 문서는 항목ID 'COMMON')

건수 조회(get_status)는 임베딩 없이 chromadb 클라이언트로 바로 한다. 키가 없어도 색인 건수를 보여 주기 위해서다.
"""

from __future__ import annotations

from typing import Any, Optional

import chromadb
import chromadb.errors
from langchain_chroma import Chroma
from langchain_core.documents import Document

from cspnav import settings

COMMON_ITEM = "COMMON"
_SPACE = {"hnsw:space": "cosine"}   # 거리 = 1 - 코사인 유사도 (작을수록 가깝다)


def where_all(**conds: Any) -> Optional[dict]:
    """키=값 조건 여러 개를 Chroma where 형식으로 만든다. 값이 None인 조건은 뺀다."""
    items = [{k: v} for k, v in conds.items() if v is not None]
    if not items:
        return None
    return items[0] if len(items) == 1 else {"$and": items}


class VectorStore:
    """두 컬렉션을 한 PersistentClient로 다룬다. 임베딩은 검색·추가할 때만 필요하다."""

    def __init__(self, embeddings=None, persist_dir: Optional[str] = None):
        path = persist_dir or str(settings.resolve_path("chroma_dir"))
        self.path = path
        self.client = chromadb.PersistentClient(path=path)
        self.embeddings = embeddings
        self.meta_name = settings.get("collections.meta", "csp_product_meta")
        self.docs_name = settings.get("collections.docs", "csp_external_docs")
        self._meta: Optional[Chroma] = None
        self._docs: Optional[Chroma] = None

    # ── 컬렉션 ──────────────────────────────────────────
    def _vs(self, name: str) -> Chroma:
        if self.embeddings is None:
            raise RuntimeError("임베딩이 설정되지 않아 검색·색인을 할 수 없습니다.")
        return Chroma(client=self.client, collection_name=name, embedding_function=self.embeddings,
                      collection_metadata=_SPACE)

    @property
    def meta(self) -> Chroma:
        if self._meta is None:
            self._meta = self._vs(self.meta_name)
        return self._meta

    @property
    def docs(self) -> Chroma:
        if self._docs is None:
            self._docs = self._vs(self.docs_name)
        return self._docs

    def reopen(self) -> None:
        """다른 프로세스(예: Streamlit과 FastAPI를 동시에 띄운 경우)가 같은 색인 폴더에 청크를 추가하면
        이 프로세스의 메모리 색인이 낡아 Chroma가 'Error finding id'를 낸다(2026-10-23 실제 검증에서 확인).
        클라이언트 캐시를 비우고 다시 열어 디스크의 최신 상태를 읽는다. (F2006)"""
        from chromadb.api.client import SharedSystemClient

        SharedSystemClient.clear_system_cache()
        self.client = chromadb.PersistentClient(path=self.path)
        self._meta = self._docs = None

    def count(self, name: str) -> int:
        """컬렉션 건수. 컬렉션이 없으면 0. (F2002)"""
        try:
            return self.client.get_collection(name).count()
        except Exception:  # noqa: BLE001 — 없는 컬렉션
            return 0

    def counts(self) -> tuple[int, int]:
        """(상품 메타 청크 수, 외부 문서 청크 수). (F2002, F2012)"""
        return self.count(self.meta_name), self.count(self.docs_name)

    def reset(self, which: str = "all") -> None:
        """컬렉션을 지운다(재색인용). which = meta | docs | all"""
        names = {"meta": [self.meta_name], "docs": [self.docs_name]}.get(which, [self.meta_name, self.docs_name])
        for name in names:
            try:
                self.client.delete_collection(name)
            except Exception:  # noqa: BLE001
                pass
        self._meta = self._docs = None

    # ── 추가 (upsert: 같은 ID면 덮어쓰므로 재실행해도 중복이 생기지 않는다) ──
    def _retry(self, fn):
        """색인이 다른 프로세스 때문에 바뀌었으면 한 번 다시 열고 재시도한다. (F2002, F2005, F2006)
        - InternalError "Error finding id": 다른 프로세스가 청크를 추가해 메모리 색인이 낡음
        - NotFoundError "Collection … does not exist": 다른 프로세스가 build_index.py --reset으로 컬렉션을
          지우고 새로 만들어 컬렉션 ID가 바뀜 (둘 다 2026-10-23 실제 실행에서 확인)"""
        try:
            return fn()
        except (chromadb.errors.InternalError, chromadb.errors.NotFoundError):
            self.reopen()
            return fn()

    def upsert_meta(self, docs: list[Document], ids: list[str]) -> None:
        """상품 메타 청크 추가. ID = 항목ID. (F2002)"""
        if docs:
            self._retry(lambda: self.meta.add_documents(docs, ids=ids))

    def upsert_doc_chunks(self, docs: list[Document], ids: list[str]) -> None:
        """외부 문서 청크 추가. ID = 항목ID:문서ID:순번. (F2005)"""
        if docs:
            self._retry(lambda: self.docs.add_documents(docs, ids=ids))

    # ── 조회 ────────────────────────────────────────────
    def get_meta(self, item_id: str) -> Optional[Document]:
        """선택 상품의 메타 청크를 검색 없이 ID로 가져온다. (F2006)"""
        try:
            got = self.client.get_collection(self.meta_name).get(ids=[item_id], include=["documents", "metadatas"])
        except Exception:  # noqa: BLE001
            return None
        if not got["ids"]:
            return None
        return Document(id=got["ids"][0], page_content=got["documents"][0], metadata=got["metadatas"][0] or {})

    def has_doc(self, item_id: str, doc_id: str) -> bool:
        """이 항목으로 이 문서를 이미 색인했는가. (NF2002)"""
        try:
            got = self.client.get_collection(self.docs_name).get(
                where=where_all(item_id=item_id, doc_id=doc_id), limit=1, include=[])
        except Exception:  # noqa: BLE001
            return False
        return bool(got["ids"])

    def search(self, which: str, query: str, k: int, where: Optional[dict] = None,
               search_type: Optional[str] = None) -> list[tuple[Document, Optional[float]]]:
        """유사도(similarity) 또는 MMR 검색. 색인이 다른 프로세스 때문에 낡았으면 한 번 다시 열고 재시도한다. (F2006)"""
        return self._retry(lambda: self._search(which, query, k, where, search_type))

    def _search(self, which: str, query: str, k: int, where: Optional[dict] = None,
                search_type: Optional[str] = None) -> list[tuple[Document, Optional[float]]]:
        """유사도(similarity) 또는 MMR 검색. MMR은 거리값이 없어 None을 돌려준다. (F2006, F2014 설정만)"""
        if k <= 0:
            return []
        name = self.meta_name if which == "meta" else self.docs_name
        if self.count(name) == 0:
            return []
        vs = self.meta if which == "meta" else self.docs
        search_type = search_type or settings.get("retrieval.search_type", "similarity")
        if search_type == "mmr":
            docs = vs.max_marginal_relevance_search(
                query, k=k, fetch_k=max(k, int(settings.get("retrieval.mmr_fetch_k", 20))),
                lambda_mult=float(settings.get("retrieval.mmr_lambda", 0.5)), filter=where)
            return [(d, None) for d in docs]
        return vs.similarity_search_with_score(query, k=k, filter=where)
