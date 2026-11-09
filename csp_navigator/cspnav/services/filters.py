"""부문 필터. (F2017)

- 상품 단위: 조건을 만족하지 않는 상품(False)은 추천 근거에서 빼고, '확인 필요'인 상품은 빼지 않고 unknown으로 표시한다.
- CSP 단위(공공): KISA CSAP IaaS 인증 현황(csap.json)으로 판단한다.
  · 유효기간 안의 인증이 없으면 제외
  · 데이터 등급 상·중 시스템인데 하등급 인증만 있으면 제외
  · 그 밖에는 '확인 필요'(공공기관용 별도 플랫폼 기준 인증, 등급 미표기 등)
  2026-04-20 발표된 제도 변경(국정원 단일 검증, 2027년 하반기 시행)은 안내 문구로 덧붙인다.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from cspnav.schemas import Product


def needs_from(sector: str, security: list[str]) -> tuple[bool, bool]:
    """부문과 보안 조건에서 (공공 요건 필요, 폐쇄망 필요)를 정한다. (F2017)"""
    need_public = sector == "public" or "공공 요건" in security
    need_closed = sector == "private" or "폐쇄망(사설 연결)" in security
    return need_public, need_closed


def check_product(product: Product, need_public: bool, need_closed: bool) -> str:
    """'ok' / 'unknown'(확인 필요, 제외하지 않음) / 'fail'(제외). (F2017)"""
    values = []
    if need_public:
        values.append(product.public_support)
    if need_closed:
        values.append(product.closed_network_support)
    if any(v is False for v in values):
        return "fail"
    if any(v is not True for v in values):
        return "unknown"
    return "ok"


def meta_where(sector: str, security: Optional[list[str]] = None) -> Optional[dict]:
    """메타 색인 검색 단계에 거는 Chroma where 필터. 미지원(fail)만 거르고 확인 필요는 남긴다. (F2017)"""
    need_public, need_closed = needs_from(sector, security or [])
    conds = []
    if need_public:
        conds.append({"public_status": {"$ne": "fail"}})
    if need_closed:
        conds.append({"closed_status": {"$ne": "fail"}})
    if not conds:
        return None
    return conds[0] if len(conds) == 1 else {"$and": conds}


def _short(text: str, limit: int = 40) -> str:
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


def check_csp_public(csp: str, data_grade: str, csap_rows: list[dict], today: Optional[date] = None) -> tuple[str, str]:
    """공공 부문 CSP 단위 판단 → (ok/unknown/fail, 사유). (F2017)"""
    today = today or date.today()
    rows = [r for r in csap_rows if r["csp"] == csp]
    valid = []
    for r in rows:
        try:
            if r["valid_to"] and date.fromisoformat(r["valid_to"]) >= today:
                valid.append(r)
        except ValueError:
            continue
    if not valid:
        return "fail", "유효기간 안의 CSAP IaaS 인증이 수집 자료에서 확인되지 않음"
    low_only = all(r.get("low_grade_only") for r in valid)
    certs = ", ".join(f"{r['cert_no']} · {_short(r['scope'])}" for r in valid)
    if data_grade in ("상", "중") and low_only:
        return "fail", f"CSAP 하등급 인증만 보유 — {data_grade}등급 시스템에는 쓸 수 없음 ({certs})"
    if low_only:
        return "unknown", f"CSAP 하등급 인증 보유 — 시스템 등급이 하등급인지 확인 필요 ({certs})"
    return "unknown", f"공공기관용 별도 플랫폼 기준 CSAP 인증 보유 — 해당 플랫폼 상품·요금 확인 필요 ({certs})"
