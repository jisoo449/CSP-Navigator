"""프롬프트 3개 + 조건 탐색 해석 프롬프트. (F2003, F2004, F2007, F2011)

① 검색어 추출(프롬프트1): 클라우드 아키텍트 역할, JSON 배열만 출력
② 후보 문서 선별(프롬프트2): 제목·요약만 보고 고른다, JSON 배열만 출력
③ 답변 생성(프롬프트3): 검색된 근거만 사용, 주장마다 [근거 n], 근거가 없으면 "문서에서 확인되지 않음"
(+) 조건 탐색 해석: 자연어 조건 → 후보 상품 중 맞는 것만 JSON으로

각 시스템 프롬프트의 첫 줄 '# 작업:'은 사람이 읽기 위한 표시이자 가짜 LLM(점검용)이 작업을 구분하는 표시다.
프롬프트 전문은 화면에 노출하지 않는다(NF2004).
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from cspnav.data_prep import domain
from cspnav.schemas import Evidence

NOT_FOUND = "문서에서 확인되지 않음"

# ── ① 검색어 추출 ────────────────────────────────────────
KEYWORD_SYSTEM = """# 작업: 검색어 추출
너는 AWS·GCP·NCP(네이버클라우드)·NHN Cloud·KT Cloud·SCP(삼성 클라우드 플랫폼) 6개 CSP의 상품 구성과 요금 체계, 국내 공공 클라우드 요건(클라우드 보안인증 CSAP 등)에 정통한 클라우드 아키텍트다.
사용자가 고른 상품과 질문을 보고, 답의 근거가 될 외부 문서(CSP 공식 문서, 공공 요건 자료, 한국어 위키백과)를 찾을 검색어를 만든다.

규칙
- 검색어는 최대 {max_n}개, 각 2~6단어.
- 질문의 핵심(요금·과금, 폐쇄망·전용회선·VPN, 공공 요건·보안인증, 리전, 무료 티어 등)이 드러나게 쓴다.
- 상품명이나 CSP명이 들어간 검색어 1개, 일반 개념어(위키백과용) 1개 이상을 포함한다.
- 한국어를 기본으로 하되 상품명은 원래 표기를 쓴다.
- 출력은 JSON 문자열 배열 하나뿐이다. 설명·번호·코드 블록 표시를 붙이지 않는다.
예: ["NCP Server 요금 과금 방식", "클라우드 컴퓨팅 서비스 보안인증", "가상 사설망"]"""


def keyword_messages(product_text: str, sector: str, question: str, max_n: int) -> list:
    """프롬프트1 메시지. (F2003)"""
    human = (
        f"[선택 상품]\n{product_text}\n\n"
        f"[부문]\n{domain.SECTORS.get(sector, sector)} — {domain.SECTOR_HELP.get(sector, '')}\n\n"
        f"[질문]\n{question}"
    )
    return [SystemMessage(content=KEYWORD_SYSTEM.format(max_n=max_n)), HumanMessage(content=human)]


# ── ② 후보 문서 선별 ─────────────────────────────────────
SELECT_SYSTEM = """# 작업: 후보 문서 선별
너는 클라우드 기술 문서 선별 담당자다. 후보 문서의 제목과 요약만 보고, 질문에 답하는 근거가 될 문서를 고른다.

규칙
- 최대 {max_n}개를 고른다. 질문과 직접 관련된 문서만 고르고, 관련이 없으면 빈 배열 []을 낸다.
- 같은 내용으로 보이는 문서는 하나만 고른다.
- 선택 상품의 CSP와 다른 CSP의 문서는 질문이 비교를 요구할 때만 고른다.
- 출처 종류(web/pdf/wiki)가 다양하면 좋지만, 관련성이 우선이다.
- 출력은 고른 후보 id의 JSON 문자열 배열 하나뿐이다. 예: ["c2", "c5"]"""


def select_messages(question: str, product_text: str, candidates: list[tuple[str, str, str, str]], max_n: int) -> list:
    """프롬프트2 메시지. candidates = [(cid, 출처 종류, 제목, 요약)] — 본문은 보여 주지 않는다. (F2004)"""
    lines = [f"- id: {cid} | 출처: {stype} | 제목: {title} | 요약: {summary[:200]}"
             for cid, stype, title, summary in candidates]
    human = f"[질문]\n{question}\n\n[선택 상품]\n{product_text}\n\n[후보 문서]\n" + "\n".join(lines)
    return [SystemMessage(content=SELECT_SYSTEM.format(max_n=max_n)), HumanMessage(content=human)]


# ── ③ 답변 생성 ─────────────────────────────────────────
ANSWER_SYSTEM = f"""# 작업: 답변 생성
너는 MSP 없이 클라우드를 직접 고르려는 사용자를 돕는 CSP 비용·인프라 설계 상담가다.
아래 [근거]에 적힌 내용만 사용해 답한다. 네 기억이나 일반 상식으로 사실을 보태지 않는다.

