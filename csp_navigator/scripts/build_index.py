"""데이터 준비 2단계: 상품 메타 색인(RAG 1) + 공통 문서 색인. (F2002, F2005, F2016)

실행 (csp_navigator 폴더에서, prepare_data.py 다음에):
    python scripts/build_index.py            # 추가·갱신 (같은 ID는 덮어써서 중복이 생기지 않음)
    python scripts/build_index.py --reset    # 두 컬렉션을 지우고 처음부터

필요한 .env: GMS_KEY, GMS_BASE_URL, EMBEDDING_MODEL (LLM_MODEL은 이 단계에서 쓰지 않지만 앱 실행에 필요)
성공하면 "csp_product_meta: 108건" 이 출력된다. 같은 명령을 다시 실행해도 건수는 그대로여야 한다.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from cspnav import settings  # noqa: E402
from cspnav.data_prep.products import load_json, load_products  # noqa: E402
from cspnav.errors import ServiceError  # noqa: E402


def build(reset: bool = False, verbose: bool = True) -> tuple[int, int]:
    """색인을 만들고 (메타 건수, 문서 청크 수)를 돌려준다. (F2002)"""
    from cspnav.rag.llm import get_embeddings
    from cspnav.vectorstore.indexer import index_common_docs, index_products
    from cspnav.vectorstore.store import VectorStore

    products = load_products()
    if not products:
        raise SystemExit("[실패] data/processed/products.json이 없습니다. 먼저 python scripts/prepare_data.py 를 실행하세요.")
    store = VectorStore(embeddings=get_embeddings())
    if reset:
        store.reset("all")
        store.embeddings = get_embeddings()
    n_meta = index_products(store, products)
    n_common = index_common_docs(store, load_json("common_docs.json"))
    meta, docs = store.counts()
    if verbose:
        print(f"상품 메타 색인 {n_meta}건 · 공통 문서 청크 {n_common}개 색인(upsert)")
        print(f"csp_product_meta: {meta}건")
        print(f"csp_external_docs: {docs}청크")
        print(f"저장 위치: {settings.resolve_path('chroma_dir')}")
    return meta, docs


def main() -> int:
    parser = argparse.ArgumentParser(description="CSP Navigator 색인")
    parser.add_argument("--reset", action="store_true", help="두 컬렉션을 지우고 다시 만든다")
    args = parser.parse_args()
    env = settings.load_env()
    if env.missing():
        print("[실패] .env에 비어 있는 항목이 있습니다: " + ", ".join(env.missing()))
        return 1
    try:
        build(reset=args.reset)
    except ServiceError as err:
        print(f"[실패] {err.user_message}")
        return 1
    except Exception as exc:  # noqa: BLE001 — 개발자용 콘솔이라 오류 종류와 메시지만 보여 준다(키는 메시지에 없다)
        print(f"[실패] 색인 중 오류: {type(exc).__name__}: {exc}")
        print("  확인: .env의 GMS_BASE_URL·EMBEDDING_MODEL 값, 네트워크, GMS 키 유효기간")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
