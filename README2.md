# CSP Navigator

> AI 코어 프로젝트 2회차 「RAG 기반 도메인 지식 서비스」
> MSP 없이 요구사항에 맞는 저렴한 CSP를 추천하고 인프라를 설계해 주는 RAG 서비스

> **면책** 요금, 인증 보유 현황, 리전 정보는 수시로 바뀔 수 있습니다. 이 서비스의 답변은 색인된 문서를 근거로 한 참고용이며, CSP의 공식 견적이나 보안·법률 전문가의 검토를 대신하지 않습니다. 각 근거의 확인일을 함께 확인하세요.

---

## 1. 개요

사용자가 **요구사항**(워크로드·규모·월 예산·보안 조건)과 **부문**(공공 / private / 학습용)을 입력하면, 서비스가 색인된 상품 메타데이터와 외부 문서를 근거로 6개 CSP(AWS, GCP, NCP, NHN Cloud, KT Cloud, SCP) 중 조건을 만족하면서 비용이 낮은 CSP를 추천하고, 상품 조합으로 된 인프라 설계안과 예상 월 비용을 근거 번호와 함께 보여 줍니다.

| 화면 | 하는 일 |
|---|---|
| CSP 추천·설계 | 요구사항 → CSP 6곳 후보 비교 → 추천 CSP·설계안·계산식·근거 |
| 조건 탐색 | "서울 리전, 폐쇄망 지원, 월 3만 원 이하 MySQL" 같은 자연어로 상품 카드 찾기 → 카드에서 질의응답으로 이동 |
| 상품 질의응답 | 상품을 골라 질문 → 외부 문서 수집·색인 → 근거 기반 답변(인용된 근거만 표시) |

데이터 규모: 상품 메타데이터 **108건**(CSP당 18건), 서버 가격표 1,708행, Block Storage 단가 30종, CSAP 인증 현황 8행. 모두 2026-10-21에 각 CSP 공식 요금 페이지·KISA 조회 페이지에서 확인한 값입니다(1일차 수집 결과).

## 2. 폴더 구조 (모듈 분리, NF2005)

```
csp_navigator/
├─ settings.json              조정값(청크 크기·Top-k·검색 방식·비용 기준·설계 규칙). 키는 넣지 않음
├─ .env.example               키·주소·모델명 항목(빈 값)
├─ requirements.txt           고정 스택
├─ cspnav/
│  ├─ settings.py             settings.json + .env 로드
│  ├─ schemas.py              서비스 ↔ 화면 데이터 형식
│  ├─ data_prep/              ① 데이터 준비 — 도메인에 묶인 코드는 여기 모음
│  │  ├─ domain.py            CSP·분류·부문 상수, 역할 분류, 요금 원문 파싱, 지원 여부 매핑
│  │  ├─ md_products.py       1일차 수집 결과(md) → data/processed/*.json
│  │  ├─ products.py          상품 로드·원화 환산·색인 텍스트 (F2001)
│  │  ├─ prices.py            서버·Block Storage 가격표 CSV
│  │  ├─ http_client.py       재시도·호출 간격·robots.txt·User-Agent (NF2006)
│  │  ├─ sources.py           출처별 후보·본문: web / pdf / wiki (F2016)
│  │  └─ collector.py         수집 흐름 + 캐시 (F2004, NF2002)
│  ├─ vectorstore/            ② vector store — 컬렉션 2개·청킹·색인 (F2002, F2005)
│  ├─ rag/                    ③ RAG 파이프라인 — 프롬프트 3개·LangGraph retrieve/generate·근거 번호
│  └─ services/               ④ 서비스 기능 — 추천·설계, 조건 탐색, 비용 계산, 부문 필터
├─ ui/                        ⑤ Streamlit 화면 (필수 기능)
├─ api/                       ⑤ FastAPI 서버 + static/ HTML·CSS·JS (심화 F2013)
├─ scripts/                   prepare_data · build_index · smoke_test · compare_rag
├─ data/                      processed(변환 결과) · chroma(색인) · cache(수집 캐시) · pdf(PDF 출처)
├─ docs/                      설계문서 · 검증결과 · RAG 전후 비교 · 출처와 이용 조건
└─ tests/fixtures/            점검용 발췌 데이터
```

원본 수집 자료는 상위 폴더 `../data/sources/`에 있고 **수정하지 않습니다**. 변환 결과만 `data/processed/`에 새로 씁니다.

## 3. 실행 방법 (Windows PowerShell 기준)

### 3.1 설치

```powershell
cd "C:\SSAFY16\workspace\08 관통 프로젝트\04 AI Application Core Project\csp_navigator"
python -m venv .venv                 # 상위 폴더의 실습용 .venv를 써도 된다
.venv\Scripts\activate
pip install -r requirements.txt
```

