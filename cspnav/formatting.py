"""화면(Streamlit·HTML)과 서비스가 함께 쓰는 표시용 변환."""

from __future__ import annotations

from datetime import date
from typing import Optional

from cspnav import settings

BILLING_LABELS = {"hour": "시간당", "month": "월 정액", "gb_month": "GB·월당", "other": "복합 요금"}


def krw(value: Optional[float]) -> str:
    """금액을 '12,345원' 형식으로. None이면 '계산 불가'. (F2018)"""
    if value is None:
        return "계산 불가"
    if abs(value) < 10 and value != int(value):
        return f"{value:,.2f}원"
    return f"{round(value):,}원"


def support_text(value: object) -> str:
    """지원 여부 값(True/False/문자열)을 화면 문구로. (F2017)"""
    if value is True:
        return "지원"
    if value is False:
        return "미지원"
    return str(value)


def billing_label(unit: str) -> str:
    """과금 단위 코드를 화면 문구로. (F2001)"""
    return BILLING_LABELS.get(unit, unit)


def is_stale(checked_at: date, today: Optional[date] = None) -> bool:
    """확인일이 기준일(freshness_days, 기본값 90일)보다 오래됐는가. (F2019)"""
    days = int(settings.get("freshness_days", 90))
    return ((today or date.today()) - checked_at).days > days


def freshness_text(checked_at: date) -> str:
    """'최신' / '재확인 권장'. (F2019)"""
    return "재확인 권장" if is_stale(checked_at) else "최신"
