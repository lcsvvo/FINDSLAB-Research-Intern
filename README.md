# Industry Rate Beta — 산업별 금리 베타 분석

KRX 산업지수 수익률의 금리 민감도를 추정하고, 수익률곡선 요인·금리 방향과 정책국면·산업 재무특성으로 이어지는 후속 분석을 수행한 FINDS Lab 학부 연구인턴 프로젝트다.

`분석 완료` · `공개 release 검토 중` · `Python 3.9+`

## 1. 연구 개요

이 연구는 2016~2025년 KRX 7개 산업지수의 일별 수익률을 대상으로 KOSPI 수익률을 통제한 뒤 국고채 금리 변화에 대한 산업별 조건부 민감도(금리베타)를 추정한다. Baseline에서 산업 간 차이를 확인하고, 이후 분석에서 수익률곡선의 Level·Slope·Curvature, 금리 상승·하락과 정책국면, 기업 재무특성과의 탐색적 정렬을 차례로 살펴본다.

모든 결과는 동시점 조건부 연관이며 금리 변화가 산업 수익률을 인과적으로 변화시켰다는 의미가 아니다.

## 2. 연구 설계

연구 흐름은 다음과 같다.

```text
Baseline: 산업별 금리베타 차이
    ↓
H1: 금리충격의 원천 — 수익률곡선 요인
    ↓
H2: 상승·하락 비대칭과 정책국면
    ↓
H3: 산업 재무특성과의 탐색적 정렬
```

최초 계획서, 현재 가설 번호, 모형 A~E, 노트북과 결과 폴더의 상세 대응은 [`docs/HYPOTHESIS_MODEL_MAP.md`](docs/HYPOTHESIS_MODEL_MAP.md)를 참고한다.

## 3. 연구 질문

- **Baseline / 모형 A:** 시장을 통제한 뒤에도 산업마다 국고채 3년물 금리 민감도가 다른가?
- **H1 / 모형 B:** 산업 간 차이는 수익률곡선의 Level·Slope·Curvature 또는 Credit Spread 중 어느 차원에서 관찰되는가?
- **H2 / 모형 C·D:** 금리가 오를 때와 내릴 때 반응이 다른가? 정책국면에 따라 반응이 달라지는가?
- **H3 / 모형 E:** 산업 금리베타의 순위가 부채비율·배당수익률 등 산업 재무특성의 순위와 정렬되는가?

## 4. 데이터

| 구분 | 내용 |
|---|---|
| 분석 패널 | 2016-01-04~2025-12-30, 17,164 산업-일 관측치 |
| 회귀 표본 | 산업별 2,451 거래일(첫 차분 결측 제외) |
| 산업 | 건설업, 금융업, 운수장비, 의약품, 전기전자, 철강금속, 화학 |
| 산업·시장 | KRX 산업지수, KOSPI |
| 금리 | 한국은행 ECOS 국고채 1·3·5·10년 및 회사채 AA− 3년 |
| H3 기업표본 | 산업별 시가총액 상위 10개사, 7개 산업 70개사 |
| H3 기업-연도 | 2016~2025년 700 firm-year |
| 기업 재무자료 | DART OpenAPI 재무제표·배당, 사업보고서 원문 보완, KRX 시가총액·구성종목 |

원자료와 `data/`의 중간·최종 분석 데이터는 공개 저장소에서 추적하지 않는다. 커밋된 결과표와 보고서는 분석 결과 검토용이며, 원자료 라이선스와 API 인증정보를 포함하지 않는다.

## 5. 방법론

### Baseline

- 산업 수익률을 KOSPI 수익률과 국고채 3년물 일별 변화에 회귀하는 Two-Index Model
- 산업별 계수 추정은 HAC(Newey–West, maxlags=5)
- 산업 간 동일성 공동검정과 쌍별 비교는 날짜 클러스터 표준오차
- 산업별·쌍별 다중검정은 사전에 정의한 검정족별 BH(FDR) 보정

### H1

- Nelson–Siegel 수익률곡선 분해: Level·Slope·Curvature, 기본값 λ=0.5
- λ 대안·민감도, PCA, 모형 간 설명력, HAC 시차 민감도 점검
- 회사채 AA− 3년과 국고채 3년의 차이로 Credit Spread 구성
- 산업별 추정은 HAC, 산업 간 동일성 검정은 날짜 클러스터

### H2

- 금리 변화의 상승분·하락분 분해와 산업별 Wald 대칭성 검정
- 전 산업 동시검정과 산업 간 차이 검정은 날짜 클러스터
- BH 보정, 극단값·기간·rolling window·공분산 사양 민감도 점검
- 정책국면 상호작용과 금리 변동 크기 모형은 보조·확장 분석으로 구분

### H3

- 기업 재무특성의 산업별 시가총액가중 평균과 중앙값 집계
- 산업 단위 Spearman 순위상관과 exact permutation p-value(n=7)
- 집계 기준, 결측 처리, 금융업 제외, leave-one-out 민감도 점검
- 의약품 R&D와 시가총액 집중도는 인과 설명이 아닌 보조 기술통계

