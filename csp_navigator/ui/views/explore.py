"""조건 기반 상품 탐색 화면. 카드를 누르면 그 상품의 대화로 이어진다. (F2011, F2017, F2019, F2012)"""

import streamlit as st

from components.common import (
    current_service,
    freshness_md,
    render_disclaimer_footer,
    render_status_notices,
    safe_call,
    support_md,
)
from cspnav.data_prep import domain
from cspnav.formatting import krw

EXAMPLES = [
    "서울 리전, 폐쇄망 지원, 월 3만 원 이하 MySQL",
    "공공 요건을 만족하는 웹 방화벽",
    "무료 티어가 있는 소형 서버",
]

svc = current_service()
sector = st.session_state.sector

st.title("조건 기반 상품 탐색")
st.caption(f"현재 부문: **{domain.SECTORS[sector]}** — 부문 조건을 만족하지 않는 상품은 검색 단계에서 빠집니다.")

ready = render_status_notices(safe_call(svc.get_status))


def _fill(text: str) -> None:
    st.session_state.explore_q = text


cols = st.columns(len(EXAMPLES))
for col, example in zip(cols, EXAMPLES):
    col.button(example, on_click=_fill, args=(example,), width="stretch", disabled=not ready)

query = st.text_input("찾는 조건을 자연어로 입력하세요", key="explore_q",
                      placeholder="예: 서울 리전, 폐쇄망 지원, 월 3만 원 이하 MySQL", disabled=not ready)

if query and ready:
    with st.spinner("조건을 해석하고 상품 메타데이터에서 후보를 찾고 있습니다…"):   # 진행 상태 (F2012)
        result = safe_call(svc.explore, query, sector)
    if result:
        st.markdown("**해석한 조건** " + " ".join(f":gray-badge[{c}]" for c in result.conditions))
        if not result.hits:
            st.info("조건에 맞는 상품이 문서에서 확인되지 않음. 조건을 줄여 다시 찾아보세요.", icon=":material/search_off:")
        else:
            st.caption(f"{len(result.hits)}건 · 예상 월 비용이 낮은 순")
            grid = st.columns(3)
            for i, hit in enumerate(result.hits):
                p = hit.product
                with grid[i % 3].container(border=True):
                    st.markdown(f"**{p.name}**")
                    st.caption(f"{p.csp} · {domain.CATEGORIES[p.category]} · {p.region}")
                    st.markdown(p.spec)
                    st.caption(f"요금 {p.price_text}")
                    st.markdown(f"예상 월 **{krw(hit.monthly_estimate)}**  \n({hit.estimate_basis})")
                    st.markdown(f"공공 {support_md(p.public_support)} 폐쇄망 {support_md(p.closed_network_support)} "
                                f"무료 {support_md(p.free_tier)}")
                    if hit.sector_status == "unknown":
                        st.markdown(":orange-badge[부문 조건 확인 필요]")
                    st.markdown(freshness_md(p.checked_at))
                    if hit.reason:
                        st.caption(hit.reason)
                    if st.button("이 상품으로 질문하기", key=f"ask_{p.item_id}", icon=":material/chat:", width="stretch"):
                        st.session_state.pending_product = p.item_id
                        st.switch_page("views/chat.py")
        render_disclaimer_footer()
