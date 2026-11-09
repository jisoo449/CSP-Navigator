"""상품 질의응답 화면. (F2009, F2007, F2008, F2012, F2017, F2019)"""

import streamlit as st

from components.common import (
    current_service,
    persistent_selectbox,
    render_answer,
    render_product_summary,
    render_status_notices,
    safe_call,
)
from cspnav.data_prep import domain

EXAMPLE_QUESTIONS = [
    "이 상품을 월 730시간 쓰면 비용이 얼마인가요?",
    "공공기관이 이 상품을 써도 되나요?",
    "사내 폐쇄망에서 이 상품을 쓰려면 무엇이 더 필요한가요?",
]

svc = current_service()
sector = st.session_state.sector

st.title("상품 질의응답")
st.caption("사이드바에서 상품을 고른 뒤 질문하세요. 대화 기록은 상품별로 따로 남습니다.")

ready = render_status_notices(safe_call(svc.get_status))
products = safe_call(svc.list_products) or []
by_id = {p.item_id: p for p in products}

# 조건 탐색 카드에서 넘어온 경우, 사이드바 선택값을 그 상품으로 맞춘다. (F2011 → F2009)
pending = st.session_state.pop("pending_product", None)
if pending in by_id:
    st.session_state.sel_csp = by_id[pending].csp
    st.session_state.sel_cat = by_id[pending].category
    st.session_state.sel_product = pending

ids: list[str] = []
with st.sidebar:
    st.subheader("상품 선택")
    csp = persistent_selectbox("CSP", ["전체", *domain.CSPS], "sel_csp")
    cat = persistent_selectbox(
        "분류", ["전체", *domain.CATEGORIES], "sel_cat",
        format_func=lambda c: "전체" if c == "전체" else f"{domain.CATEGORIES[c]} ({c})",
    )
    ids = [p.item_id for p in products
           if (csp == "전체" or p.csp == csp) and (cat == "전체" or p.category == cat)]
    if ids:
        persistent_selectbox("상품", ids, "sel_product",
                             format_func=lambda i: f"{by_id[i].csp} · {by_id[i].name}")


def _chat(product) -> None:
    """선택 상품의 대화 화면. st.stop()을 쓰지 않아 사이드바 하단 안내가 항상 그려진다. (F2009, F2012)"""
    render_product_summary(product)

    history = st.session_state.chats.setdefault(product.item_id, [])
    with st.sidebar:
        if st.button("이 상품 대화 지우기", icon=":material/delete:", disabled=not history):
            history.clear()
            st.rerun()

    # 이전 대화 다시 그리기 — 근거 목록도 함께 그린다. (F2008)
    for msg in history:
        with st.chat_message(msg["role"]):
            if msg["role"] == "user":
                st.markdown(msg["content"])
            else:
                render_answer(msg["answer"])

    question = st.chat_input(f"{product.name}에 대해 질문하세요", disabled=not ready)

    if not history and ready:
        st.caption("예시 질문")
        cols = st.columns(len(EXAMPLE_QUESTIONS))
        for col, example in zip(cols, EXAMPLE_QUESTIONS):
            if col.button(example, width="stretch"):
                question = example

    if question:
        history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.status("답변을 준비하고 있습니다…", expanded=True) as box:   # 진행 상태 (F2012)
                answer = safe_call(svc.ask, product.item_id, question, sector, on_progress=box.write)
                box.update(label="답변 준비 완료" if answer else "답변을 만들지 못했습니다",
                           state="complete" if answer else "error", expanded=False)
            if answer:
                render_answer(answer)
                history.append({"role": "assistant", "answer": answer})
            else:
                history.pop()   # 실패한 질문은 기록에 남기지 않는다


if ids:
    _chat(by_id[st.session_state.sel_product])
elif products:
    st.info("조건에 맞는 상품이 없습니다. 사이드바에서 CSP나 분류를 바꿔 보세요.")
else:
    st.warning("상품 데이터가 없습니다. README 3장의 데이터 준비 절차(scripts/prepare_data.py)를 먼저 실행하세요.")