## 6. 주요 결과

### Baseline

- 주 사양인 날짜 클러스터 공동검정에서 산업별 금리베타 동일성이 기각되었다(F=4.189, p=0.000338).
- 산업별 HAC 추정에서는 금융업·운수장비·철강금속이 유의한 양(+)의 계수, 의약품이 유의한 음(−)의 계수로 관찰되었다.
- BH 보정 후 유의한 산업 쌍 6개는 모두 의약품을 포함한다. 따라서 결과는 모든 산업이 서로 다르다는 진술보다 의약품과 나머지 산업의 대비에 가깝다.

### H1

- 기본 λ=0.5에서 Curvature의 산업 간 차이가 관찰되었다(F=3.580, 검정족 내 BH p=0.0047). 의약품은 음(−), 운수장비는 양(+)의 곡률 계수로 나타났다.
- Level·Slope의 산업별 계수와 산업 간 차이는 BH 보정 후 유의수준에 도달하지 않았다. PCA에서 PC1이 금리곡선 변화의 92.09%를 설명해 요인별 해석에는 유보가 필요하다.
- 곡률 결과는 λ와 요인 구성에 민감하다. 곡선 적합 기준 대안 λ=0.8041에서는 산업별 곡률 계수가 BH 보정 후 유의하지 않아 λ=0.5 결과를 조건부 관찰로 해석한다.

### H2

- 국고채 3년물 상승·하락 계수의 직접 Wald 검정은 건설업에서만 BH 5% 기준을 충족했다(BH p=0.0089). 다른 6개 산업은 유의수준에 도달하지 않았다.
- 전 산업 동시검정의 원 p는 0.0401이지만 Y3·Curvature 두 공동검정을 함께 보정하면 0.0801이므로, 전체 공동결론은 검정족과 공분산 사양에 민감하다. Curvature 비대칭 공동검정은 비유의였다(p=0.6173).
- 정책국면 상호작용(모형 D)은 BH 보정 후 7개 산업 모두 비유의였다. 건설업 결과는 2021년 이후에 집중되고 극단일·기간 설정에 민감해 조건부 결과로 본다.

### H3

- 배당수익률과 금리베타는 시가총액가중 기준에서 양(+)의 순위상관이 관찰되었다(ρ=0.8571, exact p=0.0238). 중앙값 기준에서는 유의수준에 도달하지 않아 집계 방식에 민감하다.
- 부채비율은 시가총액가중·중앙값·금융업 제외 기준 모두 유의수준에 도달하지 않았다. leave-one-out 결과도 산업 하나의 제외에 민감하다.
- H3는 산업 수가 7개인 탐색적 분석이다. 의약품의 낮은 배당수익률·부채비율, R&D 지출, 시가총액 집중도는 기술적 관찰이며 음(−)의 금리베타 원인을 입증하지 않는다.

## 7. Repository 구조

아래는 연구 결과를 확인하는 데 필요한 주요 공개 구조다.

```text
FINDSLAB-Research-Intern/
├── README.md
├── config.py
├── requirements.txt
├── pyproject.toml
├── src/
│   ├── data_prep.py
│   └── models.py
├── notebooks/
│   └── 01_data_preparation.ipynb ... 10_firm_characteristics_analysis.ipynb
├── results/
│   ├── EDA/
│   ├── Baseline_industry_beta/
│   ├── H1_yield_curve/
│   ├── H2_asymmetry_regime/
│   └── H3_firm_characteristics/
└── docs/
    └── HYPOTHESIS_MODEL_MAP.md
```

`data/`, `.env`, 캐시와 개인 작업 문서는 Git 추적 대상이 아니다.

## 8. Notebook 안내

별도의 통합 Final Notebook은 없다. 최종 분석은 아래 source notebook에 단계별로 기록되어 있으며, 결과 확인은 각 가설의 summary/HTML에서 시작하는 것이 가장 빠르다.

| Notebook | 역할 |
|---|---|
| [`01_data_preparation.ipynb`](notebooks/01_data_preparation.ipynb) | KRX·KOSPI·금리 원자료 정제·병합 |
| [`02_variable_generation.ipynb`](notebooks/02_variable_generation.ipynb) | 수익률·금리 변화·장단기차 생성 |
| [`03_eda_industry.ipynb`](notebooks/03_eda_industry.ipynb) | 기술통계·시계열·상관관계 점검 |
| [`04_rate_beta_estimation.ipynb`](notebooks/04_rate_beta_estimation.ipynb) | Baseline 산업별 HAC 금리베타 |
| [`05_baseline_industry_difference.ipynb`](notebooks/05_baseline_industry_difference.ipynb) | Baseline 날짜 클러스터 공동·쌍별검정 |
| [`06_yield_curve_exposure.ipynb`](notebooks/06_yield_curve_exposure.ipynb) | H1 수익률곡선·Credit Spread·민감도 |
| [`07_asymmetric_rate_response.ipynb`](notebooks/07_asymmetric_rate_response.ipynb) | H2 상승·하락 비대칭과 강건성 |
| [`08_regime_interaction.ipynb`](notebooks/08_regime_interaction.ipynb) | H2 정책국면 상호작용 |
| [`09_firm_data_collection.ipynb`](notebooks/09_firm_data_collection.ipynb) | H3 DART/KRX 기업자료 수집·보완 |
| [`10_firm_characteristics_analysis.ipynb`](notebooks/10_firm_characteristics_analysis.ipynb) | H3 산업집계·exact Spearman·LOO |

