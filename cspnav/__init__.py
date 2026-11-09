"""CSP Navigator — RAG 기반 CSP 추천·인프라 설계 서비스.

모듈 구성 (NF2005)
- data_prep   : 데이터 준비(상품 메타 변환·로드, 가격표, 외부 문서 수집). 도메인에 묶인 코드는 여기 모은다.
- vectorstore : Chroma 컬렉션 2개, 청킹, 색인
- rag         : LLM 연결, 프롬프트 3개, LangGraph retrieve/generate, 근거 번호
- services    : CSP 추천·설계, 조건 탐색, 비용 계산, 부문 필터
- (ui/, api/) : Streamlit 화면, FastAPI 서버 + HTML 프론트
"""
