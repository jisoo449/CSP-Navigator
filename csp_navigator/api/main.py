"""FastAPI 서버 + HTML/CSS/JS 프론트엔드 제공. (F2013, NF2004)

실행 (csp_navigator 폴더에서):
    uvicorn api.main:app --port 8000
브라우저: http://localhost:8000  ·  API 문서: http://localhost:8000/docs

API (요청·응답 JSON 형식은 api/models.py)
    GET  /api/status                    색인 건수·키 상태 (F2002, F2012)
    GET  /api/products?csp=&category=   상품 목록 (F2009)
    GET  /api/products/{item_id}        상품 1건
    POST /api/ask                       상품 질의응답 (F2003~F2008)
    POST /api/recommend                 CSP 추천·설계 (F2010, F2017, F2018)
    POST /api/explore                   조건 탐색 (F2011)

오류는 {"detail": "사용자용 문구"}로만 돌려준다. 추적 정보·키·프롬프트는 응답에 넣지 않는다(NF2004).
"""

from __future__ import annotations

import logging
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.models import (  # noqa: E402
    AnswerOut,
    AskRequest,
    ExploreOut,
    ExploreRequest,
    ProductListOut,
    ProductOut,
    RecommendOut,
    RecommendRequest,
    StatusOut,
)
from cspnav.data_prep import domain  # noqa: E402
from cspnav.errors import ServiceError  # noqa: E402
from cspnav.formatting import is_stale  # noqa: E402
from cspnav.schemas import Answer, Product, Requirement  # noqa: E402
from cspnav.services import get_service  # noqa: E402

logger = logging.getLogger("cspnav.api")
app = FastAPI(title="CSP Navigator API", version="0.1",
              description="RAG 기반 CSP 추천·인프라 설계. " + domain.DISCLAIMER)


# ── 오류 처리 (NF2004) ───────────────────────────────────
@app.exception_handler(ServiceError)
async def _service_error(_: Request, exc: ServiceError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": exc.user_message})


@app.exception_handler(RequestValidationError)
async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    fields = ", ".join(".".join(str(x) for x in e.get("loc", [])[1:]) for e in exc.errors())
    return JSONResponse(status_code=422, content={"detail": f"입력값을 확인하세요: {fields}"})


@app.exception_handler(Exception)
async def _unexpected(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("처리 중 오류")
    return JSONResponse(status_code=500, content={"detail": "처리 중 문제가 생겼습니다. 잠시 후 다시 시도해 주세요."})


# ── 변환 ────────────────────────────────────────────────
def product_out(p: Product) -> dict:
    data = asdict(p)
    data.pop("is_dummy", None)
    data["stale"] = is_stale(p.checked_at)
    return data


def answer_out(a: Answer) -> dict:
    """인용된 근거만 내보낸다. LLM용 본문(content)·청크 ID는 빼고 snippet만. (F2008, NF2004)"""
    by_no = {e.number: e for e in a.evidences}
    shown = []
    for n in a.cited:
        e = by_no.get(n)
        if e is None:
            continue
        shown.append({
            "number": e.number, "source_type": e.source_type,
            "source_label": domain.SOURCE_TYPE_LABELS.get(e.source_type, e.source_type),
            "title": e.title, "source": e.source, "checked_at": e.checked_at, "stale": is_stale(e.checked_at),
            "csp": e.csp, "item_id": e.item_id, "snippet": e.snippet,
        })
    return {"text": a.text, "evidences": shown, "cited": a.cited, "notices": a.notices, "disclaimer": domain.DISCLAIMER}


# ── 엔드포인트 ──────────────────────────────────────────
@app.get("/api/status", response_model=StatusOut)
def status() -> dict:
    """색인 건수·키 상태 (F2002, F2012)"""
    s = get_service().get_status()
    return {**asdict(s), "index_ready": s.index_ready, "disclaimer": domain.DISCLAIMER}


@app.get("/api/meta")
def meta() -> dict:
    """화면 구성용 상수: CSP·분류·부문·입력 선택지."""
    return {"csps": domain.CSPS, "categories": domain.CATEGORIES, "sectors": domain.SECTORS,
            "sector_help": domain.SECTOR_HELP, "workloads": domain.WORKLOADS,
            "security_options": domain.SECURITY_OPTIONS, "data_grades": domain.DATA_GRADES,
            "source_labels": domain.SOURCE_TYPE_LABELS, "disclaimer": domain.DISCLAIMER}


@app.get("/api/products", response_model=ProductListOut)
def products(csp: Optional[str] = None, category: Optional[str] = None) -> dict:
    """상품 목록 (F2009)"""
    return {"items": [product_out(p) for p in get_service().list_products(csp or None, category or None)]}


@app.get("/api/products/{item_id}", response_model=ProductOut)
def product(item_id: str) -> dict:
    p = get_service().get_product(item_id)
    if p is None:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")
    return product_out(p)


@app.post("/api/ask", response_model=AnswerOut)
async def ask(body: AskRequest) -> dict:
    """상품 질의응답 (F2003~F2008)"""
    answer = await run_in_threadpool(get_service().ask, body.item_id, body.question, body.sector)
    return answer_out(answer)


@app.post("/api/recommend", response_model=RecommendOut)
async def recommend(body: RecommendRequest) -> dict:
    """CSP 추천·설계 (F2010, F2017, F2018)"""
    req = Requirement(**body.requirement.model_dump())
    rec = await run_in_threadpool(get_service().recommend, req, body.sector)
    candidates = []
    for c in rec.candidates:
        d = asdict(c)
        for line in d["lines"]:
            line["stale"] = is_stale(line["checked_at"])
        candidates.append(d)
    return {"sector": rec.sector, "recommended_csp": rec.recommended_csp, "candidates": candidates,
            "answer": answer_out(rec.answer)}


@app.post("/api/explore", response_model=ExploreOut)
async def explore(body: ExploreRequest) -> dict:
    """조건 탐색 (F2011)"""
    res = await run_in_threadpool(get_service().explore, body.query, body.sector)
    return {"conditions": res.conditions,
            "hits": [{"product": product_out(h.product), "monthly_estimate": h.monthly_estimate,
                      "estimate_basis": h.estimate_basis, "sector_status": h.sector_status, "reason": h.reason}
                     for h in res.hits]}


# 정적 파일(HTML·CSS·JS)은 마지막에 붙인다. /api/* 가 먼저 매칭된다.
app.mount("/", StaticFiles(directory=str(Path(__file__).parent / "static"), html=True), name="static")
