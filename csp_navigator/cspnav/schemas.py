"""서비스 계층과 UI(Streamlit·FastAPI)가 주고받는 데이터 형식. (NF2005)

UI 프로토타입(ui/schemas.py)을 실제 데이터에 맞게 넓혔다.
- Product: 원래 통화의 요금 원문·단가와 원화 환산 단가를 함께 둔다. 계산할 수 없는 요금은 None.
- 지원 여부(Support): True(지원) / False(미지원) / 문자열(예: '확인 필요', '계정 단위')
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional, Union

Support = Union[bool, str]
UNKNOWN = "확인 필요"


@dataclass(frozen=True)
class Product:
    """상품 메타데이터 1건. (F2001)"""

    item_id: str
    csp: str
    name: str
    category: str                    # CMP / DB / STG / NET / SEC
    role: str                        # 설계안 조합용 구분값 (예: server, db_mysql, net_vpn)
    spec: str
    vcpu: Optional[float]
    memory_gb: Optional[float]
    price_text: str                  # 공식 페이지 표기 그대로
    currency: str                    # USD / KRW
    unit_price_orig: Optional[float] # 원래 통화 단가 (billing_unit 기준)
    unit_price: Optional[float]      # 원화 환산 단가 (billing_unit 기준). 계산 불가면 None
    billing_unit: str                # hour / month / gb_month / other
    qty_unit: str                    # 대 / 개 / GB / 연결 …
    official_monthly: Optional[float]  # 공식 월 요금(원). 있으면 월 사용 시 이 값을 쓴다
    price_note: str                  # 환산 근거·추가 과금 안내
    region: str
    public_support: Support
    public_note: str
    closed_network_support: Support
    closed_note: str
    free_tier: Support
    free_note: str
    description: str
    source_url: str
    checked_at: date
    is_dummy: bool = False


@dataclass(frozen=True)
class ServerPrice:
    """서버 가격표(csp_server_prices.csv) 1행. 추천 설계안의 서버 단가에 쓴다. (F2018)"""

    price_id: str
    csp: str
    platform: str
    family: str
    server_type: str
    vcpu: float
    memory_gb: float
    included_disk: str
    currency: str
    hourly_orig: Optional[float]
    monthly_orig: Optional[float]    # 공식 월 요금(원래 통화)
    note: str
    source_url: str
    checked_at: date


@dataclass(frozen=True)
class StoragePrice:
    """Block Storage 단가표(csp_block_storage_prices.csv) 1행. (F2018)"""

    storage_id: str
    csp: str
    storage_type: str
    unit_text: str
    currency: str
    per_gb_month_orig: float
    note: str
    source_url: str
    checked_at: date


@dataclass
class Evidence:
    """답변에 붙는 근거 1건. (F2007, F2008, F2016, F2019)"""

    number: int
    source_type: str         # meta / price / web / pdf / wiki / summary / public_data
    title: str
    source: str              # URL 또는 "파일명 · n쪽"
    checked_at: date
    csp: str = ""
    item_id: str = ""
    snippet: str = ""
    chunk_id: str = ""
    content: str = ""        # LLM에 넘기는 본문(화면에는 snippet만)


@dataclass
class Answer:
    """답변 본문과 근거. cited에는 본문이 실제로 인용한 근거 번호만 담는다. (F2007, F2008)"""

    text: str
    evidences: list[Evidence] = field(default_factory=list)
    cited: list[int] = field(default_factory=list)
    notices: list[str] = field(default_factory=list)   # 수집 실패·캐시 사용 등 안내 (F2012)


@dataclass
class Requirement:
    """CSP 추천 입력값. (F2010)"""

    workload: str
    instances: int
    vcpu: int
    memory_gb: int
    need_db: bool
    storage_gb: int
    hours: int
    budget: int
    security: list[str]
    note: str = ""
    data_grade: str = "모름"   # 공공 부문: 상 / 중 / 하 / 모름 (F2017)


@dataclass
class CostLine:
    """설계안 상품 1줄의 비용 계산 결과. (F2018)"""

    item_id: str
    product_name: str
    category: str
    quantity: int
    qty_unit: str
    hours: Optional[int]
    unit_price: float
    billing_unit: str
    subtotal: int
    formula: str
    source_url: str
    checked_at: date
    sector_status: str       # ok / unknown
    source_type: str = "meta"   # meta(상품 메타) / price(가격표)
    note: str = ""


@dataclass
class CspCandidate:
    """CSP 1곳의 후보 비교 결과. (F2010, F2017)"""

    csp: str
    eligible: bool
    lines: list[CostLine]
    monthly_total: int
    within_budget: bool
    unknown_items: list[str]
    excluded_reasons: list[str]
    notes: list[str] = field(default_factory=list)


@dataclass
class Recommendation:
    """CSP 추천·설계 결과. (F2010)"""

    requirement: Requirement
    sector: str
    candidates: list[CspCandidate]
    recommended_csp: Optional[str]
    answer: Answer


@dataclass
class ProductHit:
    """조건 탐색 결과 카드 1장. (F2011)"""

    product: Product
    monthly_estimate: Optional[int]
    estimate_basis: str
    sector_status: str       # ok / unknown
    reason: str


@dataclass
class ExploreResult:
    """조건 탐색 결과. conditions는 해석한 조건 목록이다. (F2011)"""

    conditions: list[str]
    hits: list[ProductHit]


@dataclass
class SystemStatus:
    """색인·API 키 상태. (F2002 색인 건수 표시, F2012 안내)"""

    meta_count: int
    doc_chunk_count: int
    api_key_ready: bool
    missing_env: list[str] = field(default_factory=list)
    fake_mode: bool = False
    product_count: int = 0

    @property
    def index_ready(self) -> bool:
        return self.meta_count > 0
