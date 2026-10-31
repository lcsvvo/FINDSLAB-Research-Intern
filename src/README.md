# Source

| Module | Role |
|---|---|
| `data_prep.py` | 날짜, 수치 형식 정리와 산업, 시장, 금리 패널 생성 |
| `models.py` | HAC 금리베타, 날짜 클러스터 공동검정, 이동창 추정, 순위상관 |
| `krx_collector.py` | KRX API로 기업 시가총액 수집, 로컬 캐시 관리 |

- **진입점**: [단계별 Notebook](../notebooks/README.md)에서 함수 호출.
- **주요 함수**: `rate_beta_stats()`, `industry_rate_betas()`, `cross_industry_Ftest()`, `rolling_beta()`.
- **설정**: 경로와 공통 상수는 루트 `config.py`에서 관리.
- **수집 조건**: KRX 수집 시 `KRX_API_KEY` 환경변수 필요. API 제공 범위 밖의 구성종목, 배당 자료는 Notebook 입력 형식에 맞춰 별도 준비.
