# (테스트용 발췌) 수집 결과: CSP 상품 메타데이터 · 공공 PDF 목록

> 이 파일은 scripts/smoke_test.py 전용 발췌본이다. 1일차 수집 결과(data/sources/수집결과_상품메타_공공PDF.md)에서 AWS·NCP 일부 행만 옮겼다. 실제 적재에는 쓰지 않는다.
> 수집일(checked_at): 2026-10-21 · 수집 방법: 각 CSP 공식 요금 페이지·요금계산기를 브라우저로 직접 열어 확인

## 요약

- **제도 변경 주의**: 2026-04-20 정부가 공공 클라우드 보안 검증을 국정원 단일 검증으로 일원화하고 CSAP를 정리한다고 발표했습니다(2027년 하반기 본격 시행, 기존 인증서는 잔여 유효기간 동안 유효).

### CSP별 공통 정보

| CSP | 기준 리전 | 통화 | 무료 티어·크레딧 (계정 단위) |
|---|---|---|---|
| AWS | 서울(ap-northeast-2) | USD | 계정 단위: 신규 크레딧 최대 200 USD, 최대 6개월 무료 플랜 |
| NCP(네이버클라우드) | 한국(VPC) | KRW | 확인 필요 |

---

## ① CSP별 상품 메타데이터 (발췌)

### AWS

