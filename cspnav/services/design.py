"""CSP별 설계안 구성과 후보 비교. (F2010, F2017, F2018)

요구사항을 구성 요소(서버·서버 디스크·DB·오브젝트 스토리지·사설 연결·WAF·로드밸런서)로 바꾸고,
CSP마다 조건을 만족하는 가장 저렴한 상품을 골라 비용을 코드로 계산한다. 추천 이유 문장만 LLM이 쓴다.

선택 규칙(모두 settings.json design.* 의 기본값)
- 서버: 서버 가격표에서 vCPU·메모리가 요구 이상인 사양 중 월 비용이 가장 낮은 것
  (제외: exclude_server_platforms, 비고에 exclude_server_note_keywords가 든 행 — 예: 계정 기본료가 따로 붙는 플랫폼)
- 서버 디스크: 서버 단가에 OS 디스크가 빠져 있으면 boot_disk_gb만큼 CSP별 SSD Block Storage를 더한다
- DB: 상품 메타의 MySQL 중 db_min_vcpu·db_min_memory_gb 이상에서 가장 저렴한 것 (학습용은 learning_* 값)
- 사설 연결: closed_network_roles 순서(기본 전용회선 → VPN, 학습용은 VPN 먼저)로 '지원' 확인된 상품 중 가장 저렴한 것
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from cspnav import settings
from cspnav.data_prep.prices import needs_boot_disk
from cspnav.schemas import CostLine, CspCandidate, Product, Requirement, ServerPrice, StoragePrice
from cspnav.services import cost
from cspnav.services.filters import check_csp_public, check_product, needs_from


@dataclass
class DesignData:
    """설계에 쓰는 데이터 묶음."""

    products: tuple[Product, ...]
    servers: tuple[ServerPrice, ...]
    storages: tuple[StoragePrice, ...]
    csap: list[dict]


@dataclass
class DesignResult:
    """CSP 1곳의 설계 결과와, 근거로 쓸 원천(상품·가격표 행)."""

    candidate: CspCandidate
    products_used: list[Product] = field(default_factory=list)
    servers_used: list[ServerPrice] = field(default_factory=list)
    storages_used: list[StoragePrice] = field(default_factory=list)


def _product_monthly(p: Product, qty: int, hours: int) -> float:
    line = cost.calc_product_line(p, qty, hours, "ok")
    return float(line.subtotal) if line else float("inf")


def pick_server(servers: tuple[ServerPrice, ...], csp: str, vcpu: int, mem: int, hours: int) -> Optional[ServerPrice]:
    """요구 사양 이상 중 월 비용 최저 서버. (F2010)"""
    exclude_platforms = set(settings.get("design.exclude_server_platforms", []))
    exclude_notes = settings.get("design.exclude_server_note_keywords", [])
    best, best_cost = None, float("inf")
    for s in servers:
        if s.csp != csp or s.vcpu < vcpu or s.memory_gb < mem:
            continue
        if s.platform in exclude_platforms or any(k in s.note for k in exclude_notes):
            continue
        try:
            monthly, _ = cost.server_monthly(s, hours)
        except ValueError:
            continue
        # 같은 값이면 사양이 작은 쪽(과잉 사양을 피함)
        key = (monthly, s.vcpu, s.memory_gb)
        if best is None or key < (best_cost, best.vcpu, best.memory_gb):
            best, best_cost = s, monthly
    return best


def pick_product(products: tuple[Product, ...], csp: str, roles: list[str], qty: int, hours: int,
                 min_vcpu: float = 0, min_mem: float = 0, require_closed: bool = False) -> Optional[Product]:
    """역할(roles 순서 우선)과 최소 사양을 만족하는 상품 중 월 비용 최저. (F2010)"""
    for role in roles:
        pool = []
        for p in products:
            if p.csp != csp or p.role != role:
                continue
            if require_closed and p.closed_network_support is not True:
                continue
            vcpu = p.vcpu if p.vcpu is not None else (1.0 if min_vcpu <= 1 else 0.0)   # 공유 vCPU는 1개로 본다
            if vcpu < min_vcpu or (p.memory_gb or 0) < min_mem:
                continue
            pool.append((_product_monthly(p, qty, hours), p))
        pool = [x for x in pool if x[0] != float("inf")] or pool
        if pool:
            return min(pool, key=lambda x: x[0])[1]
    return None


def build_candidate(csp: str, req: Requirement, sector: str, data: DesignData) -> DesignResult:
    """CSP 1곳의 설계안·비용·부문 조건 판단. (F2010, F2017, F2018)"""
    need_public, need_closed = needs_from(sector, req.security)
    hours = req.hours or cost.hours_per_month()
    lines: list[CostLine] = []
    unknown: list[str] = []
    reasons: list[str] = []
    notes: list[str] = []
    result = DesignResult(candidate=CspCandidate(csp, False, [], 0, False, [], []))

    # 공공: CSP 단위 CSAP 판단 (F2017)
    csp_public_status = "ok"
    if need_public:
        csp_public_status, why = check_csp_public(csp, req.data_grade, data.csap)
        (reasons if csp_public_status == "fail" else notes).append(f"공공 요건: {why}")

    def add_product(p: Optional[Product], qty: int, label: str, missing: str, required: bool = True) -> None:
        if p is None:
            (reasons if required else notes).append(missing)
            return
        status = check_product(p, need_public, need_closed)
        if status == "fail":
            reasons.append(f"{p.name}: 부문·보안 조건 미지원")
            return
        line = cost.calc_product_line(p, qty, hours, status, label=f"{label}: {p.name}")
        if line is None:
            unknown.append(f"{p.name}(복합 요금, 계산 제외)")
            return
        if status == "unknown":
            unknown.append(p.name)
        lines.append(line)
        result.products_used.append(p)

    # 1) 서버 (가격표)
    server = pick_server(data.servers, csp, req.vcpu, req.memory_gb, hours)
    if server is None:
        reasons.append(f"서버: {req.vcpu}vCPU/{req.memory_gb}GB 이상 사양이 서버 가격표에 없음")
    else:
        status = "unknown" if (need_closed or csp_public_status == "unknown") else "ok"
        lines.append(cost.calc_server_line(server, req.instances, hours, status))
        result.servers_used.append(server)
        if status == "unknown":
            unknown.append(f"서버 {server.server_type}")
        # 2) 서버 디스크
        boot = needs_boot_disk(server)
        if boot is True:
            sid = (settings.get("design.boot_disk_storage_id", {}) or {}).get(csp)
            storage = next((s for s in data.storages if s.storage_id == sid), None)
            if storage:
                gb = int(settings.get("design.boot_disk_gb", 50))
                lines.append(cost.calc_storage_line(storage, gb, req.instances, status, "서버 디스크"))
                result.storages_used.append(storage)
            else:
                notes.append("서버 디스크 단가를 찾지 못해 비용에서 빠짐")
        elif boot is None:
            unknown.append(f"서버 디스크({server.included_disk})")

    # 3) DB
    if req.need_db:
        learning = sector == "learning"
        min_v = settings.get("design.learning_db_min_vcpu" if learning else "design.db_min_vcpu", 2)
        min_m = settings.get("design.learning_db_min_memory_gb" if learning else "design.db_min_memory_gb", 4)
        db = pick_product(data.products, csp, ["db_mysql"], 1, hours, min_v, min_m)
        add_product(db, 1, "DB", f"DB: {min_v}vCPU/{min_m}GB 이상 MySQL 상품이 상품 메타데이터에 없음")

    # 4) 오브젝트 스토리지
    if req.storage_gb > 0:
        obj = pick_product(data.products, csp, ["storage_object"], req.storage_gb, hours)
        add_product(obj, req.storage_gb, "스토리지", "오브젝트 스토리지 상품이 상품 메타데이터에 없음")

    # 5) 사설 연결 (폐쇄망)
    if need_closed:
        key = "design.learning_closed_network_roles" if sector == "learning" else "design.closed_network_roles"
        roles = settings.get(key, ["net_dedicated", "net_vpn"])
        link = pick_product(data.products, csp, roles, 1, hours, require_closed=True)
        add_product(link, 1, "사설 연결", "사설 연결: 전용회선·VPN 지원이 확인된 상품이 없음")
        if link is not None and link.price_note:
            notes.append(f"{link.name}: {link.price_note}")

    # 6) WAF
    if "웹 방화벽(WAF)" in req.security:
        waf = pick_product(data.products, csp, ["sec_waf"], 1, hours)
        add_product(waf, 1, "웹 방화벽", "웹 방화벽(WAF) 상품이 상품 메타데이터에 없음")

    # 7) 로드밸런서 (서버가 여러 대일 때, 없으면 안내만)
    if req.instances >= int(settings.get("design.add_lb_when_instances_gte", 2)):
        lb = pick_product(data.products, csp, ["net_lb"], 1, hours)
        add_product(lb, 1, "로드밸런서", "로드밸런서 상품이 상품 메타데이터에 없어 비용에서 빠짐", required=False)

    total = sum(line.subtotal for line in lines)
    result.candidate = CspCandidate(
        csp=csp, eligible=not reasons, lines=lines, monthly_total=total,
        within_budget=total <= req.budget, unknown_items=unknown, excluded_reasons=reasons, notes=notes,
    )
    return result


def choose_best(candidates: list[CspCandidate], sector: str) -> Optional[CspCandidate]:
    """조건 충족 후보 중 예산 안에서 가장 저렴한 CSP. 예산 안에 없으면 가장 저렴한 후보. (F2010)

    동률이면 '확인 필요' 항목이 적은 쪽을 고른다.
    """
    eligible = [c for c in candidates if c.eligible]
    pool = [c for c in eligible if c.within_budget] or eligible
    if not pool:
        return None
    return min(pool, key=lambda c: (c.monthly_total, len(c.unknown_items)))
