"""화면 공통 컴포넌트. (F2008, F2012, F2017, F2019, NF2004)"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Callable, Optional

import streamlit as st

from cspnav.data_prep import domain
from cspnav.errors import ServiceError
from cspnav.formatting import billing_label, is_stale, krw, support_text
from cspnav.schemas import Answer, Evidence, Product, SystemStatus

logger = logging.getLogger("csp_navigator.ui")

_SOURCE_BADGE_COLOR = {"meta": "blue", "price": "blue", "web": "violet", "pdf": "orange", "wiki": "green",
                       "summary": "gray", "public_data": "gray"}


# ── 상태·서비스 ──────────────────────────────────────────
def init_state() -> None:
    """세션 상태 기본값. 대화 기록은 상품 ID별로 따로 둔다. (F2009)"""
    defaults = {"sector": "public", "chats": {}, "last_recommendation": None}
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


@st.cache_resource(show_spinner=False)
def _service():
    from cspnav.services import get_service
    return get_service()


def current_service():
    """서비스 객체(앱 전체에서 1개). (NF2005)"""
    return _service()


def safe_call(fn: Callable[..., Any], *args, **kwargs) -> Any:
    """서비스 호출 오류를 사용자용 문구로 바꿔 보여 준다. 추적 정보는 서버 로그에만 남긴다. (NF2004)"""
    try:
        return fn(*args, **kwargs)
    except ServiceError as err:
        st.error(err.user_message, icon=":material/error:")
    except Exception:  # noqa: BLE001 — 화면에는 원인을 노출하지 않는다
        logger.exception("서비스 호출 실패")
        st.error("처리 중 문제가 생겼습니다. 잠시 후 다시 시도해 주세요.", icon=":material/error:")
    return None


def persistent_selectbox(label: str, options: list, store_key: str, **kwargs) -> Any:
    """페이지를 옮겨 다녀도 선택값이 남는 selectbox. (F2009)

    Streamlit은 화면에 그려지지 않은 위젯의 상태를 지우므로, 값을 별도 키(store_key)에 보관한다.
    """
    widget_key = f"w_{store_key}"
    if st.session_state.get(store_key) not in options:
        st.session_state[store_key] = options[0]
    st.session_state[widget_key] = st.session_state[store_key]

    def _sync() -> None:
        st.session_state[store_key] = st.session_state[widget_key]

    return st.selectbox(label, options, key=widget_key, on_change=_sync, **kwargs)


# ── 안내 ─────────────────────────────────────────────────
def render_disclaimer_banner() -> None:
    """화면 상단 면책 문구. (F2012, 요구사항 정의서 3.4)"""
    st.info(domain.DISCLAIMER, icon=":material/info:")


def render_disclaimer_footer() -> None:
    """답변 하단 면책 문구. (F2012, 요구사항 정의서 3.4)"""
    st.caption("※ " + domain.DISCLAIMER)


def render_status_notices(status: Optional[SystemStatus]) -> bool:
    """API 키 누락·색인 없음 안내. 사용할 수 있으면 True. (F2012)"""
    if status is None:
        return False
    ready = True
    if not status.api_key_ready:
        st.error("LLM·임베딩 API 키가 설정되지 않았습니다. 관리자에게 .env 설정을 요청하세요."
                 + (f" (비어 있는 항목: {', '.join(status.missing_env)})" if status.missing_env else ""),
                 icon=":material/key_off:")
        ready = False
    if not status.index_ready:
        st.warning("색인된 상품 데이터가 없습니다. 데이터 준비·색인 절차(README 3장)를 먼저 실행하세요.",
                   icon=":material/database:")
        ready = False
    if status.fake_mode:
        st.warning("점검 모드(CSPNAV_FAKE=1)입니다. 답변은 가짜 LLM이 만든 (더미) 문장입니다.", icon=":material/science:")
    return ready


def render_sidebar_status(svc) -> None:
    """사이드바 하단: 색인 건수. (F2002, F2012)"""
    with st.sidebar:
        st.divider()
        status = safe_call(svc.get_status)
        if status:
            st.caption(
                f"색인 현황  \n"
                f"· csp_product_meta: {status.meta_count:,}건  \n"
                f"· csp_external_docs: {status.doc_chunk_count:,}청크  \n"
                f"· 상품 데이터: {status.product_count:,}건"
            )


# ── 표시 변환 ────────────────────────────────────────────
def support_md(value: object) -> str:
    """지원 여부 배지(markdown). (F2017)"""
    color = "green" if value is True else "gray" if value is False else "orange"
    return f":{color}-badge[{support_text(value)}]"


def freshness_md(checked_at: date) -> str:
    """확인일과 '재확인 권장' 배지(markdown). (F2019)"""
    text = f"확인일 {checked_at:%Y-%m-%d}"
    if is_stale(checked_at):
        text += " :orange-badge[재확인 권장]"
    return text


def link_md(source: str) -> str:
    """URL이면 링크로, 파일명·쪽이면 그대로 보여 준다. (F2008)"""
    return f"[{source}]({source})" if source.startswith("http") else source


# ── 상품·근거 표시 ────────────────────────────────────────
def render_product_summary(product: Product) -> None:
    """선택 상품 요약 상자. (F2009, F2017, F2019)"""
    with st.container(border=True):
        st.markdown(f"#### {product.name}")
        st.caption(f"{product.csp} · {domain.CATEGORIES[product.category]} · {product.region} · ID `{product.item_id}`")
        c1, c2 = st.columns([3, 2])
        with c1:
            st.markdown(f"**사양** {product.spec}")
            price = f"**요금** {product.price_text}"
            if product.unit_price is not None:
                price += f" → 원화 환산 {krw(product.unit_price)} ({billing_label(product.billing_unit)})"
            st.markdown(price)
            if product.price_note:
                st.caption(product.price_note)
            st.markdown(product.description)
        with c2:
            st.markdown(f"공공 요건 {support_md(product.public_support)}")
            st.caption(product.public_note)
            st.markdown(f"폐쇄망 {support_md(product.closed_network_support)}")
            st.caption(product.closed_note)
            st.markdown(f"무료 티어 {support_md(product.free_tier)}")
            st.markdown(freshness_md(product.checked_at))
        st.caption(f"출처: {link_md(product.source_url)}")


def render_evidences(evidences: list[Evidence], cited: list[int]) -> None:
    """답변이 실제로 인용한 근거만 보여 준다. 인용이 없으면 그 사실을 안내한다. (F2008, F2016, F2019)"""
    by_no = {e.number: e for e in evidences}
    shown = [by_no[n] for n in cited if n in by_no]
    if not shown:
        st.info("이 답변에 인용된 근거가 없습니다. 색인된 문서에서 확인된 내용이 없다는 뜻입니다.", icon=":material/help:")
        return
    with st.expander(f"근거 {len(shown)}건 보기", icon=":material/format_quote:"):
        for e in shown:
            color = _SOURCE_BADGE_COLOR.get(e.source_type, "gray")
            label = domain.SOURCE_TYPE_LABELS.get(e.source_type, e.source_type)
            st.markdown(f"**[근거 {e.number}]** :{color}-badge[{label}] {e.title}")
            st.markdown(f"출처: {link_md(e.source)} · {freshness_md(e.checked_at)}")
            if e.snippet:
                st.caption(e.snippet)


def render_answer(answer: Answer) -> None:
    """답변 본문 + 안내 + 인용 근거 + 하단 면책 문구. (F2007, F2008, F2012)"""
    st.markdown(answer.text)
    for notice in answer.notices:
        st.caption(f":material/info: {notice}")
    render_evidences(answer.evidences, answer.cited)
    render_disclaimer_footer()
