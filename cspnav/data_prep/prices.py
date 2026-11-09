"""서버·Block Storage 가격표(CSV) 로드. 추천 설계안의 서버·디스크 단가에 쓴다. (F2010, F2018)

csp_server_prices.csv(1,708행)와 csp_block_storage_prices.csv(30행)는 1일차 수집 결과다. 원본은 수정하지 않는다.
표준 라이브러리만 쓴다.
"""

from __future__ import annotations

import csv
from datetime import date
from functools import lru_cache
from typing import Optional

from cspnav import settings
from cspnav.data_prep import domain
from cspnav.schemas import ServerPrice, StoragePrice


def _float(value: str) -> Optional[float]:
    value = (value or "").strip().replace(",", "")
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


@lru_cache(maxsize=1)
def load_servers() -> tuple[ServerPrice, ...]:
    """서버 가격표. 파일이 없으면 빈 목록. (F2018)"""
    path = settings.resolve_path("server_csv")
    if not path.exists():
        return tuple()
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            csp = domain.csp_name(r["csp"]) or domain.csp_name(r["item_id"])
            vcpu, mem = _float(r["vcpu"]), _float(r["memory_gb"])
            if not csp or vcpu is None or mem is None:
                continue
            rows.append(ServerPrice(
                price_id=r["item_id"], csp=csp, platform=r["platform"], family=r["category"],
                server_type=r["server_type"], vcpu=vcpu, memory_gb=mem, included_disk=r["included_disk"],
                currency="USD" if r["currency"] == "USD" else "KRW",
                hourly_orig=_float(r["hourly_price"]), monthly_orig=_float(r["official_monthly_price"]),
                note=r["note"], source_url=r["source_url"],
                checked_at=date.fromisoformat(r["checked_at"]),
            ))
    return tuple(rows)


@lru_cache(maxsize=1)
def load_storages() -> tuple[StoragePrice, ...]:
    """Block Storage 단가표. price_per_gb_month(원래 통화, GB-월 환산값)를 쓴다. (F2018)"""
    path = settings.resolve_path("storage_csv")
    if not path.exists():
        return tuple()
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            csp = domain.csp_name(r["csp"])
            per_gb = _float(r["price_per_gb_month"])
            if not csp or per_gb is None:
                continue
            rows.append(StoragePrice(
                storage_id=r["storage_id"], csp=csp, storage_type=r["storage_type"], unit_text=f"{r['unit_price']} {r['unit']}",
                currency="USD" if r["currency"] == "USD" else "KRW", per_gb_month_orig=per_gb,
                note=r["note"], source_url=r["source_url"], checked_at=date.fromisoformat(r["checked_at"]),
            ))
    return tuple(rows)


def needs_boot_disk(server: ServerPrice) -> Optional[bool]:
    """서버 단가에 OS 디스크가 빠져 있는가. True=별도 필요, False=포함, None=확인 필요. (F2018)"""
    disk = server.included_disk
    if "확인 필요" in disk:
        return None
    if "포함" in disk and "별도" not in disk:
        return False
    if any(w in disk for w in ("별도", "없음")) or disk.startswith("로컬"):
        return True
    if any(w in disk for w in ("HDD", "SSD")) and "GB" in disk:
        return False
    return None