> 실습용 `.venv`에는 langsmith 0.14.11, uvicorn 0.54.0, pydantic 2.14.1 등 고정 스택과 다른 버전이 이미 깔려 있습니다. 위 명령이 고정 버전으로 맞춥니다. 실습 파일과 섞이지 않게 하려면 새 가상환경을 권장합니다.

### 3.2 .env

`csp_navigator/.env`를 만들고 `.env.example`의 항목을 채웁니다. 상위 폴더 `.env`를 먼저 읽으므로 `GMS_KEY`·`WIKI_CONTACT`가 이미 거기 있으면 나머지 세 줄만 추가하면 됩니다.

| 항목 | 필수 | 값 |
|---|---|---|
| `GMS_KEY` | 필수 | SSAFY GMS 키 |
| `GMS_BASE_URL` | 필수 | 실습 0단계(`step0_llm.py`)가 쓰는 GMS OpenAI 호환 주소 |
| `LLM_MODEL` | 필수 | 검증에 쓴 값: `gpt-4.1-mini` |
| `EMBEDDING_MODEL` | 필수 | 검증에 쓴 값: `text-embedding-3-small`(GMS에서 1,536차원으로 동작 확인) |
| `CONTACT` | 권장 | 외부 문서 수집 User-Agent용 영문 이메일(없으면 `WIKI_CONTACT` 사용) |

### 3.3 데이터 준비·색인

```powershell
python scripts\prepare_data.py     # ① md → data/processed/*.json (키 불필요)
python scripts\build_index.py      # ② 상품 메타 108건 + 공통 문서 색인 (임베딩 키 필요)
```

| 단계 | 성공하면 보이는 것 |
|---|---|
| ① | `상품 108건`, `CSP별: AWS 18, GCP 18, …`, `요금 자동 계산 제외(복합 요금): 1건 ['AWS-DB-04']`, `서버 가격 1708행` |
| ② | `csp_product_meta: 108건`, `csp_external_docs: n청크`. **다시 실행해도 108건 그대로**(청크 ID = 항목ID) |

처음부터 다시 만들려면 `python scripts\build_index.py --reset`.

### 3.4 화면 실행

```powershell
# 필수 기능 화면 (Streamlit) — 반드시 csp_navigator 폴더에서 실행 (.streamlit/config.toml 적용)
streamlit run ui\app.py

# 심화 F2013 화면 (FastAPI + HTML/CSS/JS)
uvicorn api.main:app --port 8000
#   화면: http://localhost:8000   API 문서: http://localhost:8000/docs
```

외부 문서(공식 웹 문서·위키백과·PDF)는 **상품 질의응답에서 처음 질문할 때** 수집·색인됩니다. 같은 검색어는 다시 수집하지 않습니다(캐시).

### 3.5 키 없이 흐름 점검

```powershell
python scripts\smoke_test.py
```

가짜 LLM·임베딩과 오프라인 모드로 변환 → 색인 → 질의응답 → 추천 → 탐색 → API까지 돌립니다. 마지막 줄이 `결과: n개 통과 / 0개 실패`면 성공입니다. 답변 문장은 (더미)이며 품질 평가에는 쓰지 않습니다.

## 4. 기능 구분

