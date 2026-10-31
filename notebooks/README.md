# Notebooks

- **전체 분석 열람**: [final.ipynb](final.ipynb).
- **실행 순서**: 원자료 준비 후 `01`부터 `10`까지 순서대로 실행. 기존 가공자료가 있으면 해당 분석부터 실행 가능.
- **결과 탐색**: [results/](../results/README.md)의 분석별 요약과 결과표 참고.

## Analysis Order

| Notebook | Role | Output |
|---|---|---|
| [01](01_data_preparation.ipynb) | 산업지수, KOSPI, 금리 정제와 병합 | 원본 수준 패널 |
| [02](02_variable_generation.ipynb) | 수익률, 금리 차분, 장단기차 생성 | 일별 분석 패널 |
| [03](03_eda_industry.ipynb) | 기술통계, 시계열, 상관관계 | [EDA](../results/EDA/) |
| [04](04_rate_beta_estimation.ipynb) | 산업별 2지수 회귀와 HAC 추정 | [Baseline](../results/Baseline_industry_beta/) |
| [05](05_baseline_industry_difference.ipynb) | 날짜 클러스터 공동검정, 쌍별 비교 | [Baseline](../results/Baseline_industry_beta/) |
| [06](06_yield_curve_exposure.ipynb) | Nelson–Siegel 요인, 신용스프레드 회귀 | [H1](../results/H1_yield_curve/) |
| [07](07_asymmetric_rate_response.ipynb) | 상승, 하락 계수와 Wald 검정 | [H2](../results/H2_asymmetry_regime/) |
| [08](08_regime_interaction.ipynb) | 정책국면별 계수와 상호작용 추정 | [H2](../results/H2_asymmetry_regime/) |
| [09](09_firm_data_collection.ipynb) | DART, KRX 기업자료 수집과 산업별 집계 | 기업 재무자료 |
| [10](10_firm_characteristics_analysis.ipynb) | 금리베타와 재무특성의 순위상관, 정확 순열검정 | [H3](../results/H3_firm_characteristics/) |

## Inputs

`data/`는 로컬 입력 경로이며 공개 저장소에서 제외.

| Path | Content |
|---|---|
| `data/raw/industry/` | KRX 산업별 지수 자료 |
| `data/raw/market/kospi_index/` | KOSPI 지수 자료 |
| `data/raw/rates/` | ECOS 국고채 만기별 금리, 회사채 AA− 3년 금리 |
| `data/raw/firm/` | DART 기업 재무자료, 선정 기업 목록 |
| `data/raw/firm/krx_manual/` | 구성종목, 시가총액, 사업보고서 보완 자료 |
| `data/processed/industry_rate_panel_daily.csv` | Baseline 입력 패널 |
| `data/processed/industry_rate_panel_extended.csv` | 수익률곡선, 비대칭 분석 입력 패널 |
| `data/processed/firm_financials_recovered.csv` | 보완 기업 재무자료 |

세부 열 이름과 원본 파일 형식은 각 Notebook과 `config.py` 참고.

## Setup

Python 3.9 이상 환경에서 저장소 루트 기준 실행.

```bash
pip install -e .
jupyter lab
```

- **인증**: 기업자료 수집 시 `OPENDART_API_KEY`, `KRX_API_KEY` 환경변수 설정. 실제 키는 로컬에서만 관리.
- **데이터**: 이용 권한이 있는 원자료를 위 경로에 배치. API 키만으로 수기 보완 자료가 생성되지는 않음.
