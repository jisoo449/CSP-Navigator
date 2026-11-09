"""CSP 추천·인프라 설계 화면. (F2010, F2017, F2018, F2019, F2012)"""

import streamlit as st

from components.common import (
    current_service,
    link_md,
    render_disclaimer_footer,
    render_evidences,
    render_status_notices,
    safe_call,
)
from cspnav.data_prep import domain
from cspnav.formatting import freshness_text, krw
from cspnav.schemas import Recommendation, Requirement
from cspnav.services.cost import hours_per_month

svc = current_service()
sector = st.session_state.sector

st.title("CSP 추천·인프라 설계")
st.caption(f"현재 부문: **{domain.SECTORS[sector]}** — 사이드바에서 바꿀 수 있습니다. 부문 조건은 후보 비교에 바로 적용됩니다.")

ready = render_status_notices(safe_call(svc.get_status))

with st.form("requirement_form"):
    c1, c2 = st.columns(2)
    workload = c1.selectbox("워크로드", domain.WORKLOADS)
    budget = c2.number_input("월 예산(원)", min_value=0, value=300_000, step=10_000)
    c3, c4, c5 = st.columns(3)
    instances = c3.number_input("서버 수(대)", min_value=1, max_value=50, value=2)
    vcpu = c4.selectbox("서버당 vCPU", [1, 2, 4, 8], index=1)
    memory = c5.selectbox("서버당 메모리(GB)", [1, 2, 4, 8, 16, 32], index=3)
    c6, c7, c8 = st.columns(3)
    need_db = c6.checkbox("관리형 DB(MySQL) 포함", value=True)
    storage = c7.number_input("오브젝트 스토리지(GB)", min_value=0, max_value=100_000, value=100, step=50)
    hours = c8.number_input("월 사용 시간", min_value=1, max_value=744, value=hours_per_month(),
                            help=f"기본값 {hours_per_month()}시간(24시간 × 약 30.4일)")
    security = st.multiselect("보안·연결 조건", domain.SECURITY_OPTIONS)
    grade = "모름"
    if sector == "public":
        grade = st.selectbox("공공 시스템 등급(클라우드 보안인증 등급 기준)", domain.DATA_GRADES,
                             help="상·중 등급 시스템은 하등급 CSAP 인증만 보유한 CSP를 후보에서 뺍니다. 모르면 '모름'.")
    note = st.text_area("추가 요구사항(선택)", placeholder="예: 사내망에서만 접근하는 ERP, 개인정보 포함")
    submitted = st.form_submit_button("추천 받기", type="primary", icon=":material/auto_awesome:", disabled=not ready)

if submitted:
    req = Requirement(workload, int(instances), int(vcpu), int(memory), need_db, int(storage),
                      int(hours), int(budget), list(security), note, grade)
    with st.status("추천안을 만들고 있습니다…", expanded=True) as box:   # 진행 상태 (F2012)
        rec = safe_call(svc.recommend, req, sector, on_progress=box.write)
        box.update(label="추천안 준비 완료" if rec else "추천안을 만들지 못했습니다",
                   state="complete" if rec else "error", expanded=False)
    # 실패하면 이전 추천 결과를 지운다. 남겨 두면 "만들지 못했습니다" 아래에 옛 결과가 보여 헷갈린다. (F2012)
    st.session_state.last_recommendation = rec


