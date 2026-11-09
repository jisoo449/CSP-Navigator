"""F2015 RAG 전후 품질 비교: 같은 질문을 RAG 없이 / RAG로 답하게 하고 결과를 문서로 남긴다.

실행 (csp_navigator 폴더에서, 색인을 만든 뒤):
    python scripts/compare_rag.py
출력: docs/04_RAG_전후비교_실행결과.md  (평가 칸은 사람이 채운다: 사실 정확성 · 근거 제시 · 모름 인정)

질문은 요구사항 정의서 3.3의 Q1~Q5를 쓰고, RAG 쪽은 질문과 관련된 상품을 골라 질의응답(F2009) 흐름으로 답한다.
질문·상품은 아래 QUESTIONS에서 바꿀 수 있다.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from langchain_core.messages import HumanMessage, SystemMessage  # noqa: E402

from cspnav import settings  # noqa: E402
from cspnav.data_prep import domain  # noqa: E402
from cspnav.errors import ServiceError  # noqa: E402
from cspnav.rag.llm import invoke_text  # noqa: E402
from cspnav.services import get_service  # noqa: E402

# (번호, 질문, RAG에 쓸 상품 항목ID, 부문)
QUESTIONS = [
    ("Q1", "지방자치단체 민원 시스템을 클라우드로 옮기려 한다. 공공 요건을 충족하는 CSP는 어디인가?", "NHN-CMP-02", "public"),
    ("Q2", "인터넷과 완전히 분리된 사내망에서만 접근하는 ERP를 구성하려면 어떤 상품이 필요한가?", "KT-NET-02", "private"),
    ("Q3", "월 예산 5만 원 안에서 학습용 웹 서버 + DB를 띄울 수 있는 가장 저렴한 조합은?", "NCP-CMP-05", "learning"),
    ("Q4", "서울 리전에서 2vCPU·8GB 서버를 월 730시간 쓰면 CSP별 비용 차이는?", "NCP-CMP-01", "learning"),
    ("Q5", "공공기관이 외부 SaaS가 아닌 IaaS로 구성할 때 데이터 저장 위치 요건은?", "SCP-CMP-04", "public"),
]

NO_RAG_SYSTEM = ("너는 클라우드 아키텍트다. 사용자의 질문에 네가 아는 지식으로 한국어로 답하라. "
                 "700자 안팎, 핵심 먼저.")


def no_rag(question: str) -> str:
    return invoke_text([SystemMessage(content=NO_RAG_SYSTEM), HumanMessage(content=question)])


def main() -> int:
    env = settings.load_env()
    if env.missing() and not settings.fake_mode():
        print("[실패] .env에 비어 있는 항목이 있습니다: " + ", ".join(env.missing()))
        return 1
    svc = get_service()
    out = [
        "# RAG 전후 품질 비교 — 실행 결과 (F2015)",
        "",
        f"> 실행 시각: {datetime.now():%Y-%m-%d %H:%M} · LLM: `{env.llm_model or '(점검 모드)'}` · "
        f"임베딩: `{env.embedding_model or '(점검 모드)'}` · Top-k {settings.get('retrieval.top_k')} · "
        f"청크 {settings.get('chunking.web.chunk_size')}/{settings.get('chunking.web.chunk_overlap')}",
        "> 평가 칸(사실 정확성·근거 제시·모름 인정)은 사람이 원문 출처와 대조해 채운다. 채우기 전에는 '미확인'이다.",
        "",
        f"> {domain.DISCLAIMER}",
        "",
    ]
    for qid, question, item_id, sector in QUESTIONS:
        print(f"{qid} 실행 중…")
        product = svc.get_product(item_id)
        try:
            before = no_rag(question)
        except ServiceError as err:
            before = f"(실행 실패: {err.user_message})"
        try:
            ans = svc.ask(item_id, question, sector)
            after = ans.text
            by_no = {e.number: e for e in ans.evidences}
            cites = [by_no[n] for n in ans.cited if n in by_no]
            cite_lines = [f"  - [근거 {e.number}] ({domain.SOURCE_TYPE_LABELS.get(e.source_type, e.source_type)}) "
                          f"{e.title} — {e.source} · 확인일 {e.checked_at}" for e in cites] or ["  - (인용된 근거 없음)"]
        except ServiceError as err:
            after, cite_lines = f"(실행 실패: {err.user_message})", []
        out += [
            f"## {qid}. {question}",
            "",
            f"- RAG 쪽 선택 상품: `{item_id}` {product.name if product else '(없음)'} · 부문 {domain.SECTORS[sector]}",
            "",
            "### RAG 없이",
            "",
            before,
            "",
            "### RAG 사용",
            "",
            after,
            "",
            "인용 근거:",
            *cite_lines,
            "",
            "| 기준 | RAG 없이 | RAG 사용 | 메모 |",
            "|---|---|---|---|",
            "| 사실 정확성 (요금·인증·리전이 출처와 일치) | 미확인 | 미확인 | |",
            "| 근거 제시 (주장마다 출처 확인 가능) | 미확인 | 미확인 | |",
            "| 모름 인정 (근거 없는 부분을 '확인되지 않음'으로) | 미확인 | 미확인 | |",
            "",
        ]
    path = ROOT / "docs" / "04_RAG_전후비교_실행결과.md"
    path.parent.mkdir(exist_ok=True)
    path.write_text("\n".join(out), encoding="utf-8")
    print(f"저장: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
