"""CSP Navigator — Streamlit 화면 진입점. (F2009~F2012, F2017)

실행 (csp_navigator 폴더에서):
    streamlit run ui/app.py

화면은 views/ 아래 페이지 4개로 나뉘고, 데이터·답변은 cspnav.services의 실제 RAG 구현에서 온다. (NF2005)
UI 프로토타입(../ui)의 화면 구조를 그대로 옮기고 (더미) 서비스만 실제 서비스로 바꿨다.
"""

import sys
from pathlib import Path

_UI = Path(__file__).resolve().parent
for _p in (str(_UI.parent), str(_UI)):   # cspnav 패키지와 ui/components 를 import 경로에 넣는다
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st  # noqa: E402

from components.common import current_service, init_state, render_disclaimer_banner, render_sidebar_status  # noqa: E402
from cspnav.data_prep import domain  # noqa: E402

st.set_page_config(page_title="CSP Navigator", page_icon="☁️", layout="wide")
init_state()

nav = st.navigation([
    st.Page("views/home.py", title="홈", icon=":material/home:", default=True),
    st.Page("views/recommend.py", title="CSP 추천·설계", icon=":material/architecture:"),
    st.Page("views/explore.py", title="조건 탐색", icon=":material/manage_search:"),
    st.Page("views/chat.py", title="상품 질의응답", icon=":material/chat:"),
])

# 부문 선택은 모든 화면에 공통으로 적용된다. (F2017)
with st.sidebar:
    st.radio(
        "부문",
        options=list(domain.SECTORS),
        format_func=domain.SECTORS.get,
        key="sector",
        horizontal=True,
        help="부문에 따라 공공 요건·폐쇄망 지원 조건이 검색·추천 단계에 적용됩니다.",
    )
    st.caption(domain.SECTOR_HELP[st.session_state.sector])

render_disclaimer_banner()   # 모든 화면 상단 면책 문구 (F2012)
nav.run()
render_sidebar_status(current_service())
