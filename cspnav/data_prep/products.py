"""상품 메타데이터 로드와 색인 텍스트 구성. (F2001, F2018, F2019)

products.json(원래 통화·요금 원문)을 읽어, 설정값(환율·월 시간)으로 원화 단가를 계산한 Product로 만든다.
환율이나 시간 기준을 바꿔도 변환을 다시 돌릴 필요가 없게 환산은 여기서 한다.
표준 라이브러리만 쓴다.
"""

from __future__ import annotations

import json
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Optional

from cspnav import settings
from cspnav.data_prep import domain
from cspnav.schemas import Product


def fx_rate(currency: str) -> float:
    """원화 환산 비율. USD만 환율을 곱한다. (F2018)"""
    return float(settings.get("cost.usd_krw")) if currency == "USD" else 1.0


def storage_hours(csp: str) -> float:
    """GB-시간 단가를 GB-월로 바꿀 때 쓰는 시간. NCP·NHN은 720시간(30일) 기준. (F2018)"""
    table = settings.get("cost.storage_hours_per_month", {}) or {}
    return float(table.get(csp, table.get("default", settings.get("cost.hours_per_month", 730))))


def normalize_price(rec: dict) -> tuple[Optional[float], Optional[float], str, str, str]:
    """요금 구조 → (원래 통화 단가, 원화 단가, 과금 단위, 수량 단위, 환산 메모). (F2018)

    과금 단위는 hour / month / gb_month / other 중 하나다. other는 자동 계산하지 않는다.
    """
    price = rec["price"]
    csp = rec["csp"]
    qty = price.get("qty_unit") or domain.default_qty_unit(rec["category"], rec["role"])
    amount = price.get("amount")
    if price.get("status") != "ok" or amount is None:
        return None, None, "other", qty, "요금 구조가 복합적이라 자동 계산에서 제외(원문 참고)"
    rate = fx_rate(price["currency"])
    size = float(price.get("size") or 1)
    per = price["per"]
    notes = []
    if per == "hour":
        orig, unit = amount, "hour"
    elif per == "month":
        orig, unit = amount, "month"
    elif per == "day":
        days = float(settings.get("cost.days_per_month", 30))
        orig, unit = amount * days, "month"
        notes.append(f"일 단가 × {days:g}일로 월 환산(기본값)")
    elif per == "gb_month":
        orig, unit, qty = amount / size, "gb_month", "GB"
        if size != 1:
            notes.append(f"{size:g}GB 단가를 1GB로 환산")
    elif per == "gb_hour":
        hours = storage_hours(csp)
        orig, unit, qty = amount / size * hours, "gb_month", "GB"
        notes.append(f"GB-시간 단가 × {hours:g}시간으로 GB-월 환산")
    else:
        return None, None, "other", qty, "요금 구조가 복합적이라 자동 계산에서 제외(원문 참고)"
    if price["currency"] == "USD":
        notes.append(f"환율 {rate:,.2f}원/USD({settings.get('cost.usd_krw_source')})")
    if price.get("extra"):
        notes.append(f"추가 과금·조건: {price['extra']}")
    return orig, orig * rate, unit, qty, "; ".join(notes)


def _to_product(rec: dict) -> Product:
    orig, krw, unit, qty, price_note = normalize_price(rec)
    public, public_note = domain.map_public(rec["public_raw"])
    closed, closed_note = domain.map_closed(rec["closed_raw"])
    free, free_note = domain.map_free(rec["free_raw"])
    desc_parts = [f"{rec['name']} — {rec['spec']}"]
    if rec.get("note"):
        desc_parts.append(rec["note"])
    if rec.get("monthly_ref") and rec["monthly_ref"] != "-":
        desc_parts.append(f"월 환산(730시간, 참고) {rec['monthly_ref']}")
    return Product(
        item_id=rec["item_id"],
        csp=rec["csp"],
        name=rec["name"],
        category=rec["category"],
        role=rec["role"],
        spec=rec["spec"],
        vcpu=rec.get("vcpu"),
        memory_gb=rec.get("memory_gb"),
        price_text=rec["price_text"],
        currency=rec["price"].get("currency") or "",
        unit_price_orig=orig,
        unit_price=krw,
        billing_unit=unit,
        qty_unit=qty,
        official_monthly=rec.get("official_monthly"),
        price_note=price_note,
        region=rec["region"],
        public_support=public,
        public_note=public_note,
        closed_network_support=closed,
        closed_note=closed_note,
        free_tier=free,
        free_note=free_note,
        description=". ".join(desc_parts),
        source_url=rec["source_url"],
        checked_at=date.fromisoformat(rec["checked_at"]),
    )


