"""오프라인 점검: 키·네트워크 없이 전 흐름이 끊기지 않는지 확인한다. (검증용)

    python scripts/smoke_test.py

- 가짜 LLM·임베딩(CSPNAV_FAKE=1)과 오프라인 모드(CSPNAV_OFFLINE=1)로 돈다. 답변 문장은 (더미)다.
- 실제 수집 결과(../data/sources)가 있으면 그것을, 없으면 tests/fixtures 발췌본을 쓴다.
- 색인·캐시는 임시 폴더에 만들어 실제 data/chroma를 건드리지 않는다.
- 마지막 줄이 "결과: n개 통과 / 0개 실패" 이면 성공.

이 점검은 '흐름이 이어지는가'만 본다. 실제 답변 품질·GMS 연결은 README 5장 절차로 따로 확인한다.
"""

from __future__ import annotations

import os
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TMP = Path(tempfile.mkdtemp(prefix="cspnav_smoke_"))
FIX = ROOT / "tests" / "fixtures"
os.environ.update({
    "CSPNAV_FAKE": "1",
    "CSPNAV_OFFLINE": "1",
    "CSPNAV_PROCESSED_DIR": str(TMP / "processed"),
    "CSPNAV_CHROMA_DIR": str(TMP / "chroma"),
    "CSPNAV_CACHE_DIR": str(TMP / "cache"),
    "CSPNAV_PDF_DIR": str(TMP / "pdf"),
})

from cspnav import settings  # noqa: E402

if not settings.resolve_path("products_md").exists():
    os.environ["CSPNAV_PRODUCTS_MD"] = str(FIX / "sample_sources.md")
    os.environ["CSPNAV_SERVER_CSV"] = str(FIX / "sample_servers.csv")
    os.environ["CSPNAV_STORAGE_CSV"] = str(FIX / "sample_storage.csv")
    DATA_LABEL = "tests/fixtures 발췌본"
else:
    DATA_LABEL = "실제 수집 결과(../data/sources)"

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(cond), detail))
    print(f"[{'통과' if cond else '실패'}] {name}" + (f" — {detail}" if detail else ""))


def main() -> int:
    print(f"데이터: {DATA_LABEL}\n임시 폴더: {TMP}\n")
    from cspnav.data_prep import md_products
    from cspnav.data_prep.products import load_products

    summary = md_products.convert(settings.resolve_path("products_md"), settings.resolve_path("processed_dir"))
    load_products.cache_clear()
    products = load_products()
    check("F2001 상품 메타 로드", len(products) == summary["products"] > 0, f"{len(products)}건")

    sys.path.insert(0, str(ROOT / "scripts"))
    from build_index import build
    meta, docs = build(verbose=False)
    check("F2002 메타 색인 건수 = 상품 수", meta == len(products), f"{meta}건")
    meta2, _ = build(verbose=False)
    check("F2002 재실행해도 중복 없음", meta2 == meta, f"{meta2}건")
    check("F2016 공통 문서(수집 요약) 색인", docs > 0, f"{docs}청크")

    # PDF 출처 점검용: 임시 PDF 1개를 만들어 catalog에 등록
    pdf_ok = _make_test_pdf()

    from cspnav.services import get_service
    svc = get_service()
    status = svc.get_status()
    check("F2012 상태 조회", status.meta_count == meta and status.api_key_ready, f"meta={status.meta_count}")

    target = next((p for p in products if p.category == "CMP"), products[0])
    progress: list[str] = []
    ans = svc.ask(target.item_id, "이 상품을 월 730시간 쓰면 비용이 얼마인가요?", "public", on_progress=progress.append)
    check("F2006 선택 상품 메타 청크 항상 포함", ans.evidences and ans.evidences[0].chunk_id == target.item_id,
          ans.evidences[0].chunk_id if ans.evidences else "근거 없음")
    check("F2007 답변 생성", bool(ans.text))
    check("F2008 인용 근거만 표시용 목록에", set(ans.cited) <= {e.number for e in ans.evidences} and len(ans.cited) > 0,
          f"cited={ans.cited}")
    check("F2012 진행 상태 문구", len(progress) >= 2, f"{len(progress)}개")
    ids = [e.chunk_id for e in ans.evidences]
    check("F2006 청크 ID 중복 제거", len(ids) == len(set(ids)))
    doc_ids = [e.chunk_id for e in ans.evidences if e.source_type != "meta"]
    check("F2005 외부 문서 청크 ID 형식(항목ID:문서ID:순번)",
          all(len(c.split(":")) == 3 for c in doc_ids) and len(doc_ids) > 0, ", ".join(doc_ids[:2]))
    if pdf_ok:
        check("F2016 PDF 출처 근거(파일명·쪽)", any(e.source_type == "pdf" and "쪽" in e.source for e in ans.evidences),
              next((e.source for e in ans.evidences if e.source_type == "pdf"), "PDF 근거 없음"))

    ans2 = svc.ask(target.item_id, "이 상품을 월 730시간 쓰면 비용이 얼마인가요?", "public")
    check("NF2002 같은 검색어 재질문 시 캐시 사용", any("캐시" in n for n in ans2.notices), "; ".join(ans2.notices))

    from cspnav.schemas import Requirement
    req = Requirement("웹 서비스", 2, 2, 8, True, 100, 730, 1_000_000, [], "")
    rec = svc.recommend(req, "learning")
    check("F2010 추천 CSP 산출", rec.recommended_csp is not None, str(rec.recommended_csp))
    best = next((c for c in rec.candidates if c.csp == rec.recommended_csp), None)
    check("F2018 비용 = 줄 합계(코드 계산)", best is not None and best.monthly_total == sum(l.subtotal for l in best.lines),
          f"{best.monthly_total if best else '-'}원")
    check("F2018 계산식 표시", best is not None and all("=" in l.formula for l in best.lines))
    req_p = Requirement("사내 업무 시스템(ERP 등)", 1, 2, 8, False, 0, 730, 1_000_000, ["폐쇄망(사설 연결)"], "")
    rec_p = svc.recommend(req_p, "private")
    best_p = next((c for c in rec_p.candidates if c.csp == rec_p.recommended_csp), None)
    check("F2017 private: 사설 연결 상품 포함",
          best_p is not None and any(l.product_name.startswith("사설 연결") for l in best_p.lines),
          ", ".join(l.product_name for l in best_p.lines) if best_p else "-")
    req_g = Requirement("민원·대국민 서비스", 1, 2, 8, False, 0, 730, 1_000_000, [], "", data_grade="중")
    rec_g = svc.recommend(req_g, "public")
    aws = next((c for c in rec_g.candidates if c.csp == "AWS"), None)
    check("F2017 공공 중등급: 하등급만 보유한 CSP 제외", aws is not None and not aws.eligible,
          "; ".join(aws.excluded_reasons) if aws else "-")

    ex = svc.explore("서울 리전 MySQL 월 20만 원 이하", "learning")
    check("F2011 조건 탐색 결과", isinstance(ex.hits, list), f"{len(ex.hits)}건, 조건 {ex.conditions}")
    check("F2011 금액 조건 코드 비교", all(h.monthly_estimate is not None and h.monthly_estimate <= 200000 for h in ex.hits))

    _api_checks()

    ok = sum(1 for _, c, _ in RESULTS if c)
    bad = len(RESULTS) - ok
    print(f"\n결과: {ok}개 통과 / {bad}개 실패")
    return 0 if bad == 0 else 1