def _render(rec: Recommendation) -> None:
    """추천 결과: 요약 지표 → 추천 이유 → 설계안·비용 / 후보 비교 / 근거 탭."""
    st.subheader("추천 결과")
    if rec.sector != st.session_state.sector:
        st.caption(f"이 결과는 부문 「{domain.SECTORS[rec.sector]}」 기준입니다. 바뀐 부문으로 보려면 다시 추천을 받으세요.")

    best = next((c for c in rec.candidates if c.csp == rec.recommended_csp), None)
    if best:
        m1, m2, m3 = st.columns(3)
        m1.metric("추천 CSP", best.csp)
        m2.metric("예상 월 비용", krw(best.monthly_total))
        m3.metric("예산 잔액", krw(rec.requirement.budget - best.monthly_total))
        if not best.within_budget:
            st.warning("예산 안에 드는 후보가 없습니다. 가장 저렴한 후보를 보여 줍니다.", icon=":material/savings:")
    else:
        st.warning("조건을 모두 만족하는 CSP 후보가 없습니다.", icon=":material/search_off:")

    st.markdown(rec.answer.text)
    for n in rec.answer.notices:
        st.caption(f":material/info: {n}")

    tab_design, tab_compare, tab_evidence = st.tabs(["설계안·비용 계산", "CSP 후보 비교", "근거"])

    with tab_design:   # F2018: 코드 계산 + 계산식 + 단가 출처·확인일
        if best:
            st.dataframe(
                [
                    {
                        "구성": line.product_name,
                        "계산식": line.formula,
                        "월 비용": krw(line.subtotal),
                        "부문 조건": "확인 필요" if line.sector_status == "unknown" else "충족",
                        "단가 출처": "요금표(CSV)" if line.source_type == "price" else "상품 메타데이터",
                        "확인일": f"{line.checked_at:%Y-%m-%d}",
                        "최신성": freshness_text(line.checked_at),
                    }
                    for line in best.lines
                ],
                hide_index=True,
                width="stretch",
            )
            st.markdown(f"**합계 {krw(best.monthly_total)}** / 월 예산 {krw(rec.requirement.budget)}")
            st.caption("비용은 단가 × 수량 × 사용 시간으로 코드에서 계산했습니다(LLM 계산 아님). VAT 별도, 트래픽·약정 할인 제외.")
            for n in best.notes:
                st.caption(f"· {n}")
            with st.expander("단가 출처"):
                for line in best.lines:
                    st.markdown(f"- {line.product_name}: {link_md(line.source_url)} · 확인일 {line.checked_at:%Y-%m-%d}"
                                + (f"  \n  {line.note}" if line.note else ""))
        else:
            st.info("표시할 설계안이 없습니다.")

    with tab_compare:   # F2010 후보 비교, F2017 부문 필터 결과
        if rec.candidates:
            rows = sorted(rec.candidates, key=lambda c: (not c.eligible, c.monthly_total))
            st.dataframe(
                [
                    {
                        "CSP": ("★ " if c.csp == rec.recommended_csp else "") + c.csp,
                        "조건 충족": "충족" if c.eligible else "제외",
                        "예상 월 비용": krw(c.monthly_total) if c.eligible else "-",
                        "예산 이내": ("예" if c.within_budget else "아니오") if c.eligible else "-",
                        "확인 필요 항목": ", ".join(c.unknown_items) or "-",
                        "제외 사유": "; ".join(c.excluded_reasons) or "-",
                        "참고": "; ".join(c.notes) or "-",
                    }
                    for c in rows
                ],
                hide_index=True,
                width="stretch",
            )
            st.caption("조건을 만족하지 않는 상품은 추천 근거에서 뺐고, 값이 '확인 필요'인 상품은 빼지 않고 표시했습니다.")
        else:
            st.info("비교할 후보가 없습니다.")

    with tab_evidence:   # F2008
        render_evidences(rec.answer.evidences, rec.answer.cited)

    with st.expander("입력한 요구사항"):
        r = rec.requirement
        st.markdown(
            f"- 워크로드: {r.workload}\n- 서버: {r.instances}대 × {r.vcpu}vCPU/{r.memory_gb}GB, 월 {r.hours}시간\n"
            f"- DB: {'포함' if r.need_db else '없음'} · 스토리지: {r.storage_gb:,}GB\n"
            f"- 보안·연결 조건: {', '.join(r.security) or '없음'}\n- 월 예산: {krw(r.budget)}"
            + (f"\n- 공공 시스템 등급: {r.data_grade}" if rec.sector == "public" else "")
            + (f"\n- 추가 요구사항: {r.note}" if r.note else "")
        )
    render_disclaimer_footer()


if st.session_state.last_recommendation:
    _render(st.session_state.last_recommendation)
