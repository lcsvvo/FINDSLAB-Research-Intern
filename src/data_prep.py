"""
src/data_prep.py — 01_data_preparation / 02_variable_generation 공통 함수

notebooks/01_data_preparation.ipynb 와
notebooks/02_variable_generation.ipynb 에서 쓰는 데이터 적재·정제·
병합·파생변수 생성 코드를 재사용 가능한 함수로 모아둔다.

계산 로직 자체는 이전 버전 노트북(00_data_preparation.ipynb, 01_eda_industry.ipynb)
코드를 그대로 옮긴 것이며, 계산 결과가 달라지지 않도록 값을 바꾸는 리팩토링은
하지 않았다. 유일한 차이는 산업/KOSPI/국고채 병합(raw 레벨)과 수익률·금리
변화분 파생변수 생성을 두 단계로 나눈 것뿐이며, 각 단계에서 동일한 pandas
연산(groupby().pct_change(), diff())을 그대로 사용하므로 최종 수치는 기존과 같다.

python -m src.data_prep 로 실행하면 01 -> 02 파이프라인 전체를 스크립트로
재현할 수 있다 (재현성 확인용; 분석 서사 자체는 notebooks/*.ipynb 참고).
"""
from __future__ import annotations

import unicodedata
import warnings
from pathlib import Path

import pandas as pd

import config


# ---------------------------------------------------------------------
# 공통 유틸
# ---------------------------------------------------------------------
#: 확장자별 읽기 방식 분기용. config.DATA_EXTENSIONS와 짝을 이룬다.
EXCEL_SUFFIXES = (".xlsx", ".xlsm", ".xls")


