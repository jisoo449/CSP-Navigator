"""도메인(CSP·상품·부문)에 묶인 상수와 규칙을 한곳에 모은다. (NF2005)

다른 도메인으로 바꿀 때는 이 파일과 md_products.py, prices.py를 바꾸면 된다.
표준 라이브러리만 쓴다.
"""

from __future__ import annotations

import re
from typing import Optional

# ── CSP ─────────────────────────────────────────────────
CSPS = ["AWS", "GCP", "NCP", "NHN Cloud", "KT Cloud", "SCP"]

# 항목ID 접두어(AWS-CMP-01) · CSV의 csp 열 · md 섹션 제목 → 화면 표시명
CSP_ALIASES = {
    "AWS": "AWS",
    "GCP": "GCP",
    "NCP": "NCP",
    "NCP(네이버클라우드)": "NCP",
    "NHN": "NHN Cloud",
    "NHN Cloud": "NHN Cloud",
    "KT": "KT Cloud",
    "KT Cloud": "KT Cloud",
    "SCP": "SCP",
    "SCP(삼성 클라우드 플랫폼)": "SCP",
}


def csp_name(raw: str) -> Optional[str]:
    """여러 표기를 화면 표시명으로 바꾼다. 모르면 None."""
    raw = raw.strip()
    if raw in CSP_ALIASES:
        return CSP_ALIASES[raw]
    prefix = raw.split("-")[0]
    return CSP_ALIASES.get(prefix)


# ── 분류 ────────────────────────────────────────────────
CATEGORIES = {"CMP": "컴퓨팅", "DB": "데이터베이스", "STG": "스토리지", "NET": "네트워크", "SEC": "보안"}
CATEGORY_FROM_KO = {"컴퓨팅": "CMP", "DB": "DB", "데이터베이스": "DB", "스토리지": "STG", "네트워크": "NET", "보안": "SEC"}

# ── 부문 (F2017) ─────────────────────────────────────────
SECTORS = {"public": "공공", "private": "private", "learning": "학습용"}
SECTOR_HELP = {
    "public": "공공 요건(클라우드 보안인증) 충족 여부가 1차 조건입니다. 비용은 그다음에 비교합니다.",
    "private": "폐쇄망·전용 회선·사설 연결 지원 여부가 1차 조건입니다.",
    "learning": "최저 비용과 무료 티어·크레딧을 우선합니다.",
}

# ── 근거 출처 종류 (F2007, F2016) ────────────────────────
SOURCE_TYPE_LABELS = {
    "meta": "상품 메타데이터",
    "price": "요금표(가격 CSV)",
    "web": "CSP 공식 웹 문서",
    "pdf": "PDF 자료",
    "wiki": "한국어 위키백과",
    "summary": "수집 결과 요약",
    "public_data": "공공데이터",
}

# ── 추천 화면 입력 선택지 (F2010) ────────────────────────
WORKLOADS = ["웹 서비스", "사내 업무 시스템(ERP 등)", "민원·대국민 서비스", "데이터 분석", "학습·실습"]
SECURITY_OPTIONS = ["폐쇄망(사설 연결)", "공공 요건", "웹 방화벽(WAF)"]
DATA_GRADES = ["모름", "상", "중", "하"]

# 면책 문구 (요구사항 정의서 3.4 원문) (F2012)
DISCLAIMER = (
    "요금, 인증 보유 현황, 리전 정보는 수시로 바뀔 수 있습니다. "
    "이 답변은 색인된 문서를 근거로 한 참고용이며, CSP의 공식 견적이나 보안·법률 전문가의 검토를 대신하지 않습니다. "
    "각 근거의 확인일을 함께 확인하세요."
)


