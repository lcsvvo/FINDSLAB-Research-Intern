"""
=====================================================================
 rate_beta.py  --  산업별 금리 베타 분석 (김지우 팀)
 2지수 모형(시장+금리)으로 산업별 금리 베타를 HAC 표준오차로 추정하고,
 산업 간 차이(F-검정), rolling 변동성, 산업특성과의 순위상관을 검토.
---------------------------------------------------------------------
 Python >= 3.9 ; 설치: pip install numpy pandas scipy statsmodels
=====================================================================
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import spearmanr
from statsmodels.stats.multitest import multipletests

# #####################################################################
# [ 1 ] 기본 코드 — 핵심 (2지수 모형 금리 베타, HAC)
# #####################################################################

# ---------------------------------------------------------------------
# 1. 2지수 모형 : 산업별 금리 베타 (HAC 표준오차)
# ---------------------------------------------------------------------
def rate_beta(ind_ret, mkt_ret, d_yield, hac_lags=5):
    # [대체값] hac_lags=5 : Newey-West 시차(일별 자기상관 길이). 보통 4~10에서 고르시면 됩니다.
    X = sm.add_constant(pd.concat([mkt_ret.rename("mkt"),
                                   d_yield.rename("dY")], axis=1))
    res = sm.OLS(ind_ret, X, missing="drop").fit(
        cov_type="HAC", cov_kwds={"maxlags": hac_lags})
    return res.params["dY"], res.bse["dY"], res.pvalues["dY"]   # beta_r, SE, p


# ---------------------------------------------------------------------
# 1-b. STEP4 결과표용 : 산업 1개 2지수 회귀의 전체 통계 (t·p·CI·n·R²)
# ---------------------------------------------------------------------
def rate_beta_stats(ind_ret, mkt_ret, d_yield, hac_lags=5, alpha=0.05):
    """rate_beta()와 '동일한' 2지수 회귀(R = a + βM·mkt + βr·d_yield, HAC)를 적합하되,
    STEP4 결과표에 필요한 전체 통계를 dict로 반환한다. 회귀식은 바꾸지 않는다.
    (rate_beta()는 rolling_beta()가 3-튜플 반환에 의존하므로 그대로 둔다.)

    반환 keys : beta_rate, std_error, t_value, p_value, ci_lower, ci_upper,
                n_obs, r_squared  (t·p·CI 모두 HAC 공분산 기반)
    """
    X = sm.add_constant(pd.concat([mkt_ret.rename("mkt"),
                                   d_yield.rename("dY")], axis=1))
    res = sm.OLS(ind_ret, X, missing="drop").fit(
        cov_type="HAC", cov_kwds={"maxlags": hac_lags})
    ci_lower, ci_upper = res.conf_int(alpha=alpha).loc["dY"]
    return {
        "beta_rate": res.params["dY"],
        "std_error": res.bse["dY"],
        "t_value": res.tvalues["dY"],
        "p_value": res.pvalues["dY"],
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "n_obs": int(res.nobs),
        "r_squared": res.rsquared,
    }


# ---------------------------------------------------------------------
# 1-c. STEP4 드라이버 : long 패널 -> 산업별 결과표(DataFrame). 함수 하나로 7개 산업 실행.
# ---------------------------------------------------------------------
def industry_rate_betas(panel, ret_col="industry_return", mkt_col="kospi_return",
                        yield_col="d_y3", industry_col="industry",
                        hac_lags=5, alpha=0.05):
    """long 패널(산업별로 쌓인 일별 데이터)에서 산업마다 '동일한' 2지수 회귀(HAC)를
    실행해 산업별 금리 베타 결과표를 만든다.

    Parameters
    ----------
    panel : pd.DataFrame
        최소 [industry_col, ret_col, mkt_col, yield_col] 컬럼을 가진 long 패널.
        (예: data/processed/industry_rate_panel_daily.csv)
    yield_col : str
        금리 변화 변수. 기본 "d_y3"(국고채 3년). "d_y10"·"d_term_spread"로 바꾸면
        회귀식·구조 변경 없이 강건성 검정에 그대로 재사용한다.

    Returns
    -------
    pd.DataFrame
        컬럼 = [industry, beta_rate, std_error, t_value, p_value,
                ci_lower, ci_upper, n_obs, r_squared], 산업명 오름차순.
    """
    cols = ["industry", "beta_rate", "std_error", "t_value", "p_value", "p_value_bh",
            "ci_lower", "ci_upper", "n_obs", "r_squared"]
    rows = []
    for industry, g in panel.groupby(industry_col):
        sub = g[[ret_col, mkt_col, yield_col]].dropna()
        stats = rate_beta_stats(sub[ret_col], sub[mkt_col], sub[yield_col],
                                hac_lags=hac_lags, alpha=alpha)
        rows.append({"industry": industry, **stats})
    out = pd.DataFrame(rows).sort_values("industry").reset_index(drop=True)
    # BH(FDR) 보정 p-value 추가(7개 산업 다중검정). 기존 p_value는 유지.
    out["p_value_bh"] = multipletests(out["p_value"].values, method="fdr_bh")[1]
    return out.reindex(columns=cols)

# #####################################################################
# [ 2 ] Robustness — 산업 간 차이 F검정 · rolling · 순위상관
# #####################################################################

# ---------------------------------------------------------------------
# 2. 산업 간 차이 검정 (H1) : 산업더미 x 금리변화 교차항의 동일성 F-검정
# ---------------------------------------------------------------------
def cross_industry_Ftest(long_df, dates=None, date_col="date", hac_lags=None):
    """산업 간 금리 베타 동일성 F-검정 (H0: 모든 산업의 교차항 계수가 같다).

    long_df : columns = [industry, ret, mkt, dY]  (산업을 세로로 쌓은 long 형식)
    dates   : 각 행의 날짜(그룹) 라벨. None이면 long_df[date_col]을 사용.
    date_col: 날짜 컬럼명(기본 "date"). 날짜 기준 Cluster SE의 그룹 키.
    hac_lags: Deprecated. Cluster SE에서는 사용하지 않음(하위호환·향후 DK 대비 유지).

    표준오차: 날짜 기준 Cluster Robust로 같은 날 산업 간 잔차 상관(횡단면 상관)을 보정.
    (시계열 HAC는 이 상관을 놓쳐 검정이 과도하게 보수적이 되므로 쓰지 않는다.)
    """
    d = long_df.copy()
    if dates is None:
        if date_col not in d.columns:
            raise ValueError(f"날짜가 필요합니다. dates 인자 또는 long_df['{date_col}']를 넘기세요.")
        dates = d[date_col]
    d = d.assign(_grp=np.asarray(dates)).dropna(
        subset=["industry", "ret", "mkt", "dY", "_grp"])
    date_codes = pd.factorize(d["_grp"])[0]                              # 날짜 -> 정수 그룹키
    if len(np.unique(date_codes)) < 2:                                  # 그룹 1개면 Cluster SE 무의미
        raise ValueError("날짜 그룹이 2개 이상이어야 Cluster SE를 계산할 수 있습니다.")
    dummies = pd.get_dummies(d["industry"], prefix="ind", dtype=float)
    inter = dummies.mul(d["dY"].values, axis=0).add_prefix("dY_")        # 산업별 금리 교차항
    mkt_inter = dummies.mul(d["mkt"].values, axis=0).add_prefix("mkt_")  # 산업별 시장 통제
    X = pd.concat([dummies, mkt_inter, inter], axis=1)
    # TODO(H2 이후): 시계열 자기상관까지 보정하려면 Driscoll-Kraay 검토(f_test NaN 이슈 확인 필요).
    res = sm.OLS(d["ret"].values, X.values).fit(
        cov_type="cluster", cov_kwds={"groups": date_codes})            # 날짜 클러스터 SE
    names = list(X.columns)
    dY_idx = [i for i, c in enumerate(names) if c.startswith("dY_")]
    R = np.zeros((len(dY_idx)-1, len(names)))                            # 교차항 계수 동일성 제약
    for r, j in enumerate(dY_idx[1:]):
        R[r, dY_idx[0]] = 1.0; R[r, j] = -1.0
    return res.f_test(R)

# ---------------------------------------------------------------------
# 3. rolling 금리 베타 (시간변동성)
# ---------------------------------------------------------------------
def rolling_beta(ind_ret, mkt_ret, d_yield, window=504):
    # [대체값] window=504 : rolling 창(영업일, 약 2년). 1년은 252로 두시면 됩니다.
    df = pd.concat([ind_ret, mkt_ret, d_yield], axis=1).dropna()
    out = {}
    for end in range(window, len(df)):
        sub = df.iloc[end-window:end]
        b, _, _ = rate_beta(sub.iloc[:, 0], sub.iloc[:, 1], sub.iloc[:, 2])
        out[df.index[end]] = b
    return pd.Series(out, name="rolling_beta_r")

# ---------------------------------------------------------------------
# 4. H3 : 산업별 베타 vs 산업집계 특성 순위상관 (소표본 -> 탐색적)
# ---------------------------------------------------------------------
def rank_assoc(beta_by_ind, char_by_ind):
    rho, p = spearmanr(beta_by_ind.values, char_by_ind.reindex(beta_by_ind.index).values)
    return {"spearman_rho": float(rho), "p_value": float(p),
            "n_industries": int(len(beta_by_ind))}

# ---------------------------------------------------------------------
# 5. 검증 : 합성 데이터(산업마다 다른 진짜 베타)로 회수 확인
# ---------------------------------------------------------------------
if __name__ == "__main__":
    # [참고용 데모] 아래 데이터는 파이프라인이 어떻게 도는지 한 번 보시라고 만든
    #              '합성(가상) 데이터'입니다. 실제 분석 결과가 아니라 동작 예시이며,
    #              실데이터를 연결하면 동일한 함수로 진짜 결과가 나옵니다.
    print("[참고] 아래 수치는 합성(가상) 데이터로 만든 동작 예시입니다 — 실제 결과 아님.\n")
    rng = np.random.default_rng(1)
    n = 1000
    idx = pd.bdate_range("2016-01-04", periods=n)
    mkt = pd.Series(rng.normal(0, 1, n), index=idx)
    dY = pd.Series(rng.normal(0, 1, n), index=idx)
    true_beta = {"건설": 0.8, "금융": -0.6, "전기전자": 0.1, "화학": -0.2}

    rows = []
    for ind, b in true_beta.items():
        ret = 0.9*mkt + b*dY + pd.Series(rng.normal(0, 1, n), index=idx)
        est, se, p = rate_beta(ret, mkt, dY)
        rows.append((ind, b, est, p))
        long_part = pd.DataFrame({"industry": ind, "ret": ret.values,
                                  "mkt": mkt.values, "dY": dY.values,
                                  "date": idx}, index=idx)  # date: 날짜 클러스터 SE용
        rows_long = long_part if ind == "건설" else pd.concat([rows_long, long_part])

    print("=== 산업별 금리 베타 추정 (진짜 vs 추정) ===")
    print(pd.DataFrame(rows, columns=["산업", "진짜β", "추정β", "p"]).round(3).to_string(index=False))

    print("\n=== STEP4 결과표(데모): 산업별 금리 베타 전체 통계 ===")
    print(industry_rate_betas(rows_long.reset_index(drop=True),
                              ret_col="ret", mkt_col="mkt", yield_col="dY"
                              ).round(4).to_string(index=False))

    print("\n=== H1: 산업 간 베타 동일성 F-검정 ===")
    ft = cross_industry_Ftest(rows_long.reset_index(drop=True))
    print(f"  F={float(ft.fvalue):.2f}, p={float(ft.pvalue):.3e}  (p작으면 산업 간 차이 유의)")

    print("\n=== H3: 베타 vs 산업특성(가상 부채비율) 순위상관 ===")
    beta_s = pd.Series({r[0]: r[2] for r in rows})
    char = pd.Series({"건설": 0.7, "금융": 0.9, "전기전자": 0.3, "화학": 0.5})
    print("  ", rank_assoc(beta_s, char))
    print("  -> 산업별 베타 차이(F검정)와 특성 순위상관으로 H1~H3을 함께 본다")