| 항목ID | 분류 | 상품명 | 사양 | 요금·과금 단위 | 월 환산(참고) | 리전 | 공공 | 폐쇄망 | 무료 티어 | 비고 | 출처 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AWS-CMP-03 | 컴퓨팅 | EC2 t3.large | 2vCPU / 8GiB, Linux | 0.104 USD/시간 | 75.92 USD | 서울(ap-northeast-2) | 하등급 | 확인 필요 | 계정 크레딧 | 버스트형 | [링크](https://aws.amazon.com/ko/ec2/pricing/on-demand/) |
| AWS-DB-01 | DB | RDS for MySQL db.t3.micro | 2vCPU / 1GiB, Single-AZ | 0.026 USD/시간 | 18.98 USD | 서울(ap-northeast-2) | 하등급 | 확인 필요 | 계정 크레딧 | 스토리지 별도 | [링크](https://aws.amazon.com/ko/rds/mysql/pricing/) |
| AWS-DB-02 | DB | RDS for MySQL db.t4g.medium | 2vCPU / 4GiB, Single-AZ | 0.102 USD/시간 | 74.46 USD | 서울(ap-northeast-2) | 하등급 | 확인 필요 | 계정 크레딧 | 스토리지 별도 | [링크](https://aws.amazon.com/ko/rds/mysql/pricing/) |
| AWS-DB-04 | DB | DynamoDB 온디맨드 | 쓰기/읽기 요청 단위 | 쓰기 0.68 USD/백만 WRU, 읽기 0.1355 USD/백만 RRU, 저장 0.27075 USD/GB-월 | - | 서울(ap-northeast-2) | 하등급 | 확인 필요 | 계정 크레딧 |  | [링크](https://aws.amazon.com/ko/dynamodb/pricing/on-demand/) |
| AWS-STG-01 | 스토리지 | S3 Standard | 객체 스토리지 | 0.025 USD/GB-월 | - | 서울(ap-northeast-2) | 하등급 | 확인 필요 | 계정 크레딧 | 처음 50TB 구간 | [링크](https://aws.amazon.com/ko/s3/pricing/) |
| AWS-NET-01 | 네트워크 | Application Load Balancer | L7 부하 분산 | 0.0225 USD/시간 | 16.42 USD | 서울(ap-northeast-2) | 하등급 | 확인 필요 | 계정 크레딧 | + 0.008 USD/LCU-시간 | [링크](https://aws.amazon.com/ko/elasticloadbalancing/pricing/) |
| AWS-NET-02 | 네트워크 | Site-to-Site VPN | IPsec VPN 연결 | 0.05 USD/연결-시간 | - | 서울(ap-northeast-2) | 하등급 | 지원(IPsec VPN) | 계정 크레딧 |  | [링크](https://aws.amazon.com/ko/vpn/pricing/) |
| AWS-NET-03 | 네트워크 | Direct Connect 1G 전용 포트 | KINX 가산 / LG U+ 평촌 | 0.3 USD/포트-시간 | - | 서울(ap-northeast-2) | 하등급 | 지원(전용회선) | 계정 크레딧 | 회선·상면 비용 별도 | [링크](https://aws.amazon.com/ko/directconnect/pricing/) |
| AWS-SEC-02 | 보안 | WAF | Web ACL | 5.00 USD/Web ACL-월 + 1.00 USD/규칙-월 + 0.60 USD/백만 요청 | - | 서울(ap-northeast-2) | 하등급 | 확인 필요 | 계정 크레딧 |  | [링크](https://aws.amazon.com/ko/waf/pricing/) |

### NCP(네이버클라우드)

| 항목ID | 분류 | 상품명 | 사양 | 요금·과금 단위 | 월 환산(참고) | 리전 | 공공 | 폐쇄망 | 무료 티어 | 비고 | 출처 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| NCP-CMP-01 | 컴퓨팅 | Server Standard-g2 2vCPU/8GB | 2vCPU / 8GB, 디스크 50GB | 119 원/시간 | 86,870 원 | 한국(VPC) | 별도(공공용) | 확인 필요 | 확인 필요 | 월 85,120원 | [링크](https://www.ncloud.com/charge/price/ko) |
| NCP-DB-01 | DB | Cloud DB for MySQL High CPU 2vCPU/4GB | 2vCPU / 4GB | 160 원/시간 | 116,800 원 | 한국(VPC) | 별도(공공용) | 확인 필요 | 확인 필요 | 데이터 스토리지 별도, HA 시 2대 | [링크](https://www.ncloud.com/charge/price/ko) |
| NCP-STG-01 | 스토리지 | Object Storage | 객체 스토리지 | 28 원/GB-월 | - | 한국(VPC) | 별도(공공용) | 확인 필요 | 확인 필요 | 1PB 이하 구간 | [링크](https://www.ncloud.com/charge/price/ko) |
| NCP-NET-03 | 네트워크 | Cloud Connect 1G 포트 | 전용 회선 연결 | 237,600원/월 + 45원/GB(한국) | - | 한국(VPC) | 별도(공공용) | 지원(전용회선) | 확인 필요 | Cross Connect·통신사 회선 비용 별도(문의) | [링크](https://www.ncloud.com/charge/price/ko) |
| NCP-NET-04 | 네트워크 | IPsec VPN (VPC) | IPsec VPN Gateway | 138 원/시간 | 100,740 원 | 한국(VPC) | 별도(공공용) | 지원(IPsec VPN) | 확인 필요 |  | [링크](https://www.ncloud.com/charge/price/ko) |

---

## ② 공공 요건 판단 자료 목록

### ②-1 CSP별 CSAP(클라우드 보안인증) IaaS 인증 현황

출처: [KISA ISMS-P 누리집 – CSAP 인증서 발급현황](https://isms-p.or.kr/sttus/vrtl/selectVrtlCrtfctList.do) (인증범위 'IaaS' 검색, 2026-10-21 확인)

| CSP | 인증번호 | 인증범위 | 유효기간 | 유지여부 |
|---|---|---|---|---|
| AWS | CSAP-2025-014호 | 아마존 웹 서비스(AWS) 서울 리전에서 제공하는 클라우드컴퓨팅서비스 (다그룹) (하등급 IaaS) | 2025-03-28 ~ 2030-03-27 | 유지 |
| NCP(네이버클라우드) | CSAP-2017-001호 | 네이버클라우드플랫폼 공공기관용(IaaS) | 2022-02-24 ~ 2027-02-23 | 유지 |

- AWS·GCP는 **하등급** IaaS만 인증 범위입니다.

### ②-2 공공 요건 PDF·원문 자료

| # | 자료명 | 발행처 | 판·시행일 | 형태 | URL | 저작권·이용 조건 | 용도 |
|---|---|---|---|---|---|---|---|
| P5 | 행정기관 및 공공기관의 클라우드컴퓨팅서비스 이용 기준 및 안전성 확보 등에 관한 고시 | 행정안전부(고시 제2025-79호) | 시행 2025-12-29 | 법령 원문 | [국가법령정보센터](https://www.law.go.kr/행정규칙/행정기관및공공기관의클라우드컴퓨팅서비스이용기준및안전성확보등에관한고시) | 저작권법 제7조 (보호 대상 아님) | 공공기관의 민간 클라우드 이용 기준(Q1, Q5) |

**참고(PDF 아님, 제도 변경 근거)**: [바이라인네트워크 2026-04-20 – 공공 클라우드 보안 검증](https://byline.network/2026/04/20-578/) — 공식 보도자료 원문은 확인 필요.

---

## ③ 로그인·회원가입이 필요해 수집하지 않은 정보

| CSP·기관 | 정보 | 막힌 이유 | 대안 |
|---|---|---|---|
| AWS·GCP | 무료 크레딧 실제 적용 범위 | 계정 생성·결제수단 등록 후 콘솔에서 확인 | 계정 단위 혜택으로만 기록 |
