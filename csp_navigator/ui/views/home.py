"""홈 화면: 서비스 소개, 색인 현황, 바로 가기. (F2002, F2012, F2019)"""

import streamlit as st

from components.common import current_service, render_status_notices, safe_call
from cspnav import settings
from cspnav.data_prep import domain
from cspnav.formatting import is_stale

svc = current_service()

st.title("CSP Navigator")
st.markdown(
    "요구사항(워크로드·규모·예산·보안 조건)과 부문을 입력하면, 색인된 상품 메타데이터와 외부 문서를 근거로 "
    "6개 CSP(AWS·GCP·NCP·NHN Cloud·KT Cloud·SCP) 중 조건을 만족하면서 저렴한 CSP를 추천하고 인프라 설계안을 제시합니다."
)

status = safe_call(svc.get_status)
render_status_notices(status)

products = safe_call(svc.list_products) or []
stale = sum(1 for p in products if is_stale(p.checked_at))
c1, c2, c3 = st.columns(3)
c1.metric("상품 메타 색인 (csp_product_meta)", f"{status.meta_count if status else 0:,}건")
c2.metric("외부 문서 색인 (csp_external_docs)", f"{status.doc_chunk_count if status else 0:,}청크")
c3.metric(f"재확인 권장 상품 ({settings.get('freshness_days', 90)}일 초과)", f"{stale:,}건")
if products:
    latest = max(p.checked_at for p in products)
    st.caption(f"상품 데이터 {len(products):,}건 · 최근 확인일 {latest:%Y-%m-%d} · 각 CSP 공식 요금 페이지 기준(VAT 별도, 온디맨드)")

st.subheader("부문")
st.table([
    {"부문": domain.SECTORS[code], "핵심 판단 기준": domain.SECTOR_HELP[code]}
    for code in domain.SECTORS
])
st.caption(f"현재 선택: **{domain.SECTORS[st.session_state.sector]}** · 사이드바에서 바꿀 수 있습니다.")

st.subheader("바로 가기")
st.page_link("views/recommend.py", label="CSP 추천·설계 — 요구사항으로 CSP와 설계안 받기", icon=":material/architecture:")
st.page_link("views/explore.py", label="조건 탐색 — 자연어 조건으로 상품 찾기", icon=":material/manage_search:")
st.page_link("views/chat.py", label="상품 질의응답 — 상품을 골라 근거 기반으로 묻기", icon=":material/chat:")