| 구분 | 번호 | 기능 | 구현 위치 |
|---|---|---|---|
| 필수 | F2001 | 상품 메타데이터 108건 적재·색인 텍스트 구성 | `data_prep/md_products.py`, `products.py` |
| 필수 | F2002 | 메타 색인(`csp_product_meta`, 항목당 1청크, ID=항목ID), 건수 표시 | `vectorstore/indexer.py`, 화면 홈·사이드바 |
| 필수 | F2003 | 검색어 추출(프롬프트1), 공식 문서 항상 포함 | `rag/prompts.py`, `services/navigator.py` |
| 필수 | F2004 | 출처별 후보 → 선별(프롬프트2) → 본문 저장, 검색어 캐시 | `data_prep/collector.py`, `sources.py` |
| 필수 | F2005 | 외부 문서 색인(`csp_external_docs`, ID=항목ID:문서ID:순번) | `vectorstore/indexer.py`, `chunking.py` |
| 필수 | F2006 | 메타 청크 항상 포함 + 유사도 검색 병합·중복 제거 | `rag/graph.py` `retrieve_evidences` |
| 필수 | F2007 | LangGraph retrieve/generate, 근거만 사용, "문서에서 확인되지 않음" | `rag/graph.py`, 프롬프트3 |
| 필수 | F2008 | `[근거 n]`, 인용된 근거만 제목·출처·확인일 표시 | `rag/citations.py`, 화면 근거 목록 |
| 필수 | F2009 | CSP·분류로 좁혀 상품 선택, 상품별 대화 기록 | `ui/views/chat.py` |
| 필수 | F2010 | CSP 추천·설계안 | `services/design.py`, `navigator.recommend` |
| 필수 | F2011 | 자연어 조건 탐색 → 카드 → 대화로 이동 | `navigator.explore`, `ui/views/explore.py` |
| 필수 | F2012 | 진행 상태, 색인 없음·키 누락·결과 없음 안내, 면책 문구 | 화면 전반 |
| 심화 | F2013 | HTML·CSS·JS + FastAPI, JSON 형식 정의 | `api/` |
| 심화 | F2014 | MMR — **미선택**. `settings.json`의 `retrieval.search_type`만 유지(`mmr`로 바꾸면 동작) | `vectorstore/store.py` |
| 심화 | F2015 | RAG 전후 비교(질문 5개, 세 기준) | `scripts/compare_rag.py`, `docs/04_*` |
| 심화 | F2016 | 공식 웹 문서 + PDF + 위키백과 + 수집 요약, 출처 종류 표시 | `data_prep/sources.py`, `chunking.py` |
| 추가 | F2017 | 부문 필터(검색 단계 where 필터 + CSAP 등급 판단, '확인 필요'는 제외하지 않음) | `services/filters.py` |
| 추가 | F2018 | 예상 월 비용 코드 계산 + 계산식 + 단가 출처·확인일 | `services/cost.py` |
| 추가 | F2019 | 확인일 표시, 90일(기본값) 초과 시 "재확인 권장" | `formatting.py`, 화면 |

## 5. 실제 연결 확인 (GMS)

2026-10-23 SSAFY GMS(LLM `gpt-4.1-mini`, 임베딩 `text-embedding-3-small`)로 아래 순서를 모두 실행했고, 결과는 `docs/03_검증결과.md`와 `docs/evidence/`에 있습니다. 다시 확인할 때는 같은 순서로 합니다.

1. `python scripts\build_index.py` → `csp_product_meta: 108건`
2. `streamlit run ui\app.py` → 홈의 색인 건수 108건, 키 누락 안내가 없어야 함
3. 상품 질의응답에서 `NCP · Server Standard-g2 2vCPU/8GB` 선택 → 예시 질문 → 진행 상태가 단계별로 바뀌고, 답변 아래 근거에 `상품 메타데이터` 근거(확인일 2026-10-21)가 보여야 함
4. 같은 질문을 한 번 더 → "캐시를 사용했습니다" 안내
5. CSP 추천·설계에서 기본값으로 추천 → 후보 비교 탭에 6개 CSP, 설계안 탭에 계산식
6. `python scripts\compare_rag.py` → `docs/04_RAG_전후비교_실행결과.md` 생성
7. `python scripts\verify_real.py` → 명세서 4장 확인 항목·설정값 비교 실험을 실행해 `docs/evidence/verify_real.json`에 기록(약 15분, 실험용 색인은 `data/experiments/`에 따로 만듦)

