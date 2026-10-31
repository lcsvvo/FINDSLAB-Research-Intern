# Results

분석별 요약, CSV 결과표, 그림. 원자료는 미포함.

| Analysis | Summary | Main Table |
|---|---|---|
| EDA | [기술통계와 상관관계](EDA/tables/) | [산업별 기술통계](EDA/tables/descriptive_statistics_by_industry.csv) |
| Baseline | [산업별 금리베타](Baseline_industry_beta/summary.md) | [날짜 클러스터 공동검정](Baseline_industry_beta/tables/industry_beta_joint_test.csv) |
| H1 | [수익률곡선 요인](H1_yield_curve/summary.md) | [요인별 산업 간 차이](H1_yield_curve/tables/industry_difference_test.csv) |
| H2 | [상승, 하락 비대칭](H2_asymmetry_regime/summary.md) | [Wald 검정](H2_asymmetry_regime/tables/asymmetry_wald_tests.csv) |
| H3 | [산업 재무특성](H3_firm_characteristics/summary.md) | [순위상관과 순열검정](H3_firm_characteristics/tables/spearman_results.csv) |

- **구성**: 각 분석 폴더의 `tables/`는 결과표, `figures/`는 그림.
- **논문 그림**: [paper_figures/](paper_figures/README.md)에 README에 사용한 원본 이미지 수록.
- **해석 조건**: 검정족, 표준오차, λ, 집계 기준에 따라 결과가 달라짐. 각 요약의 조건과 함께 해석.