def _make_test_pdf() -> bool:
    """(점검용) 1쪽짜리 PDF를 만들어 catalog.json에 등록한다. pypdf가 없으면 건너뛴다."""
    try:
        from pypdf import PdfWriter
        from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
    except ImportError:
        print("[건너뜀] pypdf가 없어 PDF 출처 점검을 건너뜁니다.")
        return False
    import json
    pdf_dir = settings.resolve_path("pdf_dir")
    pdf_dir.mkdir(parents=True, exist_ok=True)
    writer = PdfWriter()
    page = writer.add_blank_page(width=595, height=842)
    font = DictionaryObject({NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"),
                             NameObject("/BaseFont"): NameObject("/Helvetica")})
    page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})})
    stream = DecodedStreamObject()
    lines = " T* ".join(f"(Line {i}: cloud computing service pricing guide for smoke test only.) Tj" for i in range(12))
    stream.set_data(f"BT /F1 9 Tf 40 800 Td 12 TL {lines} ET".encode("latin-1"))
    page[NameObject("/Contents")] = writer._add_object(stream)
    with open(pdf_dir / "smoke_test.pdf", "wb") as f:
        writer.write(f)
    catalog = {"items": [{"file": "smoke_test.pdf", "title": "(점검용) 클라우드 컴퓨팅 요금 안내 PDF", "summary": "",
                          "source_url": "", "license": "(점검용)", "sectors": ["public", "private", "learning"],
                          "use": True}]}
    (pdf_dir / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
    return True


def _api_checks() -> None:
    """FastAPI 엔드포인트 점검 (F2013)."""
    try:
        from fastapi.testclient import TestClient
        sys.path.insert(0, str(ROOT))
        from api.main import app
    except Exception as exc:  # noqa: BLE001
        check("F2013 FastAPI 앱 로드", False, f"{type(exc).__name__}: {exc}")
        return
    client = TestClient(app)
    r = client.get("/api/status")
    check("F2013 GET /api/status", r.status_code == 200 and r.json()["meta_count"] > 0, str(r.status_code))
    r = client.get("/api/products", params={"csp": "AWS"})
    items = r.json().get("items", []) if r.status_code == 200 else []
    check("F2013 GET /api/products", r.status_code == 200 and len(items) > 0, f"{len(items)}건")
    item_id = items[0]["item_id"] if items else "AWS-CMP-03"
    r = client.post("/api/ask", json={"item_id": item_id, "question": "요금이 얼마인가요?", "sector": "learning"})
    check("F2013 POST /api/ask", r.status_code == 200 and "text" in r.json(), str(r.status_code))
    r = client.post("/api/recommend", json={"requirement": {"workload": "웹 서비스", "instances": 1, "vcpu": 2,
                                                            "memory_gb": 8, "need_db": False, "storage_gb": 0,
                                                            "hours": 730, "budget": 500000, "security": []},
                                            "sector": "learning"})
    check("F2013 POST /api/recommend", r.status_code == 200 and "candidates" in r.json(), str(r.status_code))
    r = client.post("/api/explore", json={"query": "MySQL", "sector": "learning"})
    check("F2013 POST /api/explore", r.status_code == 200 and "hits" in r.json(), str(r.status_code))
    r = client.post("/api/ask", json={"item_id": "NOPE", "question": "x", "sector": "public"})
    check("NF2004 오류는 사용자용 문구만", r.status_code == 400 and "Traceback" not in r.text, r.json().get("detail", ""))
    r = client.get("/")
    check("F2013 HTML 화면 제공", r.status_code == 200 and "<html" in r.text.lower(), str(r.status_code))


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001 — 점검 스크립트는 원인 파악용으로 추적 정보를 콘솔에 출력한다
        traceback.print_exc()
        raise SystemExit(1)
