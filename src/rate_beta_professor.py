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

# #####################################################################
# [ 2 ] Robustness — 산업 간 차이 F검정 · rolling · 순위상관
# #####################################################################

# ---------------------------------------------------------------------
# 2. 산업 간 차이 검정 (H1) : 산업더미 x 금리변화 교차항의 동일성 F-검정
# ---------------------------------------------------------------------
def cross_industry_Ftest(long_df, hac_lags=5):
    """
    long_df : columns = [industry, ret, mkt, dY]  (여러 산업을 쌓은 long 형식)
    H0 : 모든 산업의 금리 베타(교차항 계수)가 같다.
    """
    d = long_df.dropna().copy()
    dummies = pd.get_dummies(d["industry"], prefix="ind", dtype=float)
    inter = dummies.mul(d["dY"], axis=0).add_prefix("dY_")        # 산업별 금리 교차항
    mkt_inter = dummies.mul(d["mkt"], axis=0).add_prefix("mkt_")  # 산업별 시장 통제
    X = pd.concat([dummies, mkt_inter, inter], axis=1)
    res = sm.OLS(d["ret"].values, X.values).fit(
        cov_type="HAC", cov_kwds={"maxlags": hac_lags})
    names = list(X.columns)
    dY_idx = [i for i, c in enumerate(names) if c.startswith("dY_")]
    # 교차항들이 서로 같다는 제약(첫 항 기준 차이=0)을 묶어 F-검정
    R = np.zeros((len(dY_idx)-1, len(names)))
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
                                  "mkt": mkt.values, "dY": dY.values}, index=idx)
        rows_long = long_part if ind == "건설" else pd.concat([rows_long, long_part])

    print("=== 산업별 금리 베타 추정 (진짜 vs 추정) ===")
    print(pd.DataFrame(rows, columns=["산업", "진짜β", "추정β", "p"]).round(3).to_string(index=False))

    print("\n=== H1: 산업 간 베타 동일성 F-검정 ===")
    ft = cross_industry_Ftest(rows_long.reset_index(drop=True))
    print(f"  F={float(ft.fvalue):.2f}, p={float(ft.pvalue):.3e}  (p작으면 산업 간 차이 유의)")

    print("\n=== H3: 베타 vs 산업특성(가상 부채비율) 순위상관 ===")
    beta_s = pd.Series({r[0]: r[2] for r in rows})
    char = pd.Series({"건설": 0.7, "금융": 0.9, "전기전자": 0.3, "화학": 0.5})
    print("  ", rank_assoc(beta_s, char))
    print("  -> 산업별 베타 차이(F검정)와 특성 순위상관으로 H1~H3을 함께 본다")
