# results/

분석 결과물(표, 그림, 추정치 요약)을 저장하는 폴더.

## 폴더 소개

- **What**: `src/models.py`(및 각 노트북) 실행 결과로 나오는 표·그래프
- **Why**: 분석 결과를 코드/데이터와 분리해서 버전 관리하고, PR·README에서 바로 참조하기 위함
- 핵심 기능 요약
  1. Baseline — 산업별 금리 베타 추정치·F-검정 결과
  2. H1 — 수익률곡선(Level·Slope·Curvature)·신용스프레드 노출 (모형 B)
  3. H2 — 금리 상승·하락 비대칭, 국면 상호작용 (모형 C)
  4. H3 — 기업 재무특성과 금리 민감도 (예정)
  5. (추후) 최종 보고서용 요약 그림

## 사용 기술 스택

matplotlib/pandas, statsmodels(OLS, HAC)

## 주요 결과 / 성과 지표

_파일명은 날짜 프리픽스 대신 내용 기준으로 짓는다(이력은 git이 관리). 규칙은 루트 README의 Naming Convention 표를 따른다._

## 디렉토리 구조

**결과물은 반드시 가설(Baseline/H1/H2/H3) 기준으로 관리하며, 이 원칙은 변경하지 않는다.** 각 가설 폴더 안에서 `figures/`(그림)와 `tables/`(표)를 분리한다. 폴더명은 가설을 따르지만, 이를 생성하는 notebook 번호는 분석 수행 순서일 뿐 가설 번호와 무관하다(예: Baseline은 `04_rate_beta_estimation.ipynb`, H1은 `06_yield_curve_exposure.ipynb`).

```
results/
├── README.md
├── EDA/                              # 산업 공통 기반 (STEP1-3 기초통계·EDA)
│   ├── figures/                      # *_timeseries.png, correlation_heatmap.png
│   ├── tables/                       # descriptive_statistics*.csv, correlation_matrix.csv
│   └── summary.html
├── Baseline_industry_beta/           # Baseline: 산업 간 금리베타 차이 (04·05)
│   ├── figures/  tables/
│   ├── summary.md
│   ├── 04_summary_final.html         # 노트북 04 결과 리포트
│   └── 05_summary_final.html         # 노트북 05 결과 리포트
├── H1_yield_curve/                   # H1: 금리충격 원천 분해, 모형 B (06)
│   ├── figures/                      # 01~10 (B-1 5 · B-2 1 · 사후 4)
│   ├── tables/                       # 확증 4 · 사후 7
│   ├── summary.md
│   └── 06_summary_final.html         # 노트북 06 결과 리포트
├── H2_asymmetry_regime/{figures,tables}/ summary.md       # H2: 비대칭·국면, 모형 C (07)
└── H3_firm_characteristics/{figures,tables}/              # H3: 기업 특성 (예정)
```

### 리포트 HTML 명명

가설 폴더 안의 결과 리포트는 **`NN_summary_final.html`** 로 저장한다.
`NN`은 그 결과를 만든 notebook 번호다(예: 노트북 06 → `06_summary_final.html`).
`summary.md`가 텍스트 요약이라면 이 HTML은 표·그림을 포함한 공유용 리포트다.

새 가설(H4 등)이 생기면 같은 패턴(`results/{Hn}_{설명}/`)의 폴더만 추가한다. 아직 착수되지 않은 선택(optional) 분석은 폴더를 미리 만들지 않고, 실제로 시작되는 시점에 추가한다.