def read_table_safely(file_path):
    """원본 표 파일을 확장자에 맞게 읽는다.

    - .csv/.tsv: 인코딩이 파일마다 달라 여러 후보를 순서대로 시도한다
      (기존 read_csv_safely와 동일한 동작·동일한 순서 -> 결과 불변).
    - .xlsx/.xlsm/.xls: pandas.read_excel로 읽는다. 팀원마다 원본을 엑셀로
      받아두는 경우가 있어 csv 전용 가정을 두지 않는다.
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix in EXCEL_SUFFIXES:
        try:
            return pd.read_excel(path)
        except ImportError as exc:  # openpyxl / xlrd 미설치
            raise ImportError(
                f"엑셀 원본({path.name})을 읽으려면 관련 패키지가 필요합니다. "
                f"저장소 루트에서 `pip install -r requirements.txt` 를 실행하세요."
            ) from exc

    encodings = ["utf-8-sig", "cp949", "euc-kr", "utf-8"]
    for enc in encodings:
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"파일을 읽지 못했습니다: {path}")


#: [하위호환] 기존 호출부/문서가 참조하는 이름. 동작은 read_table_safely와 같다.
read_csv_safely = read_table_safely


# ---------------------------------------------------------------------
# 00_data_preparation : 데이터 불러오기 / 날짜 형식 통일 / 거래일 기준 병합
# ---------------------------------------------------------------------
def load_industry_and_kospi():
    """산업별 + KOSPI 원본 지수(csv)를 읽어 하나로 합친 뒤, 날짜 정리·숫자형 변환·
    결측 제거·중복 제거·정렬까지 수행하고 KOSPI/산업을 분리해 반환한다.
    (기존 00_data_preparation.ipynb 1~2번째 셀 로직과 동일. 산업별/KOSPI
    일별 수익률(pct_change) 계산만 01_variable_generation 단계로 옮겼다.)
    """
    all_data = []

    for industry_name, folder in config.get_industry_source_folders():
        # 확장자(csv/xlsx/xls)와 파일명은 config가 관리한다. 여기서 "*.csv"로
        # 하드코딩하면 엑셀로 원본을 받아둔 팀원의 파일이 조용히 누락된다.
        source_files = config.iter_data_files(folder)
        if not source_files:
            warnings.warn(f"원본 파일이 없어 건너뜁니다: {industry_name}", RuntimeWarning, stacklevel=2)
            continue

        for file in source_files:
            df = read_table_safely(file)
            df.columns = df.columns.str.strip()

            missing = [c for c in ("Date", "Close") if c not in df.columns]
            if missing:
                raise ValueError(
                    f"{file.name}: 필요한 컬럼이 없습니다 {missing}. "
                    f"실제 컬럼: {list(df.columns)}"
                )

            temp = df[["Date", "Close"]].copy()
            temp = temp.rename(columns={"Date": "date", "Close": "industry_index"})
            temp["industry"] = industry_name
            temp["source_file"] = file.name
            all_data.append(temp)

    industry_all = pd.concat(all_data, ignore_index=True)

    # 날짜 정리
    industry_all["date"] = pd.to_datetime(industry_all["date"], errors="coerce")

    # 숫자형 정리
    industry_all["industry_index"] = (
        industry_all["industry_index"].astype(str).str.replace(",", "", regex=False)
    )
    industry_all["industry_index"] = pd.to_numeric(industry_all["industry_index"], errors="coerce")

    # 결측 제거
    industry_all = industry_all.dropna(subset=["date", "industry_index"])

    # 중복 제거
    industry_all = industry_all.drop_duplicates(subset=["date", "industry"], keep="first")

    # 날짜순 정렬
    industry_all = industry_all.sort_values(["industry", "date"]).reset_index(drop=True)

    # 한글 자모 깨짐 방지: 유니코드 정규화
    industry_all["industry"] = industry_all["industry"].apply(lambda x: unicodedata.normalize("NFC", str(x)))

    # =========================
    # KOSPI 시장지수 분리
    # =========================
    kospi_daily = industry_all[industry_all["industry"] == "KOSPI"].copy()
    kospi_daily = kospi_daily.rename(columns={"industry_index": "kospi_index"})
    kospi_daily = kospi_daily[["date", "kospi_index"]]
    kospi_daily = kospi_daily.sort_values("date").reset_index(drop=True)

    # =========================
    # 산업별 지수만 남기기
    # =========================
    industry_daily = industry_all[industry_all["industry"] != "KOSPI"].copy()

    # 산업명 정리
    industry_daily["industry"] = industry_daily["industry"].str.replace("KOSPI ", "", regex=False)

    # 금속 -> 철강금속으로 통일
    industry_daily["industry"] = industry_daily["industry"].replace({"금속": "철강금속"})

    industry_daily = industry_daily[["date", "industry", "industry_index", "source_file"]]
    industry_daily = industry_daily.sort_values(["industry", "date"]).reset_index(drop=True)

    return industry_daily, kospi_daily


def load_yields():
    """국고채 3년·10년 원본(ECOS 형식 wide 포맷)을 읽어 long 포맷(date, y3, y10)으로
    변환한다. (기존 노트북 3~4번째 셀 로직과 동일. 금리 변화분·장단기 금리차 계산은
    01_variable_generation 단계로 옮겼다.)
    """
    if not Path(config.RAW_YIELD_FILE).exists():
        raise FileNotFoundError(
            f"국고채 원본을 찾지 못했습니다: {config.RAW_YIELD_FILE}\n"
            "config.describe() 로 탐색 결과를 확인하세요."
        )

    raw_yield = read_table_safely(config.RAW_YIELD_FILE)
    raw_yield.columns = raw_yield.columns.str.strip()

    date_cols = []
    for col in raw_yield.columns:
        try:
            pd.to_datetime(col)
            date_cols.append(col)
        except Exception:
            pass

    if "계정항목" in raw_yield.columns:
        account_col = "계정항목"
    else:
        possible_cols = [c for c in raw_yield.columns if "항목" in c]
        account_col = possible_cols[0]

    yields_daily = raw_yield.set_index(account_col)[date_cols].T
    yields_daily = yields_daily.rename(columns={"국고채(3년)": "y3", "국고채(10년)": "y10"})
    yields_daily = yields_daily.reset_index().rename(columns={"index": "date"})
    yields_daily["date"] = pd.to_datetime(yields_daily["date"])

    for col in ["y3", "y10"]:
        yields_daily[col] = yields_daily[col].astype(str).str.replace(",", "", regex=False)
        yields_daily[col] = pd.to_numeric(yields_daily[col], errors="coerce")

    yields_daily = yields_daily.sort_values("date").reset_index(drop=True)
    yields_daily = yields_daily[["date", "y3", "y10"]]
    return yields_daily


def build_raw_panel(industry_daily, kospi_daily, yields_daily):
    """산업지수 + KOSPI + 국고채 금리(원본 레벨)를 날짜 기준으로 병합한다.
    (기존 노트북 7~8번째 셀의 병합 로직과 동일. industry_return 등 파생변수는
    01_variable_generation에서 만든다.)
    """
    panel = industry_daily.merge(kospi_daily, on="date", how="left")
    panel = panel.merge(yields_daily, on="date", how="left")
    panel = panel.sort_values(["date", "industry"]).reset_index(drop=True)
    panel = panel[["date", "industry", "industry_index", "kospi_index", "y3", "y10", "source_file"]]
    return panel


def check_missing(panel: pd.DataFrame) -> dict:
    """결측치 확인 (기존 00_data_preparation.ipynb 마지막 점검 셀과 동일한 점검 항목)."""
    return {
        "shape": panel.shape,
        "columns": panel.columns.tolist(),
        "industries": sorted(panel["industry"].unique().tolist()),
        "date_range": (panel["date"].min(), panel["date"].max()),
        "n_missing": panel.isna().sum().to_dict(),
    }


def save_raw_panel(panel: pd.DataFrame, filename: str = "industry_rate_panel_raw.csv") -> Path:
    out = config.PROCESSED_DIR / filename
    panel.to_csv(out, index=False, encoding="utf-8-sig")
    return out


# ---------------------------------------------------------------------
# 01_variable_generation : 파생변수 생성
# ---------------------------------------------------------------------
def add_return_and_rate_change_vars(panel, kospi_daily, yields_daily):
    """00_data_preparation에서 저장한 원본 레벨 데이터로부터 아래 6개 파생변수를
    생성한다.
      - industry_return : 산업별 일별 수익률
      - kospi_return     : KOSPI 일별 수익률
      - d_y3             : 국고채 3년 금리 변화분
      - d_y10            : 국고채 10년 금리 변화분
      - term_spread      : 장단기 금리차 (y10 - y3)
      - d_term_spread    : 장단기 금리차 변화분

    주의: kospi_return / d_y3 / d_y10 / term_spread / d_term_spread는 반드시
    KOSPI·금리 고유의 날짜 시퀀스(kospi_daily, yields_daily; 산업 거래일과 완전히
    같지는 않다)에서 pct_change()/diff()를 계산한 뒤 병합해야 기존 노트북과
    동일한 수치가 나온다. 이미 산업 패널과 날짜 기준으로 병합한 뒤에 diff를
    다시 계산하면, 병합 과정에서 빠진 날짜 때문에 인접한 날짜가 바뀌어 값이
    달라진다 (예: 2017-12-29는 국고채 금리 데이터에는 있지만 산업 데이터에는
    없어, 병합 후 계산하면 국고채 diff가 실제와 달라짐 -> 반드시 병합 전
    각자의 시계열에서 계산한다).
    """
    df = panel.copy()

    # 산업별 일별 수익률 (산업 패널 자체의 날짜 시퀀스 사용 -> 병합 영향 없음)
    df = df.sort_values(["industry", "date"]).reset_index(drop=True)
    df["industry_return"] = df.groupby("industry")["industry_index"].pct_change()

    # KOSPI 고유의 날짜 시퀀스에서 수익률 계산
    kospi_daily = kospi_daily.sort_values("date").reset_index(drop=True).copy()
    kospi_daily["kospi_return"] = kospi_daily["kospi_index"].pct_change()

    # 국고채 고유의 날짜 시퀀스에서 금리 변화분 · 장단기 금리차 계산
    yields_daily = yields_daily.sort_values("date").reset_index(drop=True).copy()
    yields_daily["d_y3"] = yields_daily["y3"].diff()
    yields_daily["d_y10"] = yields_daily["y10"].diff()
    yields_daily["term_spread"] = yields_daily["y10"] - yields_daily["y3"]
    yields_daily["d_term_spread"] = yields_daily["term_spread"].diff()

    df = df.merge(kospi_daily[["date", "kospi_return"]], on="date", how="left")
    df = df.merge(
        yields_daily[["date", "d_y3", "d_y10", "term_spread", "d_term_spread"]],
        on="date",
        how="left",
    )

    df = df.sort_values(["date", "industry"]).reset_index(drop=True)
    df = df[
        [
            "date",
            "industry",
            "industry_index",
            "industry_return",
            "kospi_index",
            "kospi_return",
            "y3",
            "d_y3",
            "y10",
            "d_y10",
            "term_spread",
            "d_term_spread",
        ]
    ]
    return df


def save_final_panel(panel: pd.DataFrame, filename: str = "industry_rate_panel_daily.csv") -> Path:
    out = config.PROCESSED_DIR / filename
    panel.to_csv(out, index=False, encoding="utf-8-sig")
    return out


# ---------------------------------------------------------------------
# 스크립트 실행 (00 -> 01 파이프라인 재현)
# ---------------------------------------------------------------------
def run_data_preparation():
    """00_data_preparation 단계 전체 실행."""
    industry_daily, kospi_daily = load_industry_and_kospi()
    yields_daily = load_yields()

    industry_daily.to_csv(config.INTERIM_DIR / "industry_daily_clean.csv", index=False, encoding="utf-8-sig")
    kospi_daily.to_csv(config.INTERIM_DIR / "kospi_daily.csv", index=False, encoding="utf-8-sig")
    yields_daily.to_csv(config.INTERIM_DIR / "yields_daily.csv", index=False, encoding="utf-8-sig")

    raw_panel = build_raw_panel(industry_daily, kospi_daily, yields_daily)
    print("[00] 결측치 확인:", check_missing(raw_panel))
    save_raw_panel(raw_panel)
    return raw_panel, kospi_daily, yields_daily


def run_variable_generation(raw_panel=None, kospi_daily=None, yields_daily=None):
    """01_variable_generation 단계 전체 실행. 00에서 저장한 데이터(raw panel +
    kospi_daily/yields_daily)를 불러와 파생변수를 생성한다."""
    if raw_panel is None:
        raw_panel = pd.read_csv(config.PROCESSED_DIR / "industry_rate_panel_raw.csv", encoding="utf-8-sig")
        raw_panel["date"] = pd.to_datetime(raw_panel["date"])
    if kospi_daily is None:
        kospi_daily = pd.read_csv(config.INTERIM_DIR / "kospi_daily.csv", encoding="utf-8-sig")
        kospi_daily["date"] = pd.to_datetime(kospi_daily["date"])
    if yields_daily is None:
        yields_daily = pd.read_csv(config.INTERIM_DIR / "yields_daily.csv", encoding="utf-8-sig")
        yields_daily["date"] = pd.to_datetime(yields_daily["date"])

    final_panel = add_return_and_rate_change_vars(raw_panel, kospi_daily, yields_daily)
    save_final_panel(final_panel)
    return final_panel


if __name__ == "__main__":
    _raw_panel, _kospi_daily, _yields_daily = run_data_preparation()
    _final_panel = run_variable_generation(_raw_panel, _kospi_daily, _yields_daily)
    print("[01] 최종 패널 크기:", _final_panel.shape)
