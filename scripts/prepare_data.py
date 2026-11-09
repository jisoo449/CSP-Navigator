"""데이터 준비 1단계: 1일차 수집 결과(md) → data/processed/*.json (F2001)

실행 (csp_navigator 폴더에서):
    python scripts/prepare_data.py

LLM·임베딩 키가 필요 없고 표준 라이브러리만 쓴다.
성공하면 "상품 108건" 과 CSP별·분류별 건수가 출력된다.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from cspnav import settings  # noqa: E402
from cspnav.data_prep import md_products  # noqa: E402
from cspnav.data_prep.prices import load_servers, load_storages  # noqa: E402
from cspnav.data_prep.products import load_products  # noqa: E402


def main() -> int:
    md_path = settings.resolve_path("products_md")
    out_dir = settings.resolve_path("processed_dir")
    if not md_path.exists():
        print(f"[실패] 수집 결과 파일이 없습니다: {md_path}")
        return 1
    summary = md_products.convert(md_path, out_dir)
    print(f"수집일: {summary['checked_at']}")
    print(f"상품 {summary['products']}건")
    print("  CSP별: " + ", ".join(f"{k} {v}" for k, v in summary["by_csp"].items()))
    print("  분류별: " + ", ".join(f"{k} {v}" for k, v in summary["by_category"].items()))
    print(f"  요금 자동 계산 제외(복합 요금): {len(summary['price_unparsed'])}건 {summary['price_unparsed']}")
    print(f"CSAP 인증 행 {summary['csap']}건 · 공공 요건 자료 {summary['public_docs']}건 · "
          f"공통 문서 {summary['common_docs']}건 · 웹 문서 후보 {summary['web_catalog']}건")

    load_products.cache_clear()
    products = load_products()
    servers, storages = load_servers(), load_storages()
    print(f"로드 확인: Product {len(products)}건, 서버 가격 {len(servers)}행, Block Storage {len(storages)}행")
    print(f"출력 폴더: {out_dir}")
    if summary["products"] < 100:
        print("[경고] 상품이 100건보다 적습니다(명세 2.1 조건).")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