# ── 상품 역할 분류: 설계안 조합에 쓴다 (F2010) ─────────────
def classify_role(category: str, name: str, spec: str, closed_raw: str = "", note: str = "") -> str:
    """분류·상품명·사양으로 설계안에서 맡을 역할을 정한다. (F2010)"""
    text = f"{name} {spec} {note}".lower()
    if category == "CMP":
        return "server"
    if category == "DB":
        if "mysql" in text:
            return "db_mysql"
        if "postgres" in text:
            return "db_postgres"
        if any(w in text for w in ("redis", "cache", "memorystore")):
            return "db_cache"
        return "db_other"
    if category == "STG":
        if any(w in text for w in ("객체", "object", "s3 ", "cloud storage")) or name.lower().startswith("s3"):
            return "storage_object"
        if any(w in text for w in ("블록", "block", "ebs", "persistent disk")):
            return "storage_block"
        if any(w in text for w in ("파일", "file", "efs", "nas", "filestore")):
            return "storage_file"
        return "storage_other"
    if category == "NET":
        # 폐쇄망 열의 확인값(지원(전용회선) / 지원(IPsec VPN))을 상품명보다 먼저 본다.
        if "전용회선" in closed_raw:
            return "net_dedicated"
        if "ipsec" in closed_raw.lower() or "vpn" in text:
            return "net_vpn"
        if any(w in text for w in ("전용 회선", "전용 포트", "direct connect", "interconnect",
                                                              "cloud connect", "connect hub")):
            return "net_dedicated"
        if "사설 엔드포인트" in closed_raw or "privatelink" in text:
            return "net_private_endpoint"
        if any(w in text for w in ("load balancer", "부하 분산")):
            return "net_lb"
        if any(w in text for w in ("firewall", "방화벽")):
            return "net_firewall"
        return "net_other"
    if category == "SEC":
        if any(w in text for w in ("waf", "웹 방화벽", "cloud armor")):
            return "sec_waf"
        if any(w in text for w in ("kms", "key", "키 관리")):
            return "sec_kms"
        return "sec_other"
    return "other"


ROLE_LABELS = {
    "server": "서버", "boot_disk": "서버 디스크", "db_mysql": "DB(MySQL)", "storage_object": "오브젝트 스토리지",
    "net_dedicated": "전용 회선", "net_vpn": "IPsec VPN", "net_lb": "로드밸런서", "sec_waf": "웹 방화벽",
}


# ── 지원 여부 값 매핑 (F2017) ─────────────────────────────
def map_public(raw: str) -> tuple[object, str]:
    """md의 '공공' 열 → (지원 여부, 설명). 상품 단위 제공 여부는 수집 자료에 없으므로 '확인 필요'로 둔다."""
    raw = raw.strip()
    if raw == "하등급":
        return "확인 필요", "CSP 단위 CSAP 하등급 IaaS 인증 보유. 상품 단위 제공 여부는 확인 필요"
    if raw.startswith("별도"):
        return "확인 필요", "공공기관용 별도 플랫폼이 CSAP IaaS 인증 범위. 이 단가는 민간용 요금"
    if raw in ("지원", "O"):
        return True, raw
    if raw in ("미지원", "X"):
        return False, raw
    return "확인 필요", raw or "확인 필요"


def map_closed(raw: str) -> tuple[object, str]:
    """md의 '폐쇄망' 열 → (지원 여부, 설명). '지원(…)'으로 확인된 값만 True."""
    raw = raw.strip()
    m = re.match(r"지원\s*\((.+)\)", raw)
    if m:
        return True, m.group(1)
    if raw == "지원":
        return True, "지원"
    if raw == "미지원":
        return False, "미지원"
    return "확인 필요", "전용회선·VPN·사설 엔드포인트 지원 여부 미확인"


def map_free(raw: str) -> tuple[object, str]:
    """md의 '무료 티어' 열 → (값, 설명). 상품 단위로 확인된 무료만 True, 계정 단위 혜택은 '계정 단위'."""
    raw = raw.strip()
    if "무료" in raw and "계정" not in raw:
        return True, raw
    if raw.startswith("계정"):
        return "계정 단위", raw
    return "확인 필요", raw or "확인 필요"


def support_status(value: object) -> str:
    """지원 여부 값 → 'ok' / 'fail' / 'unknown' (Chroma 메타데이터·필터용). (F2017)"""
    if value is True:
        return "ok"
    if value is False:
        return "fail"
    return "unknown"