## 9. 주요 산출물

| 단계 | Summary / Report | 핵심 Table | 핵심 Figure |
|---|---|---|---|
| Baseline | [`summary.md`](results/Baseline_industry_beta/summary.md) · [`05_summary_final.html`](results/Baseline_industry_beta/05_summary_final.html) | [`industry_beta_joint_test.csv`](results/Baseline_industry_beta/tables/industry_beta_joint_test.csv) | [`05_pairwise_beta_difference_heatmap.png`](results/Baseline_industry_beta/figures/05_pairwise_beta_difference_heatmap.png) |
| H1 | [`summary.md`](results/H1_yield_curve/summary.md) · [`06_summary_final.html`](results/H1_yield_curve/06_summary_final.html) | [`industry_difference_test.csv`](results/H1_yield_curve/tables/industry_difference_test.csv) | [`09_industry_difference_test.png`](results/H1_yield_curve/figures/09_industry_difference_test.png) |
| H2 | [`summary.md`](results/H2_asymmetry_regime/summary.md) · [`08_summary.html`](results/H2_asymmetry_regime/08_summary.html) | [`asymmetry_wald_tests.csv`](results/H2_asymmetry_regime/tables/asymmetry_wald_tests.csv) | [`03_asymmetry_wald_comparison.png`](results/H2_asymmetry_regime/figures/03_asymmetry_wald_comparison.png) |
| H3 | [`summary.md`](results/H3_firm_characteristics/summary.md) · [`H3_report.html`](results/H3_firm_characteristics/H3_report.html) | [`spearman_results.csv`](results/H3_firm_characteristics/tables/spearman_results.csv) | [`beta_vs_characteristics.png`](results/H3_firm_characteristics/figures/beta_vs_characteristics.png) |

## 10. 재현 방법

### 환경 구성

```bash
git clone https://github.com/lcsvvo/FINDSLAB-Research-Intern.git
cd FINDSLAB-Research-Intern
python -m venv .venv
pip install -r requirements.txt
pip install -e .
jupyter lab
```

### 최종 분석 재현

공개 저장소에는 데이터가 포함되지 않는다. 권한이 있는 원자료를 동일한 `data/raw/` 구조에 배치한 뒤 `01`→`10` 순서로 실행한다. 이미 생성된 분석 패널을 제공받은 경우에는 다음 파일을 `data/processed/`에 배치하고 필요한 분석 notebook부터 실행할 수 있다.

- `industry_rate_panel_daily.csv`: Baseline 입력
- `industry_rate_panel_extended.csv`: H1·H2 입력
- `firm_financials_recovered.csv`, `industry_characteristics.csv`, `industry_characteristics_median.csv`: H3 입력

### 데이터 수집 재현

- KRX 산업지수·KOSPI와 ECOS 금리는 원자료 파일을 별도로 확보해야 한다.
- H3 DART 수집에는 `OPENDART_API_KEY` 환경변수가 필요하다. 실제 키는 `.env` 또는 저장소 밖의 비밀 저장소에서 관리하고 커밋하지 않는다.
- DART 사업보고서 원문 보완과 일부 KRX 구성종목·시가총액 입력은 notebook 09의 절차와 동일한 원자료가 필요하다.

## 11. Limitations

- 금리 변화에는 할인율 뉴스와 경기 뉴스가 함께 포함되어 있어 순수한 통화정책 충격으로 식별되지 않는다.
- 일별 동시점 회귀는 조건부 연관을 보여줄 뿐 인과효과를 식별하지 않는다.
- H1의 요인별 결론은 Nelson–Siegel λ와 높은 요인 상관에 민감하다.
- H2 건설업 결과는 시기·극단일·검정족과 표준오차 사양에 민감하다.
- H3는 산업 단위 n=7의 탐색적 순위상관이며 집계 방식과 개별 산업의 영향이 크다.
- 비공개 원자료와 수기 보완자료가 공개 저장소에 없어 clone만으로 완전 재현할 수 없다.

## 12. Project Status

- Baseline, H1, H2, H3 분석과 주요 표·그림·summary/report 생성 완료
- 가설·모형·notebook·결과 폴더 대응표 작성 완료
- 공개용 README 및 상대경로 링크 정리 완료
- 최종 GitHub release 검토 진행 중
