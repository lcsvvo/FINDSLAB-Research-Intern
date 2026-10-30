# 공통 분석 코드

| 모듈 | 역할 |
|---|---|
| `data_prep.py` | 원자료 읽기, 날짜·수치 형식 정리, 산업·시장·금리 패널 생성 |
| `models.py` | 산업별 HAC 금리베타, 날짜 클러스터 산업 간 동일성 검정, 이동창 추정, 순위상관 |
| `krx_collector.py` | KRX 공식 API 기반 기업 시가총액 수집과 로컬 캐시 관리 |

주요 함수는 `rate_beta()`, `rate_beta_stats()`, `industry_rate_betas()`, `cross_industry_Ftest()`, `rolling_beta()`다. 분석별 실행 예시와 결과는 `notebooks/`에 있다. `models.py`의 직접 실행 예시는 합성 데이터를 사용한다.

KRX 수집에는 `KRX_API_KEY`가 필요하다. 공식 API에서 제공하지 않는 구성종목·배당 등 자료는 각 노트북의 입력 형식에 맞춰 별도로 준비한다. 경로와 공통 분석 상수는 루트 `config.py`에서 관리한다.
