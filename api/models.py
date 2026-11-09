"""FastAPI 요청·응답 JSON 형식. (F2013)

응답 형식은 cspnav.schemas의 dataclass와 같은 필드를 쓴다. /docs(Swagger)에서 모양을 확인할 수 있다.
"""

from __future__ import annotations

from datetime import date
from typing import Optional, Union

from pydantic import BaseModel, Field

Support = Union[bool, str]
SectorField = Field("public", pattern="^(public|private|learning)$", description="부문: public / private / learning")


# ── 요청 ────────────────────────────────────────────────
class AskRequest(BaseModel):
    item_id: str = Field(..., description="상품 항목ID (예: NCP-CMP-01)")
    question: str = Field(..., min_length=1, max_length=1000)
    sector: str = SectorField


class RequirementIn(BaseModel):
    workload: str = "웹 서비스"
    instances: int = Field(1, ge=1, le=50)
    vcpu: int = Field(2, ge=1, le=64)
    memory_gb: int = Field(8, ge=1, le=512)
    need_db: bool = True
    storage_gb: int = Field(100, ge=0, le=100_000)
    hours: int = Field(730, ge=1, le=744)
    budget: int = Field(300_000, ge=0)
    security: list[str] = Field(default_factory=list, description="폐쇄망(사설 연결) / 공공 요건 / 웹 방화벽(WAF)")
    note: str = ""
    data_grade: str = Field("모름", pattern="^(모름|상|중|하)$")


class RecommendRequest(BaseModel):
    requirement: RequirementIn
    sector: str = SectorField


class ExploreRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=300)
    sector: str = SectorField


# ── 응답 ────────────────────────────────────────────────
class ProductOut(BaseModel):
    item_id: str
    csp: str
    name: str
    category: str
    role: str
    spec: str
    vcpu: Optional[float]
    memory_gb: Optional[float]
    price_text: str
    currency: str
    unit_price_orig: Optional[float]
    unit_price: Optional[float]
    billing_unit: str
    qty_unit: str
    official_monthly: Optional[float]
    price_note: str
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
    stale: bool = Field(False, description="확인일이 기준일(기본 90일)보다 오래되면 true — 재확인 권장 (F2019)")


class EvidenceOut(BaseModel):
    number: int
    source_type: str
    source_label: str
    title: str
    source: str
    checked_at: date
    stale: bool
    csp: str = ""
    item_id: str = ""
    snippet: str = ""


class AnswerOut(BaseModel):
    text: str
    evidences: list[EvidenceOut] = Field(description="실제로 인용된 근거만 (F2008)")
    cited: list[int]
    notices: list[str] = []
    disclaimer: str


class StatusOut(BaseModel):
    meta_count: int
    doc_chunk_count: int
    api_key_ready: bool
    missing_env: list[str]
    index_ready: bool
    fake_mode: bool
    product_count: int
    disclaimer: str


class ProductListOut(BaseModel):
    items: list[ProductOut]


class CostLineOut(BaseModel):
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
    stale: bool
    sector_status: str
    source_type: str
    note: str = ""


class CandidateOut(BaseModel):
    csp: str
    eligible: bool
    lines: list[CostLineOut]
    monthly_total: int
    within_budget: bool
    unknown_items: list[str]
    excluded_reasons: list[str]
    notes: list[str]


class RecommendOut(BaseModel):
    sector: str
    recommended_csp: Optional[str]
    candidates: list[CandidateOut]
    answer: AnswerOut


class HitOut(BaseModel):
    product: ProductOut
    monthly_estimate: Optional[int]
    estimate_basis: str
    sector_status: str
    reason: str


class ExploreOut(BaseModel):
    conditions: list[str]
    hits: list[HitOut]