> Streamlit과 FastAPI를 동시에 띄우면 두 프로세스가 같은 색인 폴더를 씁니다. 한쪽에서 새 문서를 색인하면 다른 쪽은 다음 검색 때 색인을 다시 열고 재시도합니다(설계문서 9장 #16).

## 6. 데이터 출처와 이용 조건 (요약)

자세한 목록은 [`docs/sources.md`](docs/sources.md) (NF2007).

| 출처 | 쓰임 | 이용 조건 |
|---|---|---|
| 6개 CSP 공식 요금·상품 페이지 | 상품 메타 108건, 서버·스토리지 가격표, 공식 문서 수집 | 각 사 이용약관·robots.txt **확인 필요**(미결 #3). 수집기는 robots.txt를 확인한 뒤에만 가져옴 |
| KISA CSAP 인증서 발급현황 | 공공 부문 CSP 단위 판단(F2017) | 공개 조회 페이지. 사실만 요약해 인용 |
| 국가법령정보센터(고시·법률) | 공공 요건 웹 문서 후보 | 저작권법 제7조 보호 대상 아님(출처 표기) |
| 「클라우드컴퓨팅서비스 보안인증에 관한 고시」 PDF(국가법령정보센터) | PDF 출처(F2016), `data/pdf/` | 저작권법 제7조(보호 대상 아님), 출처 표기 |
| KISA 해설서·FAQ PDF | (미사용) | 공공누리 표시 **확인 필요** → 확인 전에는 등록하지 않음 |
| 한국어 위키백과 | 개념 문서 | CC BY-SA 4.0(2023-06 이후 편집분), 이전 편집분 CC BY-SA 3.0 — 출처·라이선스 표기 |
| 환율 | USD → 원 환산 | 1,334.03원/USD (YCharts, 2026-10-16 기준, 기본값) |

## 7. 심화 기능 요약

- **F2013 프론트엔드 직접 구현**: `api/main.py`(FastAPI)가 `/api/status · products · ask · recommend · explore`를 제공하고 `api/static/`의 HTML·CSS·JS가 화면을 그립니다. 요청·응답 형식은 `api/models.py`(pydantic)와 `/docs`에서 확인합니다. 오류는 `{"detail": "사용자용 문구"}`만 돌려줍니다.
- **F2015 RAG 전후 비교**: 요구사항 정의서 3.3의 Q1~Q5를 RAG 없이/있이 답하게 해 `docs/04_RAG_전후비교_실행결과.md`로 남기고, 사실 정확성·근거 제시·모름 인정으로 평가합니다(평가 칸은 사람이 채움).
- **F2016 여러 출처 결합**: 공식 웹 문서(HTML 본문 추출), PDF(쪽 단위 추출·청킹, 출처 "파일명 · n쪽" — 보안인증 고시 1건 등록), 위키백과(API 평문, 절 경계 우선 청킹, 단어 겹침 필터), 수집 결과 요약(줄 단위)을 함께 색인하고 근거마다 출처 종류 배지를 붙입니다. 실제 화면: `docs/evidence/screens/07b_public_pdf_evidence.png`.

## 8. 알려진 한계 (확인 필요)

- 상품 메타의 **공공 지원 여부는 108건 모두 '확인 필요'**입니다. 수집 자료가 CSP 단위 CSAP 인증까지만 확인했기 때문입니다. 공공 부문 판단은 CSP 단위 인증(유효기간·하등급 여부)으로 하고, 상품 단위는 '확인 필요'로 표시합니다.
- 폐쇄망 지원은 14건만 '지원'으로 확인됐습니다. private 부문 설계안의 서버·DB는 '확인 필요'로 표시됩니다.
- 2026-04-20 발표된 공공 클라우드 보안 검증 제도 변경(국정원 단일 검증, 2027년 하반기 시행)은 안내 문서로만 반영했습니다.
- GCP Cloud SQL Enterprise 2개 상품은 수집 자료에 MySQL 여부가 적혀 있지 않아 DB(MySQL) 후보에서 빠집니다.
- 선택 상품의 공식 문서는 AWS·GCP만 실제로 수집됩니다. NCP 요금 페이지·KT 상품 페이지는 robots.txt가 수집을 막아 가져오지 않고, NHN·SCP 페이지는 스크립트로 내용을 그려 본문이 거의 없습니다(`docs/sources.md` 4장). 이때는 상품 메타데이터로 답하고 화면에 안내합니다.
- 응답 시간은 GMS 응답 속도에 따라 달라집니다. 같은 질문 재질문이 3~4초인 측정과 24초인 측정이 모두 있었습니다(`docs/03_검증결과.md` T26).
- PDF 라이브러리 `pypdf`는 고정 스택 목록 밖의 추가 라이브러리입니다(PDF 출처를 쓰지 않으면 설치하지 않아도 동작). 사용 허용 여부는 확인이 필요합니다.

## 9. 제출물 구성

| 산출물 (명세 6장) | 파일 |
|---|---|
| 1) 요구사항 정의서 | `docs/01_요구사항_정의서.md` |
| 2) RAG 파이프라인 설계문서 | `docs/02_RAG_파이프라인_설계문서.md` |
| 3) 검증 결과(대조표·테스트 결과표·확인 화면·제출 전 점검) | `docs/03_검증결과.md`, `docs/evidence/` |
| (심화) RAG 전후 비교 | `docs/04_RAG_전후비교.md`, `docs/04_RAG_전후비교_실행결과.md` |
| 4) 구현 소스코드(수집·색인 스크립트, 심화 기능 포함) | `cspnav/`, `ui/`, `api/`, `scripts/`, `settings.json`, `requirements.txt` |
| 5) 셀프 체크리스트 · 상호 체크리스트 | `docs/05_셀프_체크리스트.xlsx`, `docs/06_상호_체크리스트.xlsx` |
| 6) README | 이 문서 |
| 출처와 이용 조건 | `docs/sources.md` |

제출 zip에는 `.env`(키), `.venv`, 색인 폴더(`data/chroma`), 수집 캐시(`data/cache`), 실험 폴더(`data/experiments`)를 넣지 않습니다. 받은 뒤 3장 순서(설치 → `.env` → `prepare_data.py` → `build_index.py`)로 다시 만들 수 있습니다. 1일차 원본 수집 자료는 zip의 `data/sources/`에 함께 넣습니다.