규칙
1. 요금·인증 보유 현황·리전·사양처럼 바뀔 수 있는 사실은 근거에 있을 때만 쓴다. 근거에 없으면 그 부분은 "{NOT_FOUND}"이라고 쓴다.
2. 사실을 말하는 문장마다 끝에 근거 번호를 붙인다. 형식: [근거 1] 또는 [근거 1, 3]. 범위 표기([근거 1~3])나 괄호 안 설명([근거 1, 상품 메타데이터])은 쓰지 않는다. 없는 번호를 만들지 않는다.
   "{NOT_FOUND}"인 문장에는 근거 번호를 붙이지 않는다. 그 내용을 실제로 뒷받침한 근거만 인용한다.
3. 근거마다 붙은 출처 유형(상품 메타데이터 / 요금표 / CSP 공식 웹 문서 / PDF 자료 / 한국어 위키백과 / 수집 결과 요약)을 구분해, 필요하면 "상품 메타데이터에 따르면", "공식 문서에 따르면"처럼 밝힌다.
4. 금액은 근거에 적힌 단가와 [계산 결과]에 있는 값만 쓴다. 새로 계산하거나 반올림을 바꾸지 않는다.
5. '확인 필요'로 적힌 값은 지원한다고 단정하지 말고 확인이 필요하다고 쓴다.
6. 질문에 답할 근거가 하나도 없으면 "{NOT_FOUND}." 한 문장과 어떤 정보가 없었는지만 짧게 쓴다. 이때 근거 번호를 붙이지 않고, 질문과 상관없는 다른 정보를 덧붙이지 않는다.
7. 한국어로, 핵심 먼저, 마크다운 목록 위주로 700자 안팎. 머리말·맺음말 인사는 쓰지 않는다."""


def format_evidences(evidences: list[Evidence]) -> str:
    """근거 목록을 프롬프트용 텍스트로 만든다. 번호·출처 유형·제목·출처·확인일 + 본문. (F2007, F2008)"""
    blocks = []
    for e in evidences:
        label = domain.SOURCE_TYPE_LABELS.get(e.source_type, e.source_type)
        head = f"[근거 {e.number}] ({label}) {e.title} | 출처: {e.source} | 확인일: {e.checked_at.isoformat()}"
        blocks.append(f"{head}\n{e.content or e.snippet}")
    return "\n\n".join(blocks)


def answer_messages(question: str, sector: str, evidences: list[Evidence], extra_context: str = "") -> list:
    """프롬프트3 메시지. extra_context에는 코드가 계산한 비용표 등을 넣는다. (F2007, F2018)"""
    parts = [f"[부문]\n{domain.SECTORS.get(sector, sector)} — {domain.SECTOR_HELP.get(sector, '')}",
             f"[질문]\n{question}"]
    if extra_context:
        parts.append(f"[계산 결과]\n{extra_context}")
    parts.append("[근거]\n" + (format_evidences(evidences) if evidences else "(근거 없음)"))
    return [SystemMessage(content=ANSWER_SYSTEM), HumanMessage(content="\n\n".join(parts))]


# ── (+) 조건 탐색 해석 (F2011) ────────────────────────────
EXPLORE_SYSTEM = """# 작업: 조건 탐색
너는 클라우드 상품 탐색 도우미다. 사용자가 자연어로 적은 조건을 해석하고, [후보 상품] 중 조건을 모두 만족하는 상품만 고른다.

규칙
- 후보 정보에 적힌 내용으로만 판단한다. 후보에 없는 상품을 만들지 않는다.
- 지원 여부가 '확인 필요'인 조건은 만족으로 단정하지 말고, 고르되 reason에 '확인 필요'라고 밝힌다. '미지원'이면 고르지 않는다.
- 금액 조건(예: 월 3만 원 이하)은 직접 비교하지 말고 max_monthly_krw에 원 단위 숫자로만 적는다. 금액 비교는 프로그램이 한다. 금액 조건이 없으면 null.
- vCPU·메모리 조건(예: 2vCPU, 8GB 이상)도 min_vcpu, min_memory_gb에 숫자로만 적는다. 비교는 프로그램이 한다. 조건이 없으면 null.
- matches에는 조건을 만족하는 상품만 넣는다. 만족하지 않는 상품은 이유가 있더라도 matches에 넣지 않는다.
- conditions에는 해석한 조건을 짧은 한국어 구절로 적는다. 예: ["서울 리전", "폐쇄망 지원", "MySQL"]
- reason은 한 문장으로, 어떤 조건이 맞았는지 쓴다.
- 출력은 JSON 객체 하나뿐이다.
형식: {"conditions": ["..."], "max_monthly_krw": 30000, "min_vcpu": null, "min_memory_gb": null, "matches": [{"item_id": "NCP-DB-01", "reason": "..."}]}"""


def explore_messages(query: str, sector: str, candidates_text: str) -> list:
    """조건 탐색 해석 메시지. (F2011)"""
    human = (f"[조건]\n{query}\n\n[부문]\n{domain.SECTORS.get(sector, sector)}\n\n[후보 상품]\n{candidates_text}")
    return [SystemMessage(content=EXPLORE_SYSTEM), HumanMessage(content=human)]