# ── 사양 파싱 ─────────────────────────────────────────────
_VCPU = re.compile(r"(\d+(?:\.\d+)?)\s*v(?:CPU|Core)", re.IGNORECASE)
_MEM = re.compile(r"/\s*(\d+(?:\.\d+)?)\s*Gi?B", re.IGNORECASE)


def parse_vcpu_mem(spec: str, name: str) -> tuple[Optional[float], Optional[float]]:
    """'2vCPU / 8GiB' 형태에서 vCPU·메모리(GB)를 뽑는다. 사양에 없으면 상품명에서 찾는다."""
    vcpu = mem = None
    for text in (spec, name):
        if vcpu is None:
            m = _VCPU.search(text)
            if m:
                vcpu = float(m.group(1))
        if mem is None:
            m = _MEM.search(text)
            if m:
                mem = float(m.group(1))
    return vcpu, mem


# ── 요금 원문 파싱 (F2018) ────────────────────────────────
_PRICE = re.compile(
    r"^\s*(?:(?P<pre>\d+\s*[A-Za-z]+)당\s*)?(?P<num>\d[\d,]*(?:\.\d+)?(?:e-?\d+)?)\s*(?P<cur>USD|원)\s*/\s*(?P<unit>.+?)\s*$"
)
_SIZE_UNIT = re.compile(r"^(?P<size>\d*)\s*(?P<u>GB|GiB)$")


def parse_price(text: str) -> dict:
    """요금 원문 1칸을 구조화한다. 통화 환산·시간 환산은 하지 않는다(products.py가 설정값으로 한다).

    반환: {currency, amount, per, size, qty_unit, extra, status}
      per = hour | month | day | gb_month | gb_hour | other
      status = ok | other(복합 요금이라 자동 계산 불가)
    """
    text = (text or "").strip()
    result = {"currency": "", "amount": None, "per": "other", "size": 1.0, "qty_unit": "", "extra": "", "status": "other"}
    if not text:
        return result
    head, extra = text, ""
    for sep in (" + ", ", "):
        if sep in head:
            head, rest = head.split(sep, 1)
            extra = (rest + (" " + extra if extra else "")).strip()
    paren = re.findall(r"\((.*?)\)", head)
    head = re.sub(r"\(.*?\)", "", head).strip()
    m = _PRICE.match(head)
    if not m:
        return result
    currency = "USD" if m.group("cur") == "USD" else "KRW"
    amount = float(m.group("num").replace(",", ""))
    unit = m.group("unit").strip()
    pre = (m.group("pre") or "").replace(" ", "")
    extras = [*paren, extra] if extra else paren
    result.update(currency=currency, amount=amount, extra="; ".join(e for e in extras if e), status="ok")

    if unit.endswith("시간"):
        prefix = unit[:-2].rstrip("-").strip()
        sm = _SIZE_UNIT.match(prefix)
        if sm:
            result.update(per="gb_hour", size=float(sm.group("size") or 1), qty_unit="GB")
        else:
            result.update(per="hour", qty_unit=pre or prefix)
    elif unit.endswith("월"):
        prefix = unit[:-1].rstrip("-").strip()
        sm = _SIZE_UNIT.match(prefix)
        if sm:
            result.update(per="gb_month", size=float(sm.group("size") or 1), qty_unit="GB")
        else:
            result.update(per="month", qty_unit=pre or prefix)
    elif unit.endswith("일"):
        prefix = unit[:-1].rstrip("-").strip()
        result.update(per="day", qty_unit=pre or prefix)
    else:
        result.update(per="other", status="other")
    return result


def default_qty_unit(category: str, role: str) -> str:
    """요금 원문에 수량 단위가 없을 때 쓰는 단위."""
    if category == "CMP":
        return "대"
    if role in ("net_dedicated",):
        return "회선"
    return "개"


def official_monthly_from_note(note: str) -> Optional[float]:
    """비고의 '월 85,120원' 같은 공식 월 요금을 찾는다(NCP 서버). 없으면 None."""
    m = re.search(r"월\s*([\d,]+)\s*원", note or "")
    return float(m.group(1).replace(",", "")) if m else None
