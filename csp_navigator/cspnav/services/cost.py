"""예상 월 비용 계산. LLM을 쓰지 않고 코드로만 계산하며, 계산식을 함께 남긴다. (F2018)

규칙 (모두 settings.json cost.* 에서 조정)
- 시간 과금: 원화 단가 × 수량 × 월 사용 시간(기본 730시간)
- 공식 월 요금이 있는 상품(NCP 서버, KT 서버 등): 월 사용 시간이 기준 시간 이상이면 공식 월 요금을 쓴다
- 월 정액: 단가 × 수량 / GB-월: 단가 × 용량(GB)
- USD 단가는 설정 환율(기본 1,334.03원/USD, YCharts 2026-10-16)로 바꾼다
"""

from __future__ import annotations

from typing import Optional

from cspnav import settings
from cspnav.data_prep.products import fx_rate
from cspnav.schemas import CostLine, Product, ServerPrice, StoragePrice


def hours_per_month() -> int:
    return int(settings.get("cost.hours_per_month", 730))


def _fx_part(orig: float, currency: str, unit: str) -> str:
    """'0.104 USD × 1,334.03원/USD = ' 처럼 환산 과정을 적는다."""
    if currency != "USD":
        return ""
    return f"({orig:g} USD × {fx_rate('USD'):,.2f}원/USD) "


def _won(value: float) -> str:
    return f"{value:,.2f}".rstrip("0").rstrip(".") + "원"


def calc_product_line(product: Product, quantity: int, hours: Optional[int], sector_status: str,
                      label: str = "") -> Optional[CostLine]:
    """상품 메타 1건의 월 비용. 요금 구조가 복합적(billing_unit='other')이면 None. (F2018)"""
    price = product.unit_price
    if price is None or product.billing_unit == "other":
        return None
    hpm = hours_per_month()
    used_hours: Optional[int] = None
    fx = _fx_part(product.unit_price_orig or 0, product.currency, product.billing_unit)
    if product.billing_unit == "hour":
        used_hours = hours or hpm
        if product.official_monthly and used_hours >= hpm:
            subtotal = round(product.official_monthly * quantity)
            formula = f"공식 월 요금 {product.official_monthly:,.0f}원 × {quantity:,}{product.qty_unit} (월 {used_hours}시간 사용)"
        else:
            subtotal = round(price * quantity * used_hours)
            formula = f"{fx}{_won(price)}/시간 × {quantity:,}{product.qty_unit} × {used_hours:,}시간"
    elif product.billing_unit == "gb_month":
        subtotal = round(price * quantity)
        formula = f"{fx}{_won(price)}/GB·월 × {quantity:,}GB"
    else:  # month
        subtotal = round(price * quantity)
        formula = f"{fx}{_won(price)}/월 × {quantity:,}{product.qty_unit}"
    return CostLine(
        item_id=product.item_id, product_name=label or product.name, category=product.category, quantity=quantity,
        qty_unit=product.qty_unit, hours=used_hours, unit_price=price, billing_unit=product.billing_unit,
        subtotal=subtotal, formula=f"{formula} = {subtotal:,}원", source_url=product.source_url,
        checked_at=product.checked_at, sector_status=sector_status, source_type="meta",
        note=product.price_note,
    )


def server_monthly(server: ServerPrice, hours: int) -> tuple[float, str]:
    """서버 1대의 월 비용(원)과 계산식. (F2018)"""
    rate = fx_rate(server.currency)
    hpm = hours_per_month()
    if server.monthly_orig is not None and (server.hourly_orig is None or hours >= hpm):
        monthly = server.monthly_orig * rate
        basis = "공식 월 요금" + ("" if server.hourly_orig is None else f"(월 {hours}시간 사용)")
        return monthly, f"{basis} {_won(monthly)}"
    if server.hourly_orig is None:
        raise ValueError("시간 단가와 월 요금이 모두 없습니다.")
    unit = server.hourly_orig * rate
    fx = f"({server.hourly_orig:g} USD × {rate:,.2f}원/USD) " if server.currency == "USD" else ""
    return unit * hours, f"{fx}{_won(unit)}/시간 × {hours:,}시간"


def calc_server_line(server: ServerPrice, quantity: int, hours: int, sector_status: str) -> CostLine:
    """가격표 서버 1종 × 수량의 월 비용. (F2018)"""
    monthly, formula = server_monthly(server, hours)
    subtotal = round(monthly * quantity)
    return CostLine(
        item_id=server.price_id, product_name=f"{server.server_type} ({server.vcpu:g}vCPU/{server.memory_gb:g}GB, {server.platform})",
        category="CMP", quantity=quantity, qty_unit="대", hours=hours, unit_price=monthly, billing_unit="month",
        subtotal=subtotal, formula=f"{formula} × {quantity:,}대 = {subtotal:,}원", source_url=server.source_url,
        checked_at=server.checked_at, sector_status=sector_status, source_type="price",
        note=f"디스크: {server.included_disk}" + (f"; {server.note}" if server.note else ""),
    )


def calc_storage_line(storage: StoragePrice, gb: int, quantity: int, sector_status: str, label: str) -> CostLine:
    """Block Storage(서버 디스크) 월 비용 = GB-월 단가 × 용량 × 대수. (F2018)"""
    rate = fx_rate(storage.currency)
    unit = storage.per_gb_month_orig * rate
    subtotal = round(unit * gb * quantity)
    fx = f"({storage.per_gb_month_orig:g} USD × {rate:,.2f}원/USD) " if storage.currency == "USD" else ""
    return CostLine(
        item_id=storage.storage_id, product_name=f"{label}: {storage.storage_type}", category="STG", quantity=gb * quantity,
        qty_unit="GB", hours=None, unit_price=unit, billing_unit="gb_month", subtotal=subtotal,
        formula=f"{fx}{_won(unit)}/GB·월 × {gb:,}GB × {quantity:,}대 = {subtotal:,}원",
        source_url=storage.source_url, checked_at=storage.checked_at, sector_status=sector_status,
        source_type="price", note=storage.note,
    )


def monthly_estimate(product: Product) -> tuple[Optional[int], str]:
    """탐색 카드에 보여 줄 상품 1개의 예상 월 비용과 계산 기준. (F2011, F2018)"""
    hpm = hours_per_month()
    if product.unit_price is None or product.billing_unit == "other":
        return None, "복합 요금 — 원문 참고"
    if product.billing_unit == "hour":
        if product.official_monthly:
            return round(product.official_monthly), "공식 월 요금"
        return round(product.unit_price * hpm), f"{hpm}시간 기준(기본값)"
    if product.billing_unit == "gb_month":
        gb = int(settings.get("explore.est_storage_gb", 100))
        return round(product.unit_price * gb), f"{gb}GB 기준(기본값)"
    return round(product.unit_price), f"월 정액(1{product.qty_unit})"