def products_path() -> Path:
    return settings.resolve_path("processed_dir") / "products.json"


@lru_cache(maxsize=1)
def load_products() -> tuple[Product, ...]:
    """products.json → Product 목록. 파일이 없으면 빈 목록. (F2001)"""
    path = products_path()
    if not path.exists():
        return tuple()
    payload = json.loads(path.read_text(encoding="utf-8"))
    return tuple(_to_product(r) for r in payload["items"])


def load_json(name: str) -> list[dict]:
    """processed 폴더의 보조 JSON(items)을 읽는다. 없으면 빈 목록."""
    path = settings.resolve_path("processed_dir") / name
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8")).get("items", [])


def _support_label(value: object) -> str:
    if value is True:
        return "지원"
    if value is False:
        return "미지원"
    return str(value)


def index_text(p: Product) -> str:
    """상품 1건 → 색인 텍스트 1개. CSP·상품명·분류·사양·요금·리전·부문 지원 여부·설명을 잇는다. (F2001)"""
    if p.unit_price is not None:
        krw = f"원화 환산 {p.unit_price:,.2f}원/{_unit_label(p.billing_unit, p.qty_unit)}"
    else:
        krw = "원화 환산: 자동 계산 불가(요금 원문 참고)"
    lines = [
        f"CSP: {p.csp}",
        f"상품명: {p.name}",
        f"분류: {domain.CATEGORIES.get(p.category, p.category)} ({p.category})",
        f"사양: {p.spec}",
        f"요금(공식 표기, VAT 별도): {p.price_text}",
        f"요금 환산: {krw}" + (f" · {p.price_note}" if p.price_note else ""),
    ]
    if p.official_monthly:
        lines.append(f"공식 월 요금: {p.official_monthly:,.0f}원")
    lines += [
        f"리전: {p.region}",
        f"공공 요건: {_support_label(p.public_support)} ({p.public_note})",
        f"폐쇄망·사설 연결: {_support_label(p.closed_network_support)} ({p.closed_note})",
        f"무료 티어: {_support_label(p.free_tier)} ({p.free_note})",
        f"설명: {p.description}",
        f"출처: {p.source_url}",
        f"확인일: {p.checked_at.isoformat()}",
    ]
    return "\n".join(lines)


def _unit_label(billing_unit: str, qty_unit: str) -> str:
    base = {"hour": "시간", "month": "월", "gb_month": "GB·월"}.get(billing_unit, billing_unit)
    if billing_unit == "gb_month" or not qty_unit or qty_unit in ("대", "개"):
        return base
    return f"{qty_unit}·{base}"


def meta_metadata(p: Product) -> dict:
    """Chroma 메타데이터(문자열·숫자·불리언만). 부문 필터에 쓰는 상태값을 함께 둔다. (F2002, F2017)"""
    return {
        "item_id": p.item_id,
        "csp": p.csp,
        "category": p.category,
        "role": p.role,
        "name": p.name,
        "region": p.region,
        "billing_unit": p.billing_unit,
        "unit_price_krw": float(p.unit_price) if p.unit_price is not None else -1.0,
        "public_status": domain.support_status(p.public_support),
        "closed_status": domain.support_status(p.closed_network_support),
        "free_status": domain.support_status(p.free_tier),
        "source_url": p.source_url,
        "checked_at": p.checked_at.isoformat(),
        "source_type": "meta",
    }
