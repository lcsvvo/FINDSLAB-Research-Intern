# 가설·모형 번호 체계 대응표

이 프로젝트에는 번호 체계가 세 개 있다. 계획서(2026-06)의 H1/H2/H3, 7월 16일 개편 후의 Baseline/H1/H2/H3,
그리고 팀 내부에서 쓰는 모형 A~E다. 같은 기호가 서로 다른 대상을 가리키므로 최종 보고서에는 이 표를 부록으로 넣는다.

## 1. 대응표

| 계획서 (2026-06) | 개편 후 (2026-07-16) | 모형 | 노트북 | 결과 폴더 | 상태 |
|---|---|---|---|---|---|
| H1 산업 간 차이 | Baseline | 모형 A | `04_rate_beta_estimation`<br>`05_baseline_industry_difference` | `results/Baseline_industry_beta/` | 완료 |
| §5 데이터 엣지 · §6(e) 곡선요인 베타 | H1 금리충격의 원천 | 모형 B | `06_yield_curve_exposure` | `results/H1_yield_curve/` | 완료 |
| — (개편 시 신설) | H2 전반 · 방향 비대칭 | 모형 C | `07_asymmetric_rate_response` | `results/H2_asymmetry_regime/` | 완료 |
| — (개편 시 신설) | H2 후반 · 국면 의존성 | 모형 D | `08_regime_interaction` | `results/H2_asymmetry_regime/` (`regime_` 접두) | 완료 |
| H3 구조적 연관 | H3 기업 재무특성 | 모형 E | `09_firm_data_collection`<br>`10_firm_characteristics_analysis` | `results/H3_firm_characteristics/` | 완료 |

> 노트북 번호는 분석 수행 순서일 뿐 가설 번호와 연결하지 않는다(`README.md` §6).

## 2. 각 단계가 답하는 질문

| 모형 | 질문 | 핵심 검정 |
|---|---|---|
| A (Baseline) | 시장을 통제한 뒤에도 산업마다 금리 민감도가 다른가 | 산업더미 × Δy3 교차항 F검정 |
| B (H1) | 그 차이가 곡선의 어느 부분에서 오는가 | Level·Slope·Curvature·Credit Spread 산업 간 동일성 검정 |
| C (H2 전반) | 금리가 오를 때와 내릴 때 반응이 다른가 | H0: β_up = β_down (Wald) |
| D (H2 후반) | 같은 금리변화라도 긴축기·신용위험 고조기에 반응이 커지는가 | 국면 더미 × 방향변수 상호작용 계수 검정 |
| E (H3) | 산업 간 차이가 기업 재무특성으로 설명되는가 | Spearman 순위상관 (n=7, 탐색적) |
