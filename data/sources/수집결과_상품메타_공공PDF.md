# 수집 결과: CSP 상품 메타데이터 108건 · 공공 요건 PDF 목록

> 프로젝트: CSP Navigator (요구사항 정의서 v0.1 미결 사항 #1, #2)
> 수집일(checked_at): 2026-10-21 · 수집 방법: 각 CSP 공식 요금 페이지·요금계산기를 브라우저로 직접 열어 확인
> 표기: `확인 필요` = 공식 출처로 아직 확인하지 못한 값, `(계산)` = 공식 단가로 코드가 계산한 값

> **면책**: 요금, 인증 보유 현황, 리전 정보는 수시로 바뀔 수 있습니다. 이 문서는 수집일 기준 참고 자료이며, CSP의 공식 견적이나 보안·법률 전문가의 검토를 대신하지 않습니다.

## 요약

- 상품 메타데이터 **108건**(6개 CSP × 18건: 컴퓨팅 5, DB 4, 스토리지 3, 네트워크 4, 보안 2)을 모두 공식 페이지 값으로 채웠습니다. 단가를 추정해 넣은 행은 없습니다.
- 공공 지원 여부는 KISA의 CSAP 인증서 발급현황(IaaS)으로 6개 CSP를 모두 확인했습니다. 다만 국내 4사는 **공공기관용 별도 플랫폼**이 인증 범위입니다. 이 문서의 단가는 민간용 요금이므로, 상품별 공공 플랫폼 제공 여부는 따로 확인해야 합니다.
- **제도 변경 주의**: 2026-04-20 정부가 공공 클라우드 보안 검증을 국정원 단일 검증으로 일원화하고 CSAP를 정리한다고 발표했습니다(2027년 하반기 본격 시행, 기존 인증서는 잔여 유효기간 동안 유효). 부문 필터(F2017) 설계 시 반영이 필요합니다.
- **회원가입·로그인이 필요해 수집하지 않은 정보**는 ③에 정리했습니다. 대부분 무료 크레딧 신청, 콘솔 내 원화 SKU 단가, 협정가(영업 문의) 항목입니다.

### 열 설명

| 열 | 의미 |
|---|---|
| 요금·과금 단위 | 공식 페이지 표기 그대로(VAT 별도). USD는 AWS·GCP, 원은 국내 4사 |
| 월 환산(참고) | 시간 단가 × 730시간(계산). 스토리지·월정액 상품은 `-`. NCP 페이지의 30일(720시간) 월 요금과는 다를 수 있음 |
| 공공 | `하등급` = CSAP 하등급 IaaS 인증 보유 CSP(AWS·GCP) / `별도(공공용)` = 공공기관용 별도 플랫폼이 CSAP IaaS 인증 범위. 상품 단위 제공 여부는 `확인 필요` |
| 폐쇄망 | 페이지에서 전용회선·IPsec VPN·사설 엔드포인트로 확인된 상품만 `지원(…)`. 나머지는 `확인 필요`(VPC 사설 서브넷 + 전용회선 조합으로 구성 가능한지는 상품별 확인) |
| 무료 티어 | 상품 단위가 아니라 계정 단위 혜택이 대부분이라 CSP별 요약(아래 표)을 참고 |

### CSP별 공통 정보

| CSP | 기준 리전 | 통화 | 무료 티어·크레딧 (계정 단위) |
|---|---|---|---|
| AWS | 서울(ap-northeast-2) | USD | 계정 단위: 신규 크레딧 최대 200 USD, 최대 6개월 무료 플랜 |
| GCP | 서울(asia-northeast3) | USD | 계정 단위: 300 USD 크레딧/90일 (e2-micro 상시 무료는 미국 3개 리전만, 서울 해당 없음) |
| NCP(네이버클라우드) | 한국(VPC) | KRW | 확인 필요 |
| NHN Cloud | 한국(판교) — 확인 필요 | KRW | 확인 필요 |
| KT Cloud | Seoul M1 존(G1/G2) | KRW | 계정 단위: 가입 1개월 이내 50만원/90일 무료체험(사이트 배너) |
| SCP(삼성 클라우드 플랫폼) | 한국(오퍼링 Enterprises/Finance) | KRW | 계정 단위: 결제수단 등록 시 30만원 크레딧/3개월 |

---

## ① CSP별 상품 메타데이터 (108건)

### AWS

| 항목ID | 분류 | 상품명 | 사양 | 요금·과금 단위 | 월 환산(참고) | 리전 | 공공 | 폐쇄망 | 무료 티어 | 비고 | 출처 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AWS-CMP-01 | 컴퓨팅 | EC2 t3.micro | 2vCPU / 1GiB, Linux | 0.013 USD/시간 | 9.49 USD | 서울(ap-northeast-2) | 하등급 | 확인 필요 | 계정 크레딧 |  | [링크](https://aws.amazon.com/ko/ec2/pricing/on-demand/) |
| AWS-CMP-02 | 컴퓨팅 | EC2 t3.medium | 2vCPU / 4GiB, Linux | 0.052 USD/시간 | 37.96 USD | 서울(ap-northeast-2) | 하등급 | 확인 필요 | 계정 크레딧 |  | [링크](https://aws.amazon.com/ko/ec2/pricing/on-demand/) |
| AWS-CMP-03 | 컴퓨팅 | EC2 t3.large | 2vCPU / 8GiB, Linux | 0.104 USD/시간 | 75.92 USD | 서울(ap-northeast-2) | 하등급 | 확인 필요 | 계정 크레딧 | 버스트형 | [링크](https://aws.amazon.com/ko/ec2/pricing/on-demand/) |
| AWS-CMP-04 | 컴퓨팅 | EC2 m6i.large | 2vCPU / 8GiB, Linux | 0.118 USD/시간 | 86.14 USD | 서울(ap-northeast-2) | 하등급 | 확인 필요 | 계정 크레딧 | 범용 고정 성능 | [링크](https://aws.amazon.com/ko/ec2/pricing/on-demand/) |
| AWS-CMP-05 | 컴퓨팅 | EC2 c6i.large | 2vCPU / 4GiB, Linux | 0.096 USD/시간 | 70.08 USD | 서울(ap-northeast-2) | 하등급 | 확인 필요 | 계정 크레딧 | 컴퓨팅 최적화 | [링크](https://aws.amazon.com/ko/ec2/pricing/on-demand/) |
| AWS-DB-01 | DB | RDS for MySQL db.t3.micro | 2vCPU / 1GiB, Single-AZ | 0.026 USD/시간 | 18.98 USD | 서울(ap-northeast-2) | 하등급 | 확인 필요 | 계정 크레딧 | 스토리지 별도 | [링크](https://aws.amazon.com/ko/rds/mysql/pricing/) |
| AWS-DB-02 | DB | RDS for MySQL db.t4g.medium | 2vCPU / 4GiB, Single-AZ | 0.102 USD/시간 | 74.46 USD | 서울(ap-northeast-2) | 하등급 | 확인 필요 | 계정 크레딧 | 스토리지 별도 | [링크](https://aws.amazon.com/ko/rds/mysql/pricing/) |
| AWS-DB-03 | DB | RDS for PostgreSQL db.m6i.large | 2vCPU / 8GiB, Single-AZ | 0.247 USD/시간 | 180.31 USD | 서울(ap-northeast-2) | 하등급 | 확인 필요 | 계정 크레딧 | 스토리지 별도 | [링크](https://aws.amazon.com/ko/rds/postgresql/pricing/) |
| AWS-DB-04 | DB | DynamoDB 온디맨드 | 쓰기/읽기 요청 단위 | 쓰기 0.68 USD/백만 WRU, 읽기 0.1355 USD/백만 RRU, 저장 0.27075 USD/GB-월 | - | 서울(ap-northeast-2) | 하등급 | 확인 필요 | 계정 크레딧 |  | [링크](https://aws.amazon.com/ko/dynamodb/pricing/on-demand/) |
| AWS-STG-01 | 스토리지 | S3 Standard | 객체 스토리지 | 0.025 USD/GB-월 | - | 서울(ap-northeast-2) | 하등급 | 확인 필요 | 계정 크레딧 | 처음 50TB 구간 | [링크](https://aws.amazon.com/ko/s3/pricing/) |
| AWS-STG-02 | 스토리지 | EBS gp3 | 블록 스토리지(SSD) | 0.0912 USD/GB-월 | - | 서울(ap-northeast-2) | 하등급 | 확인 필요 | 계정 크레딧 | IOPS·처리량 추가 과금 별도 | [링크](https://aws.amazon.com/ko/ebs/pricing/) |
| AWS-STG-03 | 스토리지 | EFS Standard | 파일 스토리지 | 0.33 USD/GB-월 | - | 서울(ap-northeast-2) | 하등급 | 확인 필요 | 계정 크레딧 |  | [링크](https://aws.amazon.com/ko/efs/pricing/) |
| AWS-NET-01 | 네트워크 | Application Load Balancer | L7 부하 분산 | 0.0225 USD/시간 | 16.42 USD | 서울(ap-northeast-2) | 하등급 | 확인 필요 | 계정 크레딧 | + 0.008 USD/LCU-시간 | [링크](https://aws.amazon.com/ko/elasticloadbalancing/pricing/) |
| AWS-NET-02 | 네트워크 | Site-to-Site VPN | IPsec VPN 연결 | 0.05 USD/연결-시간 | - | 서울(ap-northeast-2) | 하등급 | 지원(IPsec VPN) | 계정 크레딧 |  | [링크](https://aws.amazon.com/ko/vpn/pricing/) |
| AWS-NET-03 | 네트워크 | Direct Connect 1G 전용 포트 | KINX 가산 / LG U+ 평촌 | 0.3 USD/포트-시간 | - | 서울(ap-northeast-2) | 하등급 | 지원(전용회선) | 계정 크레딧 | 회선·상면 비용 별도 | [링크](https://aws.amazon.com/ko/directconnect/pricing/) |
| AWS-NET-04 | 네트워크 | VPC 인터페이스 엔드포인트(PrivateLink) | 사설 연결 | 0.013 USD/시간 | 9.49 USD | 서울(ap-northeast-2) | 하등급 | 지원(사설 엔드포인트) | 계정 크레딧 | + 0.01 USD/GB(1PB 이하) | [링크](https://aws.amazon.com/ko/privatelink/pricing/) |
| AWS-SEC-01 | 보안 | KMS 고객 관리형 키 | 대칭 키 | 1.00 USD/키-월 | - | 서울(ap-northeast-2) | 하등급 | 확인 필요 | 계정 크레딧 | API 요청 별도 | [링크](https://aws.amazon.com/ko/kms/pricing/) |
| AWS-SEC-02 | 보안 | WAF | Web ACL | 5.00 USD/Web ACL-월 + 1.00 USD/규칙-월 + 0.60 USD/백만 요청 | - | 서울(ap-northeast-2) | 하등급 | 확인 필요 | 계정 크레딧 |  | [링크](https://aws.amazon.com/ko/waf/pricing/) |

### GCP

| 항목ID | 분류 | 상품명 | 사양 | 요금·과금 단위 | 월 환산(참고) | 리전 | 공공 | 폐쇄망 | 무료 티어 | 비고 | 출처 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| GCP-CMP-01 | 컴퓨팅 | Compute Engine e2-micro | 2vCPU(공유) / 1GiB | 0.010745715 USD/시간 | 7.84 USD | 서울(asia-northeast3) | 하등급 | 확인 필요 | 계정 크레딧 |  | [링크](https://cloud.google.com/products/compute/pricing/general-purpose) |
| GCP-CMP-02 | 컴퓨팅 | Compute Engine e2-medium | 2vCPU(공유) / 4GiB | 0.04298286 USD/시간 | 31.38 USD | 서울(asia-northeast3) | 하등급 | 확인 필요 | 계정 크레딧 |  | [링크](https://cloud.google.com/products/compute/pricing/general-purpose) |
| GCP-CMP-03 | 컴퓨팅 | Compute Engine e2-standard-2 | 2vCPU / 8GiB | 0.08596572 USD/시간 | 62.75 USD | 서울(asia-northeast3) | 하등급 | 확인 필요 | 계정 크레딧 |  | [링크](https://cloud.google.com/products/compute/pricing/general-purpose) |
| GCP-CMP-04 | 컴퓨팅 | Compute Engine n2-standard-2 | 2vCPU / 8GiB | 0.124718 USD/시간 | 91.04 USD | 서울(asia-northeast3) | 하등급 | 확인 필요 | 계정 크레딧 |  | [링크](https://cloud.google.com/products/compute/pricing/general-purpose) |
| GCP-CMP-05 | 컴퓨팅 | Compute Engine n4-standard-2 | 2vCPU / 8GiB | 0.116476944 USD/시간 | 85.03 USD | 서울(asia-northeast3) | 하등급 | 확인 필요 | 계정 크레딧 |  | [링크](https://cloud.google.com/products/compute/pricing/general-purpose) |
| GCP-DB-01 | DB | Cloud SQL db-f1-micro | 공유 vCPU / 0.6GiB | 0.0137 USD/시간 | 10 USD | 서울(asia-northeast3) | 하등급 | 확인 필요 | 계정 크레딧 | MySQL·PostgreSQL 공통 표, 스토리지 별도 | [링크](https://cloud.google.com/sql/pricing) |
| GCP-DB-02 | DB | Cloud SQL db-g1-small | 공유 vCPU / 1.7GiB | 0.0455 USD/시간 | 33.22 USD | 서울(asia-northeast3) | 하등급 | 확인 필요 | 계정 크레딧 | MySQL·PostgreSQL 공통 표 | [링크](https://cloud.google.com/sql/pricing) |
| GCP-DB-03 | DB | Cloud SQL Enterprise 2vCPU/8GiB | vCPU 0.0537 + 메모리 0.0091 USD/GiB-시간 | 0.1802 USD/시간 | 131.55 USD | 서울(asia-northeast3) | 하등급 | 확인 필요 | 계정 크레딧 | 2×0.0537+8×0.0091로 계산(코드 계산값) | [링크](https://cloud.google.com/sql/pricing) |
| GCP-DB-04 | DB | Cloud SQL Enterprise 2vCPU/8GiB HA | HA vCPU 0.1074 + HA 메모리 0.0182 | 0.3604 USD/시간 | 263.09 USD | 서울(asia-northeast3) | 하등급 | 확인 필요 | 계정 크레딧 | 2×0.1074+8×0.0182로 계산(코드 계산값) | [링크](https://cloud.google.com/sql/pricing) |
| GCP-STG-01 | 스토리지 | Cloud Storage Standard | 객체 스토리지(리전) | 0.000031507 USD/GiB-시간 | - | 서울(asia-northeast3) | 하등급 | 확인 필요 | 계정 크레딧 | 730시간 기준 약 0.023 USD/GiB-월 | [링크](https://cloud.google.com/storage/pricing) |
| GCP-STG-02 | 스토리지 | Cloud Storage Coldline | 객체 스토리지(리전) | 0.000008219 USD/GiB-시간 | - | 서울(asia-northeast3) | 하등급 | 확인 필요 | 계정 크레딧 | 730시간 기준 약 0.006 USD/GiB-월, 조회 요금 별도 | [링크](https://cloud.google.com/storage/pricing) |
| GCP-STG-03 | 스토리지 | Persistent Disk Balanced | 블록 스토리지 | 0.000178082 USD/GiB-시간 | - | 서울(asia-northeast3) | 하등급 | 확인 필요 | 계정 크레딧 | 730시간 기준 약 0.13 USD/GiB-월 | [링크](https://cloud.google.com/compute/disks-image-pricing) |
| GCP-NET-01 | 네트워크 | Cloud VPN(HA VPN) 터널 | IPsec VPN | 0.075 USD/터널-시간 | - | 서울(asia-northeast3) | 하등급 | 지원(IPsec VPN) | 계정 크레딧 | 99.99% 가용성은 터널 2개 필요 | [링크](https://cloud.google.com/vpn/pricing) |
| GCP-NET-02 | 네트워크 | Dedicated Interconnect 10G | 전용 회선 연결 | 2.328 USD/시간 | 1,699.44 USD | 서울(asia-northeast3) | 하등급 | 지원(전용회선) | 계정 크레딧 | + VLAN 연결 0.10 USD/시간, 데이터 전송 별도 | [링크](https://cloud.google.com/network-connectivity/interconnect/pricing) |
| GCP-NET-03 | 네트워크 | Partner Interconnect 1Gbps VLAN | 파트너 회선 연결 | 0.2778 USD/시간 | 202.79 USD | 서울(asia-northeast3) | 하등급 | 지원(전용회선) | 계정 크레딧 | 아시아 전송 0.042 USD/GiB | [링크](https://cloud.google.com/network-connectivity/interconnect/pricing) |
| GCP-NET-04 | 네트워크 | 내부 Application Load Balancer | L7 부하 분산 | 0.025 USD/프록시-시간 | - | 서울(asia-northeast3) | 하등급 | 확인 필요 | 계정 크레딧 | + 0.008 USD/GiB 처리 | [링크](https://cloud.google.com/load-balancing/pricing) |
| GCP-SEC-01 | 보안 | Cloud KMS 소프트웨어 키 | 대칭/비대칭 키 버전 | 0.000082192 USD/키버전-시간 | - | 서울(asia-northeast3) | 하등급 | 확인 필요 | 계정 크레딧 | 730시간 기준 약 0.06 USD/월, 연산 요금 별도 | [링크](https://cloud.google.com/kms/pricing) |
| GCP-SEC-02 | 보안 | Cloud Armor Standard | WAF·DDoS 정책 | 0.006849315 USD/정책-시간 | - | 서울(asia-northeast3) | 하등급 | 확인 필요 | 계정 크레딧 | + 규칙 0.001369863 USD/시간, 0.75 USD/백만 요청(전역) | [링크](https://cloud.google.com/armor/pricing) |

### NCP(네이버클라우드)

| 항목ID | 분류 | 상품명 | 사양 | 요금·과금 단위 | 월 환산(참고) | 리전 | 공공 | 폐쇄망 | 무료 티어 | 비고 | 출처 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| NCP-CMP-01 | 컴퓨팅 | Server Standard-g2 2vCPU/8GB | 2vCPU / 8GB, 디스크 50GB | 119 원/시간 | 86,870 원 | 한국(VPC) | 별도(공공용) | 확인 필요 | 확인 필요 | 월 85,120원 | [링크](https://www.ncloud.com/charge/price/ko) |
| NCP-CMP-02 | 컴퓨팅 | Server High CPU-g2 2vCPU/4GB | 2vCPU / 4GB, 디스크 50GB | 96 원/시간 | 70,080 원 | 한국(VPC) | 별도(공공용) | 확인 필요 | 확인 필요 | 월 69,120원 | [링크](https://www.ncloud.com/charge/price/ko) |
| NCP-CMP-03 | 컴퓨팅 | Server High Memory-g2 2vCPU/16GB | 2vCPU / 16GB, 디스크 50GB | 163 원/시간 | 118,990 원 | 한국(VPC) | 별도(공공용) | 확인 필요 | 확인 필요 | 월 117,120원 | [링크](https://www.ncloud.com/charge/price/ko) |
| NCP-CMP-04 | 컴퓨팅 | Server Standard-g2 4vCPU/16GB | 4vCPU / 16GB, 디스크 50GB | 241 원/시간 | 175,930 원 | 한국(VPC) | 별도(공공용) | 확인 필요 | 확인 필요 | 월 173,120원 | [링크](https://www.ncloud.com/charge/price/ko) |
| NCP-CMP-05 | 컴퓨팅 | Server Micro-g1 (Classic) | 1vCPU / 1GB, 디스크 50GB | 19 원/시간 | 13,870 원 | 한국(Classic 1세대) | 별도(공공용) | 확인 필요 | 1년 무료(조건부) | 월 13,000원. 신규 가입 후 1년 무료(계정당 1대, 한국 거주자) | [링크](https://www.ncloud.com/charge/price/ko) |
| NCP-DB-01 | DB | Cloud DB for MySQL High CPU 2vCPU/4GB | 2vCPU / 4GB | 160 원/시간 | 116,800 원 | 한국(VPC) | 별도(공공용) | 확인 필요 | 확인 필요 | 데이터 스토리지 별도, HA 시 2대 | [링크](https://www.ncloud.com/charge/price/ko) |
| NCP-DB-02 | DB | Cloud DB for MySQL Standard 2vCPU/8GB | 2vCPU / 8GB | 248 원/시간 | 181,040 원 | 한국(VPC) | 별도(공공용) | 확인 필요 | 확인 필요 | 데이터 스토리지 별도 | [링크](https://www.ncloud.com/charge/price/ko) |
| NCP-DB-03 | DB | Cloud DB for PostgreSQL Standard 2vCPU/8GB | 2vCPU / 8GB | 250 원/시간 | 182,500 원 | 한국(VPC) | 별도(공공용) | 확인 필요 | 확인 필요 | 데이터 스토리지 별도 | [링크](https://www.ncloud.com/charge/price/ko) |
| NCP-DB-04 | DB | Cloud DB for Redis 1.5GB | Cluster/Simple 1.5GB | 79 원/시간 | 57,670 원 | 한국(VPC) | 별도(공공용) | 확인 필요 | 확인 필요 | VPC 최소 3 Shard | [링크](https://www.ncloud.com/charge/price/ko) |
| NCP-STG-01 | 스토리지 | Object Storage | 객체 스토리지 | 28 원/GB-월 | - | 한국(VPC) | 별도(공공용) | 확인 필요 | 확인 필요 | 1PB 이하 구간 | [링크](https://www.ncloud.com/charge/price/ko) |
| NCP-STG-02 | 스토리지 | Block Storage SSD | 블록 스토리지 | 1.6 원/10GB-시간 | - | 한국(VPC) | 별도(공공용) | 확인 필요 | 확인 필요 | 30일 1,152원/10GB | [링크](https://www.ncloud.com/charge/price/ko) |
| NCP-STG-03 | 스토리지 | NAS 500GB | 파일 스토리지 | 50 원/시간 | 36,500 원 | 한국(VPC) | 별도(공공용) | 확인 필요 | 확인 필요 | 30일 36,000원, 100GB 추가당 10원/시간 | [링크](https://www.ncloud.com/charge/price/ko) |
| NCP-NET-01 | 네트워크 | Load Balancer (Application, Small) | L7 부하 분산 | 26 원/시간 | 18,980 원 | 한국(VPC) | 별도(공공용) | 확인 필요 | 확인 필요 | 30일 18,720원, 처리 데이터 9원/GB | [링크](https://www.ncloud.com/charge/price/ko) |
| NCP-NET-02 | 네트워크 | NAT Gateway | NAT | 56 원/시간 | 40,880 원 | 한국(VPC) | 별도(공공용) | 확인 필요 | 확인 필요 | + 60원/GB 처리 | [링크](https://www.ncloud.com/charge/price/ko) |
| NCP-NET-03 | 네트워크 | Cloud Connect 1G 포트 | 전용 회선 연결 | 237,600원/월 + 45원/GB(한국) | - | 한국(VPC) | 별도(공공용) | 지원(전용회선) | 확인 필요 | Cross Connect·통신사 회선 비용 별도(문의) | [링크](https://www.ncloud.com/charge/price/ko) |
| NCP-NET-04 | 네트워크 | IPsec VPN (VPC) | IPsec VPN Gateway | 138 원/시간 | 100,740 원 | 한국(VPC) | 별도(공공용) | 지원(IPsec VPN) | 확인 필요 |  | [링크](https://www.ncloud.com/charge/price/ko) |
| NCP-SEC-01 | 보안 | Key Management Service | 키 관리 | 1,000원/키-월 | - | 한국(VPC) | 별도(공공용) | 확인 필요 | 확인 필요 | 월 2만 건 초과 시 1만 건당 30원 | [링크](https://www.ncloud.com/charge/price/ko) |
| NCP-SEC-02 | 보안 | Secure Zone Firewall Standard | Secure Zone 방화벽 | 400,000원/월 | - | 한국(VPC) | 별도(공공용) | 확인 필요 | 확인 필요 | 30Mbps 초과 트래픽 추가 과금 | [링크](https://www.ncloud.com/charge/price/ko) |

### NHN Cloud

| 항목ID | 분류 | 상품명 | 사양 | 요금·과금 단위 | 월 환산(참고) | 리전 | 공공 | 폐쇄망 | 무료 티어 | 비고 | 출처 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| NHN-CMP-01 | 컴퓨팅 | Instance t2.c1m1 | 1vCPU / 1GB | 24 원/시간 | 17,520 원 | 한국(판교) — 확인 필요 | 별도(공공용) | 확인 필요 | 확인 필요 | 스토리지·네트워크 별도 | [링크](https://www.nhncloud.com/kr/pricing?c=Compute&s=Instance) |
| NHN-CMP-02 | 컴퓨팅 | Instance m2.c2m4 | 2vCPU / 4GB | 93 원/시간 | 67,890 원 | 한국(판교) — 확인 필요 | 별도(공공용) | 확인 필요 | 확인 필요 |  | [링크](https://www.nhncloud.com/kr/pricing?c=Compute&s=Instance) |
| NHN-CMP-03 | 컴퓨팅 | Instance m2.c4m8 | 4vCPU / 8GB | 196 원/시간 | 143,080 원 | 한국(판교) — 확인 필요 | 별도(공공용) | 확인 필요 | 확인 필요 |  | [링크](https://www.nhncloud.com/kr/pricing?c=Compute&s=Instance) |
| NHN-CMP-04 | 컴퓨팅 | Instance c2.c2m2 | 2vCPU / 2GB | 57 원/시간 | 41,610 원 | 한국(판교) — 확인 필요 | 별도(공공용) | 확인 필요 | 확인 필요 | Compute Optimized | [링크](https://www.nhncloud.com/kr/pricing?c=Compute&s=Instance) |
| NHN-CMP-05 | 컴퓨팅 | Instance r2.c2m8 | 2vCPU / 8GB | 128 원/시간 | 93,440 원 | 한국(판교) — 확인 필요 | 별도(공공용) | 확인 필요 | 확인 필요 | Memory Optimized | [링크](https://www.nhncloud.com/kr/pricing?c=Compute&s=Instance) |
| NHN-DB-01 | DB | RDS for MySQL m2.c2m4 | 2vCPU / 4GB | 149 원/시간 | 108,770 원 | 한국(판교) — 확인 필요 | 별도(공공용) | 확인 필요 | 확인 필요 | HA 시 동일 인스턴스 추가 과금 | [링크](https://www.nhncloud.com/kr/pricing?c=Database) |
| NHN-DB-02 | DB | RDS for MySQL r2.c2m8 | 2vCPU / 8GB | 231 원/시간 | 168,630 원 | 한국(판교) — 확인 필요 | 별도(공공용) | 확인 필요 | 확인 필요 |  | [링크](https://www.nhncloud.com/kr/pricing?c=Database) |
| NHN-DB-03 | DB | RDS for PostgreSQL m2.c2m4 | 2vCPU / 4GB | 149 원/시간 | 108,770 원 | 한국(판교) — 확인 필요 | 별도(공공용) | 확인 필요 | 확인 필요 |  | [링크](https://www.nhncloud.com/kr/pricing?c=Database) |
| NHN-DB-04 | DB | EasyCache m2.c1m2 | 1vCPU / 2GB | 54 원/시간 | 39,420 원 | 한국(판교) — 확인 필요 | 별도(공공용) | 확인 필요 | 확인 필요 |  | [링크](https://www.nhncloud.com/kr/pricing?c=Database) |
| NHN-STG-01 | 스토리지 | Block Storage SSD | 블록 스토리지 | 1.6 원/10GB-시간 | - | 한국(판교) — 확인 필요 | 별도(공공용) | 확인 필요 | 확인 필요 | HDD 1.4원 | [링크](https://www.nhncloud.com/kr/pricing?c=Storage) |
| NHN-STG-02 | 스토리지 | Object Storage Standard | 객체 스토리지 | 0.4 원/10GB-시간 | - | 한국(판교) — 확인 필요 | 별도(공공용) | 확인 필요 | 확인 필요 | Economy 0.2원 | [링크](https://www.nhncloud.com/kr/pricing?c=Storage) |
| NHN-STG-03 | 스토리지 | NAS | 파일 스토리지(최소 300GB) | 8.5 원/100GB-시간 | - | 한국(판교) — 확인 필요 | 별도(공공용) | 확인 필요 | 확인 필요 |  | [링크](https://www.nhncloud.com/kr/pricing?c=Storage) |
| NHN-NET-01 | 네트워크 | Load Balancer (일반) | 부하 분산 | 20 원/시간 | 14,600 원 | 한국(판교) — 확인 필요 | 별도(공공용) | 확인 필요 | 확인 필요 | 전용 LB 14,000원/일 | [링크](https://www.nhncloud.com/kr/pricing?c=Network) |
| NHN-NET-02 | 네트워크 | NAT Gateway | NAT | 50 원/시간 | 36,500 원 | 한국(판교) — 확인 필요 | 별도(공공용) | 확인 필요 | 확인 필요 |  | [링크](https://www.nhncloud.com/kr/pricing?c=Network) |
| NHN-NET-03 | 네트워크 | VPN Gateway (Site-to-Site) 20Mbps | IPsec VPN | 4,000원/일 | - | 한국(판교) — 확인 필요 | 별도(공공용) | 지원(IPsec VPN) | 확인 필요 | 50Mbps 7,400원/일, 1Gbps 26,000원/일 | [링크](https://www.nhncloud.com/kr/pricing?c=Network) |
| NHN-NET-04 | 네트워크 | Direct Connect 1G 포트 | 전용 회선 연결 | 234,000원/월 | - | 한국(판교) — 확인 필요 | 별도(공공용) | 지원(전용회선) | 확인 필요 | 네트워크 트래픽 한시 무료(페이지 안내) | [링크](https://www.nhncloud.com/kr/pricing?c=Network) |
| NHN-SEC-01 | 보안 | Secure Key Manager | 키 관리 | 1,000원/키-월 | - | 한국(판교) — 확인 필요 | 별도(공공용) | 확인 필요 | 확인 필요 | 2만 호출 초과 시 호출당 0.003원 | [링크](https://www.nhncloud.com/kr/pricing?c=Security) |
| NHN-SEC-02 | 보안 | Network Firewall | 방화벽 인스턴스 | 270 원/시간 | 197,100 원 | 한국(판교) — 확인 필요 | 별도(공공용) | 확인 필요 | 확인 필요 | 20GB 초과 인입 트래픽 70원/GB부터 | [링크](https://www.nhncloud.com/kr/pricing?c=Security) |

### KT Cloud

| 항목ID | 분류 | 상품명 | 사양 | 요금·과금 단위 | 월 환산(참고) | 리전 | 공공 | 폐쇄망 | 무료 티어 | 비고 | 출처 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| KT-CMP-01 | 컴퓨팅 | Server 1vCore 1GB (G1/G2) | 1vCore / 1GB, Linux | 22,500원/월 | - | Seoul M1 존(G1/G2) | 별도(공공용) | 확인 필요 | 계정 무료체험 | 요금계산기 데이터 | [링크](https://cloud.kt.com/calculator/) |
| KT-CMP-02 | 컴퓨팅 | Server 2vCore 4GB (G1/G2) | 2vCore / 4GB, Linux | 79,500원/월 | - | Seoul M1 존(G1/G2) | 별도(공공용) | 확인 필요 | 계정 무료체험 | 요금계산기 데이터 | [링크](https://cloud.kt.com/calculator/) |
| KT-CMP-03 | 컴퓨팅 | Server 2vCore 8GB (G1/G2) | 2vCore / 8GB, Linux | 107,850원/월 | - | Seoul M1 존(G1/G2) | 별도(공공용) | 확인 필요 | 계정 무료체험 | 요금계산기 데이터 | [링크](https://cloud.kt.com/calculator/) |
| KT-CMP-04 | 컴퓨팅 | Server 4vCore 8GB (G1/G2) | 4vCore / 8GB, Linux | 163,500원/월 | - | Seoul M1 존(G1/G2) | 별도(공공용) | 확인 필요 | 계정 무료체험 | 요금계산기 데이터 | [링크](https://cloud.kt.com/calculator/) |
| KT-CMP-05 | 컴퓨팅 | Server CPU-AMD 2vCore 4GB (D1) | 2vCore / 4GB, Linux | 61,840원/월 | - | DX-M1 존(D1) | 별도(공공용) | 확인 필요 | 계정 무료체험 | 3세대(D1) 플랫폼 | [링크](https://cloud.kt.com/calculator/) |
| KT-DB-01 | DB | DBaaS for MySQL/MariaDB 1vCore 1GB | 1vCore / 1GB | 31,000원/월 | - | Seoul M1 존(G1/G2) | 별도(공공용) | 확인 필요 | 계정 무료체험 | 데이터 스토리지 별도 | [링크](https://cloud.kt.com/calculator/) |
| KT-DB-02 | DB | DBaaS for MySQL/MariaDB 2vCore 4GB | 2vCore / 4GB | 93,000원/월 | - | Seoul M1 존(G1/G2) | 별도(공공용) | 확인 필요 | 계정 무료체험 |  | [링크](https://cloud.kt.com/calculator/) |
| KT-DB-03 | DB | DBaaS for MySQL/MariaDB 2vCore 8GB | 2vCore / 8GB | 151,350원/월 | - | Seoul M1 존(G1/G2) | 별도(공공용) | 확인 필요 | 계정 무료체험 |  | [링크](https://cloud.kt.com/calculator/) |
| KT-DB-04 | DB | Tibero Standard Edition | 라이선스 | 50,000원/vCore-월 | - | Seoul M1 존(G1/G2) | 별도(공공용) | 확인 필요 | 계정 무료체험 | 서버 요금 별도 | [링크](https://cloud.kt.com/calculator/) |
| KT-STG-01 | 스토리지 | Block Storage HDD | 블록 스토리지 | 70 원/GB-월 | - | Seoul M1 존(G1/G2) | 별도(공공용) | 확인 필요 | 계정 무료체험 | SSD-Provisioned 100원/GB + 35원/IOPS | [링크](https://cloud.kt.com/calculator/) |
| KT-STG-02 | 스토리지 | Object Storage Standard | 객체 스토리지 | 30 원/GB-월 | - | Seoul M1 존(G1/G2) | 별도(공공용) | 확인 필요 | 계정 무료체험 | 10TB까지 구간 | [링크](https://cloud.kt.com/calculator/) |
| KT-STG-03 | 스토리지 | NAS HDD | 파일 스토리지 | 70 원/GB-월 | - | Seoul M1 존(G1/G2) | 별도(공공용) | 확인 필요 | 계정 무료체험 | SSD NAS 210원(M2 존) | [링크](https://cloud.kt.com/calculator/) |
| KT-NET-01 | 네트워크 | Load Balancer (종량제) | 부하 분산 | 42 원/시간 | 30,660 원 | Seoul M1 존(G1/G2) | 별도(공공용) | 확인 필요 | 계정 무료체험 | + 20원/GB | [링크](https://cloud.kt.com/calculator/) |
| KT-NET-02 | 네트워크 | Connect Hub 1Gbps (Shared) | 전용 회선·VPN 연동 허브 | 140,000원/월 | - | Seoul M1 존(G1/G2) | 별도(공공용) | 지원(전용회선) | 계정 무료체험 |  | [링크](https://cloud.kt.com/product/productDetail?prodId=P000000029) |
| KT-NET-03 | 네트워크 | Shared VPN (IPsec) | IPsec VPN | 10Mbps당 75,000원/월(최대 50Mbps) | - | Seoul M1 존(G1/G2) | 별도(공공용) | 지원(IPsec VPN) | 계정 무료체험 | 전용 VPN은 협정가 | [링크](https://cloud.kt.com/product/productDetail?prodId=P000000032) |
| KT-NET-04 | 네트워크 | 공인 IP | Public IP | 5,000원/개-월 | - | Seoul M1 존(G1/G2) | 별도(공공용) | 확인 필요 | 계정 무료체험 | 아웃바운드 0~10TB 90원/GB | [링크](https://cloud.kt.com/calculator/) |
| KT-SEC-01 | 보안 | WAF Standard | 웹 방화벽 350Mbps | 300,000원/월 | - | Seoul M1 존(G1/G2) | 별도(공공용) | 확인 필요 | 계정 무료체험 |  | [링크](https://cloud.kt.com/calculator/) |
| KT-SEC-02 | 보안 | WAF Pro 2vCore | 웹 방화벽 100Mbps | 580,000원/월 | - | Seoul M1 존(G1/G2) | 별도(공공용) | 확인 필요 | 계정 무료체험 |  | [링크](https://cloud.kt.com/calculator/) |

### SCP(삼성 클라우드 플랫폼)

| 항목ID | 분류 | 상품명 | 사양 | 요금·과금 단위 | 월 환산(참고) | 리전 | 공공 | 폐쇄망 | 무료 티어 | 비고 | 출처 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SCP-CMP-01 | 컴퓨팅 | Virtual Server s1v2m4 (1세대) | 2vCore / 4GB, 오픈소스 OS | 118 원/시간 | 86,140 원 | 한국(오퍼링 Enterprises/Finance) | 별도(공공용) | 확인 필요 | 계정 크레딧 |  | [링크](https://cloud.samsungsds.com/serviceportal/services/compute/virtualServer.html) |
| SCP-CMP-02 | 컴퓨팅 | Virtual Server s2v1m2 (2세대) | 1vCore / 2GB, 오픈소스 OS | 43 원/시간 | 31,390 원 | 한국(오퍼링 Enterprises/Finance) | 별도(공공용) | 확인 필요 | 계정 크레딧 |  | [링크](https://cloud.samsungsds.com/serviceportal/services/compute/virtualServer.html) |
| SCP-CMP-03 | 컴퓨팅 | Virtual Server s2v2m4 (2세대) | 2vCore / 4GB, 오픈소스 OS | 103 원/시간 | 75,190 원 | 한국(오퍼링 Enterprises/Finance) | 별도(공공용) | 확인 필요 | 계정 크레딧 |  | [링크](https://cloud.samsungsds.com/serviceportal/services/compute/virtualServer.html) |
| SCP-CMP-04 | 컴퓨팅 | Virtual Server s2v2m8 (2세대) | 2vCore / 8GB, 오픈소스 OS | 109 원/시간 | 79,570 원 | 한국(오퍼링 Enterprises/Finance) | 별도(공공용) | 확인 필요 | 계정 크레딧 |  | [링크](https://cloud.samsungsds.com/serviceportal/services/compute/virtualServer.html) |
| SCP-CMP-05 | 컴퓨팅 | Virtual Server s2v4m16 (2세대) | 4vCore / 16GB, 오픈소스 OS | 234 원/시간 | 170,820 원 | 한국(오퍼링 Enterprises/Finance) | 별도(공공용) | 확인 필요 | 계정 크레딧 |  | [링크](https://cloud.samsungsds.com/serviceportal/services/compute/virtualServer.html) |
| SCP-DB-01 | DB | MySQL(DBaaS) db1v2m4 | 2vCore / 4GB | 243 원/시간 | 177,390 원 | 한국(오퍼링 Enterprises/Finance) | 별도(공공용) | 확인 필요 | 계정 크레딧 | 백업은 Object Storage 요금 | [링크](https://cloud.samsungsds.com/serviceportal/services/database/Mysql.html) |
| SCP-DB-02 | DB | MySQL(DBaaS) db1v2m8 | 2vCore / 8GB | 254 원/시간 | 185,420 원 | 한국(오퍼링 Enterprises/Finance) | 별도(공공용) | 확인 필요 | 계정 크레딧 |  | [링크](https://cloud.samsungsds.com/serviceportal/services/database/Mysql.html) |
| SCP-DB-03 | DB | PostgreSQL(DBaaS) db1v2m8 | 2vCore / 8GB | 254 원/시간 | 185,420 원 | 한국(오퍼링 Enterprises/Finance) | 별도(공공용) | 확인 필요 | 계정 크레딧 |  | [링크](https://cloud.samsungsds.com/serviceportal/services/database/PostgreSQL.html) |
| SCP-DB-04 | DB | CacheStore(DBaaS) redis1v1m2 | 1vCore / 2GB | 105 원/시간 | 76,650 원 | 한국(오퍼링 Enterprises/Finance) | 별도(공공용) | 확인 필요 | 계정 크레딧 |  | [링크](https://cloud.samsungsds.com/serviceportal/services/database/cacheStore.html) |
| SCP-STG-01 | 스토리지 | Block Storage SSD | 블록 스토리지 | 120 원/GB-월 | - | KR WEST | 별도(공공용) | 확인 필요 | 계정 크레딧 | HDD 55원, KR WEST 기준 | [링크](https://cloud.samsungsds.com/serviceportal/services/storage/blockStorage.html) |
| SCP-STG-02 | 스토리지 | Object Storage | 객체 스토리지 | 28 원/GB-월 | - | 한국(오퍼링 Enterprises/Finance) | 별도(공공용) | 확인 필요 | 계정 크레딧 | '26.1.1부터 적용 요금 | [링크](https://cloud.samsungsds.com/serviceportal/services/storage/objStorage.html) |
| SCP-STG-03 | 스토리지 | File Storage HDD | 파일 스토리지 | 70 원/GB-월 | - | KR WEST | 별도(공공용) | 확인 필요 | 계정 크레딧 | SSD 120원, KR WEST 기준 | [링크](https://cloud.samsungsds.com/serviceportal/services/storage/fileStorage.html) |
| SCP-NET-01 | 네트워크 | Load Balancer | 부하 분산 | 26 원/시간 | 18,980 원 | 한국(오퍼링 Enterprises/Finance) | 별도(공공용) | 확인 필요 | 계정 크레딧 | + 인입 7원/GB | [링크](https://cloud.samsungsds.com/serviceportal/services/network/loadBalancer.html) |
| SCP-NET-02 | 네트워크 | Direct Connect 1Gbps | 전용 회선 연결 | 100,000원/월 + 47원/GB | - | 한국(오퍼링 Enterprises/Finance) | 별도(공공용) | 지원(전용회선) | 계정 크레딧 |  | [링크](https://cloud.samsungsds.com/serviceportal/services/network/directConnect.html) |
| SCP-NET-03 | 네트워크 | VPN (IPsec VPN Gateway) | IPsec VPN | 60 원/시간 | 43,800 원 | 한국(오퍼링 Enterprises/Finance) | 별도(공공용) | 지원(IPsec VPN) | 계정 크레딧 | 아웃바운드 20GB 초과 100원/GB부터 | [링크](https://cloud.samsungsds.com/serviceportal/services/network/vpn.html) |
| SCP-NET-04 | 네트워크 | Firewall Extra Small | VPC 방화벽(규칙 5개 이하) | 120 원/시간 | 87,600 원 | 한국(오퍼링 Enterprises/Finance) | 별도(공공용) | 확인 필요 | 계정 크레딧 | + 인입 73원/GB | [링크](https://cloud.samsungsds.com/serviceportal/services/network/firewall.html) |
| SCP-SEC-01 | 보안 | Key Management Service | 키 관리 | 1,000원/키-월 | - | 한국(오퍼링 Enterprises/Finance) | 별도(공공용) | 확인 필요 | 계정 크레딧 | 월 2만 건 초과 시 1만 건당 30원 | [링크](https://cloud.samsungsds.com/serviceportal/services/security/kms.html) |
| SCP-SEC-02 | 보안 | WAF 100Mbps | 웹 방화벽 | 370,000원/월(1년 약정) | - | 한국(오퍼링 Enterprises/Finance) | 별도(공공용) | 확인 필요 | 계정 크레딧 |  | [링크](https://cloud.samsungsds.com/serviceportal/services/security/waf.html) |

**출처 보충 (원본 데이터 위치)**

- AWS: 요금 페이지가 불러오는 공개 가격 데이터 `b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/…`(EC2 게시일 2026-10-15, RDS 2026-10-20)에서 `Asia Pacific (Seoul)` 값을 읽었습니다.
- GCP: 각 요금 페이지의 지역 선택을 `Seoul (asia-northeast3)`로 바꾼 뒤 표를 읽었습니다. GCP는 USD 외 통화로 결제하면 Cloud Platform SKU의 현지 통화 가격이 적용된다고 안내합니다.
- KT Cloud: 상품 페이지에 서버 단가가 없어, 공식 요금계산기(`cloud.kt.com/calculator/`)가 쓰는 요금 데이터에서 값을 읽었습니다. 계산기 화면에는 '추정 요금으로 실제 사용 요금과 다를 수 있다'는 안내가 있습니다.
- NHN Cloud: 요금 페이지 기본 표(리전 선택 전 상태)의 값입니다. 판교/평촌 리전별 차이는 재확인이 필요합니다.

---

## ② 공공 요건 판단 자료 목록

### ②-1 CSP별 CSAP(클라우드 보안인증) IaaS 인증 현황

출처: [KISA ISMS-P 누리집 – CSAP 인증서 발급현황](https://isms-p.or.kr/sttus/vrtl/selectVrtlCrtfctList.do) (인증범위 'IaaS' 검색, 2026-10-21 확인)

| CSP | 인증번호 | 인증범위 | 유효기간 | 유지여부 |
|---|---|---|---|---|
| AWS | CSAP-2025-014호 | 아마존 웹 서비스(AWS) 서울 리전에서 제공하는 클라우드컴퓨팅서비스 (다그룹) (하등급 IaaS) | 2025-03-28 ~ 2030-03-27 | 유지 |
| GCP | CSAP-2025-002호 | 구글 클라우드 플랫폼(GCP, 하등급, 다 그룹 용)(하등급 IaaS) | 2025-01-22 ~ 2030-01-21 | 유지 |
| NCP(네이버클라우드) | CSAP-2017-001호 | 네이버클라우드플랫폼 공공기관용(IaaS) | 2022-02-24 ~ 2027-02-23 | 유지 |
| NHN Cloud | CSAP-2017-003호 | NHN Cloud (공공기관용)(IaaS) | 2022-12-13 ~ 2027-12-12 | 유지 |
| NHN Cloud | CSAP-2025-006호 | NHN Cloud (NCGN) (IaaS) | 2025-02-27 ~ 2030-02-26 | 유지 |
| KT Cloud | CSAP-2016-001호 | KT G-Cloud 서비스(IaaS) | 2021-10-20 ~ **2026-10-19** | 유지 (※ 유효기간 종료일이 지났으나 목록상 '유지' 표기 — 갱신 여부 확인 필요) |
| KT Cloud | CSAP-2026-010호 | kt cloud PLATFORM 공공기관용 (IaaS) | 2026-03-25 ~ 2031-03-24 | 유지 |
| SCP(삼성 클라우드 플랫폼) | CSAP-2019-004호 | Samsung Cloud Platform(G Cloud)(IaaS) | 2024-08-28 ~ 2029-08-27 | 유지 |

- AWS·GCP는 **하등급** IaaS만 인증 범위입니다. 상·중등급 데이터를 다루는 공공 시스템에는 그대로 쓸 수 없습니다(등급 기준은 아래 고시 확인).
- 이용 조건: 공개 조회 페이지. 별도 공공누리 표시 없음 → 인증 현황 '사실'만 인용하고 화면 원문 복제는 피합니다.

### ②-2 공공 요건 PDF·원문 자료

| # | 자료명 | 발행처 | 판·시행일 | 형태 | URL | 저작권·이용 조건 | 용도 |
|---|---|---|---|---|---|---|---|
| P1 | 클라우드서비스 보안인증기준 해설서(26.07) | 한국인터넷진흥원(KISA) | 2026-07 (2026-07-28 오탈자 수정) | PDF | [KISA 자료실(클라우드보안인증제)](https://isms-p.or.kr/ntcn/rcsrm/selectGnrlVrtlRcsrmList.do) — 게시글 '2026년 클라우드서비스 보안인증기준 해설서(2026.07)' 첨부 | 게시 페이지에 공공누리 표시 없음 → **확인 필요**. 같은 제목 이전 판은 공공데이터포털에 **공공누리 제4유형**(출처표시·상업적 이용금지·변경금지)으로 등록됨 | 공공부문 특화 요구사항(14번 항목) 근거 |
| P2 | 한국인터넷진흥원_클라우드서비스 보안인증기준 해설서 (공공데이터포털 등록본) | 한국인터넷진흥원 | 등록본 판 **확인 필요** | PDF(파일데이터) | [공공데이터포털 15160242](https://www.data.go.kr/biz/dcat/metadata/15160242.do) | **공공누리 제4유형** (출처표시, 상업적 이용금지, 변경금지) | P1의 재배포 가능 판본 후보 |
| P3 | 2026년 클라우드 보안인증 FAQ(2026.07) | 한국인터넷진흥원 | 2026-07-06 | PDF 첨부 | [KISA 자료실](https://isms-p.or.kr/ntcn/rcsrm/selectGnrlVrtlRcsrmList.do) | 공공누리 표시 없음 → **확인 필요** | 인증 등급·절차 질의응답 근거 |
| P4 | 클라우드컴퓨팅서비스 보안인증에 관한 고시 | 과학기술정보통신부(고시 제2023-4호) | 시행 2023-01-31 | 법령 원문(HTML, PDF 저장 가능) | [국가법령정보센터](https://www.law.go.kr/행정규칙/클라우드컴퓨팅서비스보안인증에관한고시) | 법령·고시는 저작권법 제7조에 따라 보호 대상 아님 (출처 표기 권장) | 보안인증 유형·기준 근거 |
| P5 | 행정기관 및 공공기관의 클라우드컴퓨팅서비스 이용 기준 및 안전성 확보 등에 관한 고시 | 행정안전부(고시 제2025-79호) | 시행 2025-12-29 | 법령 원문 | [국가법령정보센터](https://www.law.go.kr/행정규칙/행정기관및공공기관의클라우드컴퓨팅서비스이용기준및안전성확보등에관한고시) | 저작권법 제7조 (보호 대상 아님) | 공공기관의 민간 클라우드 이용 기준(Q1, Q5) |
| P6 | 클라우드컴퓨팅 발전 및 이용자 보호에 관한 법률 | 법률 제21066호 | 시행 2025-10-01 | 법령 원문 | [국가법령정보센터](https://www.law.go.kr/법령/클라우드컴퓨팅발전및이용자보호에관한법률) | 저작권법 제7조 (보호 대상 아님) | 상위 법률 근거 |
| P7 | 행정기관 및 공공기관 정보시스템 구축·운영 지침 | 행정안전부(고시 제2025-1호) | 시행 2025-01-02 | 법령 원문 | [국가법령정보센터](https://www.law.go.kr/행정규칙/행정기관및공공기관정보시스템구축·운영지침) | 저작권법 제7조 (보호 대상 아님) | 제6조: 클라우드 우선 검토 의무 |
| P8 | 국가 망 보안체계(N²SF) 보안 가이드라인 1.0 | 국가정보원 | 2025-09-30 공개(언론 보도 기준) | PDF | 공식 배포 URL **확인 필요** (보도: [바이라인네트워크](https://byline.network/2025/09/30-445/)) | **확인 필요** | 공공 망 보안·등급 분류 참고 |

**참고(PDF 아님, 제도 변경 근거)**: [바이라인네트워크 2026-04-20 – 공공 클라우드 보안 검증, ‘국정원 단일 검증 체계’로 일원화](https://byline.network/2026/04/20-578/) — 과기정통부·국정원 발표. 기존 CSAP 절차는 1년 유예, 2027년 하반기 본격 시행, 기존 인증서는 잔여 유효기간 동안 유효. 공식 보도자료 원문은 확인 필요.

---

## ③ 로그인·회원가입이 필요해 수집하지 않은 정보

| CSP·기관 | 정보 | 막힌 이유 | 대안 |
|---|---|---|---|
| SCP | 무료체험 크레딧 신청·사용 조건 세부 | 페이지에 'Console 로그인 후 이용할 수 있습니다' 안내 | 공개된 요약(30만원/3개월)만 기록 |
| GCP | 원화(KRW) 결제 시 실제 SKU 단가 | USD 외 통화는 'Cloud Platform SKUs' 가격 적용 — 콘솔·결제 계정(또는 API 키)이 필요한 SKU 카탈로그에서 확인 | USD 단가로 비교하고 환율 기준일을 별도 표기 |
| AWS·GCP | 무료 크레딧(최대 200 USD / 300 USD) 실제 적용 범위 | 계정 생성·결제수단 등록 후 콘솔에서 확인 | 계정 단위 혜택으로만 기록 |
| KT Cloud | 무료체험(가입 1개월 이내 50만원/90일) 신청 | 회원가입 필요 | 사이트 배너 문구만 기록 |
| AWS·GCP·NCP·NHN·KT·SCP | 약정 할인·맞춤 견적 | 콘솔 또는 영업 상담(맞춤 견적 요청) 필요 | 온디맨드 정가만 사용 |

**로그인과 무관하지만 공개 단가가 없는 항목(영업 문의·협정가)**

- NCP Cloud Connect: Cross Connect·통신사 전용회선 비용·설치비는 별도 문의
- KT Cloud 전용 VPN(다수 사이트·SSL VPN): 협정가
- SCP Direct Connect 20/40Gbps 전용 Edge 호스트: SR로 별도 과금
- NHN App Security Check: M/M 기준 별도 문의
- 공공기관용 플랫폼(gov-ncloud.com 등)의 요금표는 이번에 조회하지 않음 → 다음 수집 대상

---

## ④ `확인 필요` 항목 요약

| 대상 | 내용 | 다음 확인 방법 |
|---|---|---|
| 108건 전체 – 공공 열 | 상품 단위로 공공기관용 플랫폼에서 제공되는지 미확인 | 각 CSP 공공기관용 상품 목록 페이지 대조 |
| 108건 중 94건 – 폐쇄망 열 | 전용회선·VPN·사설 엔드포인트 14건만 '지원' 확인. 나머지는 VPC 사설 배치 가능 여부 미확인 | 상품별 사용자 가이드의 VPC·Private Subnet 지원 항목 확인 |
| NCP·NHN – 무료 티어 | 신규 가입 크레딧 여부 미확인(NCP Micro 서버 1년 무료만 확인) | 각 사 프로모션 페이지 확인 |
| NHN – 리전 | 요금 표가 판교/평촌 중 어느 리전 기준인지 페이지에서 명시 확인 못 함 | 리전 탭 전환 후 값 비교 |
| KT – CSAP-2016-001호 | 유효기간 종료일(2026-10-19)이 지났는데 '유지' 표기 | KISA 목록 재조회 또는 KT 공지 확인 |
| P1·P3 – 이용 조건 | KISA 자료실 게시물에 공공누리 표시 없음 | KISA 클라우드인증팀(cloud@kisa.or.kr) 문의 또는 공공데이터포털 판본(P2) 사용 |
| P2 – 판 | 공공데이터포털 등록본이 2026.07 판인지 미확인 | 파일 내려받아 표지 확인 |
| P8 – 배포처·이용 조건 | 국정원 공식 배포 URL과 이용 조건 미확인 | 국가정보원·국가사이버안보센터 자료실 확인 |
| robots.txt·약관(미결 #3) | 이번 범위에서 제외 | 문서 수집 착수 전 별도 확인 |

