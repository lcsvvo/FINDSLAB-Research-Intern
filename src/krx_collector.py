"""[DEPRECATED — 2026-08-23] Safe H3 collection using only the official KRX Open API.

이 모듈(A안: 공식 KRX API만으로 PBR·배당수익률·구성종목 확보)은 실제로는 KRX 화면
다운로드 파일(krx_valuation_YYYY.csv 등)이 끝내 확보되지 않아 pbr·dividend_yield를
한 건도 채우지 못하고 중단되었다(data/interim/firm/krx/krx_validation_report.csv 참고:
pbr_available/dividend_yield_available 모두 FAIL, 639건 결측). 현재 09/10 노트북은
DART OpenAPI 기반 수집(fnlttSinglAcntAll, alotMatter)으로 전환되어 이 모듈을 전혀
참조하지 않는다. 과거 설계 기록·비교용으로만 남겨두며, 신규 실행/유지보수 대상이 아니다.

Official API scope (checked 2026-08-18): KOSPI daily trading data includes
market cap, but PBR/dividend yield/index constituents are not offered. KRX's
2026-06-01 notice prohibits unofficial libraries for unavailable datasets.
Those three inputs are therefore loaded from KRX screen-download files while
market cap is collected with the official AUTH_KEY API.

Safety rules: isolate request failures, append a failure ledger, preserve raw
responses, checkpoint every completed year, and skip completed checkpoints.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Callable, Iterable

import pandas as pd
import requests

INDUSTRIES = ("건설업", "금융업", "운수장비", "의약품", "전기전자", "철강금속", "화학")
OFFICIAL_BASE_URL = "https://data-dbg.krx.co.kr/svc/apis"
DAILY_TRADING_ENDPOINT = "sto/stk_bydd_trd"
CONSTITUENT_COLUMNS = ["industry", "company_name", "stock_code", "snapshot_date"]
YEARLY_COLUMNS = [
    "industry", "company_name", "stock_code", "year", "trade_date",
    "market_cap", "pbr", "dividend_yield",
]
ERROR_COLUMNS = [
    "collected_at", "stock_code", "year", "step", "request_date",
    "attempt", "error_type", "error_msg",
]


class KRXCollectionError(RuntimeError):
    def __init__(self, message: str, payload: object | None = None) -> None:
        super().__init__(message)
        self.payload = payload


class KRXAuthenticationError(KRXCollectionError):
    pass


@dataclass(frozen=True)
class CollectionPaths:
    raw_dir: Path
    interim_dir: Path
    manual_dir: Path

    @property
    def errors(self) -> Path:
        return self.interim_dir / "krx_collection_errors.csv"

    @property
    def constituents(self) -> Path:
        return self.interim_dir / "industry_constituents.csv"

    @property
    def yearly(self) -> Path:
        return self.interim_dir / "krx_firm_yearly.csv"

    @property
    def validation(self) -> Path:
        return self.interim_dir / "krx_validation_report.csv"


def _atomic_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(tmp, index=False, encoding="utf-8-sig")
    tmp.replace(path)


def _read_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        last: Exception | None = None
        for encoding in ("utf-8-sig", "cp949", "utf-8"):
            try:
                return pd.read_csv(path, dtype=str, encoding=encoding)
            except UnicodeDecodeError as exc:
                last = exc
        assert last is not None
        raise last
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path, dtype=str)
    raise ValueError(f"지원하지 않는 파일 형식: {path}")


def _label(value: object) -> str:
    return "".join(ch for ch in str(value).strip().lower() if ch.isalnum() or "가" <= ch <= "힣")


def _column(frame: pd.DataFrame, aliases: Iterable[str]) -> str:
    lookup = {_label(c): str(c) for c in frame.columns}
    for alias in aliases:
        if _label(alias) in lookup:
            return lookup[_label(alias)]
    raise KeyError(f"필수 컬럼 없음: {list(aliases)} / 실제={list(frame.columns)}")


def _number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(",", "", regex=False).str.strip(), errors="coerce")


def _code(series: pd.Series) -> pd.Series:
    return series.astype(str).str.extract(r"(\d{6})", expand=False).str.zfill(6)


def _now() -> str:
    return pd.Timestamp.now(tz="Asia/Seoul").isoformat()


def _error(*, year: int | str, step: str, request_date: str, attempt: int,
           exc: Exception, stock_code: str = "") -> dict[str, object]:
    return {
        "collected_at": _now(), "stock_code": stock_code, "year": year,
        "step": step, "request_date": request_date, "attempt": attempt,
        "error_type": type(exc).__name__, "error_msg": str(exc)[:1000],
    }


def _append_errors(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    new = pd.DataFrame(rows, columns=ERROR_COLUMNS)
    if path.exists():
        old = pd.read_csv(path, dtype=str)
        new = pd.concat([old, new], ignore_index=True)
    keys = ["stock_code", "year", "step", "request_date", "attempt", "error_type", "error_msg"]
    _atomic_csv(new.drop_duplicates(keys, keep="last"), path)


class OfficialKRXClient:
    """Official KRX GET client. The secret is sent only in the AUTH_KEY header."""

    def __init__(self, api_key: str, *, session: requests.Session | None = None,
                 timeout: float = 30, max_retries: int = 2, pause: float = 1.0,
                 sleep_fn: Callable[[float], None] = time.sleep) -> None:
        if not api_key or not api_key.strip():
            raise KRXAuthenticationError("KRX_API_KEY가 없습니다. 프로젝트 .env에 설정하세요.")
        self.api_key = api_key.strip()
        self.session = session or requests.Session()
        self.timeout = timeout
        self.max_retries = max_retries
        self.pause = pause
        self.sleep_fn = sleep_fn

    def get(self, endpoint: str, params: dict[str, str]) -> tuple[dict[str, object], int, str]:
        url = f"{OFFICIAL_BASE_URL}/{endpoint.lstrip('/')}"
        last: Exception | None = None
        for attempt in range(1, self.max_retries + 2):
            try:
                response = self.session.get(
                    url, headers={"AUTH_KEY": self.api_key, "Accept": "application/json"},
                    params=params, timeout=self.timeout,
                )
                try:
                    payload = response.json()
                except ValueError as exc:
                    raise KRXCollectionError(
                        f"비JSON 응답(status={response.status_code}, body={response.text[:120]!r})",
                        {"http_status": response.status_code, "raw_text": response.text},
                    ) from exc
                code = str(payload.get("respCode", response.status_code))
                if response.status_code in {401, 403} or code in {"401", "403"}:
                    raise KRXAuthenticationError(
                        f"KRX 인증/이용승인 실패: {payload.get('respMsg', response.status_code)}. "
                        "포털에서 이 API의 이용신청 승인을 확인하세요.", payload,
                    )
                if response.status_code >= 400:
                    raise KRXCollectionError(
                        f"KRX HTTP 오류 {response.status_code}: {payload.get('respMsg')}", payload
                    )
                if "respCode" in payload and code not in {"0", "000", "200", str(response.status_code)}:
                    raise KRXCollectionError(f"KRX API 오류 {code}: {payload.get('respMsg')}", payload)
                if self.pause:
                    self.sleep_fn(self.pause)
                return payload, attempt, response.text
            except KRXAuthenticationError:
                raise
            except (requests.RequestException, KRXCollectionError) as exc:
                last = exc
                if attempt <= self.max_retries:
                    self.sleep_fn(self.pause * attempt)
        assert last is not None
        if isinstance(last, KRXCollectionError):
            raise last
        raise KRXCollectionError(str(last)) from last


def _rows(payload: dict[str, object]) -> list[dict[str, object]]:
    for key, value in payload.items():
        if key.lower().startswith("outblock") and isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]
    return []


def _normalize_market_cap(rows: list[dict[str, object]], year: int, trade_date: str) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    missing = {"ISU_CD", "ISU_NM", "MKTCAP"} - set(frame.columns)
    if missing:
        raise KRXCollectionError(f"공식 API 응답 컬럼 누락: {sorted(missing)}")
    out = pd.DataFrame({
        "stock_code": _code(frame["ISU_CD"]),
        "company_name_official": frame["ISU_NM"].astype(str).str.strip(),
        "year": year, "trade_date": trade_date, "market_cap": _number(frame["MKTCAP"]),
    })
    return out.dropna(subset=["stock_code"]).drop_duplicates("stock_code", keep="last")


def _cached_year(raw_dir: Path, year: int) -> pd.DataFrame | None:
    completed = sorted(raw_dir.glob(f"market_cap_{year}_*.csv"), reverse=True)
    return pd.read_csv(completed[0], dtype={"stock_code": str}) if completed else None


def collect_official_market_caps(years: Iterable[int], *, paths: CollectionPaths,
                                 client: OfficialKRXClient, force: bool = False) -> pd.DataFrame:
    """Checkpoint each year; a date failure never discards other completed years."""
    parts: list[pd.DataFrame] = []
    for year_value in years:
        year = int(year_value)
        cached = None if force else _cached_year(paths.raw_dir, year)
        if cached is not None:
            parts.append(cached)
            continue
        year_errors: list[dict[str, object]] = []
        completed = False
        for offset in range(12):
            request_date = (date(year, 12, 31) - timedelta(days=offset)).strftime("%Y%m%d")
            attempt = 0
            try:
                payload, attempt, raw_text = client.get(DAILY_TRADING_ENDPOINT, {"basDd": request_date})
                # Raw response is written before parsing so parser fixes never require re-download.
                _atomic_text(raw_text,
                             paths.raw_dir / f"stk_bydd_trd_{request_date}.json")
                rows = _rows(payload)
                if not rows:
                    continue
                normalized = _normalize_market_cap(rows, year, request_date)
                _atomic_csv(normalized, paths.raw_dir / f"market_cap_{year}_{request_date}.csv")
                parts.append(normalized)
                completed = True
                break
            except KRXAuthenticationError as exc:
                if exc.payload is not None:
                    _atomic_text(json.dumps(exc.payload, ensure_ascii=False, indent=2),
                                 paths.raw_dir / f"stk_bydd_trd_{request_date}_error.json")
                year_errors.append(_error(year=year, step="official_market_cap", request_date=request_date,
                                          attempt=max(attempt, 1), exc=exc))
                _append_errors(paths.errors, year_errors)
                raise
            except Exception as exc:
                if isinstance(exc, KRXCollectionError) and exc.payload is not None:
                    _atomic_text(json.dumps(exc.payload, ensure_ascii=False, indent=2),
                                 paths.raw_dir / f"stk_bydd_trd_{request_date}_error.json")
                year_errors.append(_error(year=year, step="official_market_cap", request_date=request_date,
                                          attempt=attempt, exc=exc))
                continue
        if not completed:
            exc = KRXCollectionError("12월 말 12일 범위에서 유효한 거래일 데이터를 찾지 못함")
            year_errors.append(_error(year=year, step="year_incomplete", request_date="", attempt=0, exc=exc))
        _append_errors(paths.errors, year_errors)
    if not parts:
        return pd.DataFrame(columns=["stock_code", "company_name_official", "year", "trade_date", "market_cap"])
    return pd.concat(parts, ignore_index=True).drop_duplicates(["stock_code", "year"], keep="last")


def _manual_file(folder: Path, stems: Iterable[str]) -> Path | None:
    for stem in stems:
        for suffix in (".csv", ".xlsx", ".xls"):
            candidate = folder / f"{stem}{suffix}"
            if candidate.exists():
                return candidate
    return None


def load_manual_constituents(folder: Path, snapshot_year: int) -> pd.DataFrame:
    path = _manual_file(folder, ["industry_constituents", f"industry_constituents_{snapshot_year}"])
    if path is None:
        raise FileNotFoundError(
            f"KRX 화면 다운로드 구성종목 파일 없음: {folder}/industry_constituents.[csv|xlsx]"
        )
    raw = _read_table(path)
    ic = _column(raw, ["industry", "산업", "업종", "업종명", "지수명"])
    cc = _column(raw, ["stock_code", "종목코드", "단축코드", "ISU_SRT_CD"])
    nc = _column(raw, ["company_name", "종목명", "회사명", "ISU_NM"])
    out = pd.DataFrame({
        "industry": raw[ic].astype(str).str.strip(), "company_name": raw[nc].astype(str).str.strip(),
        "stock_code": _code(raw[cc]), "snapshot_date": str(snapshot_year),
    })
    out = out[out["industry"].isin(INDUSTRIES)].dropna(subset=["stock_code"])
    multi = out.groupby("stock_code")["industry"].nunique()
    if (multi > 1).any():
        raise KRXCollectionError(f"복수 산업 배정 종목: {multi[multi > 1].index.tolist()[:10]}")
    return out.drop_duplicates(["industry", "stock_code"]).sort_values(["industry", "stock_code"])


def load_manual_valuations(folder: Path, years: Iterable[int]) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    for year_value in years:
        year = int(year_value)
        path = _manual_file(folder, [f"krx_valuation_{year}", f"valuation_{year}"])
        if path is None:
            continue
        raw = _read_table(path)
        cc = _column(raw, ["stock_code", "종목코드", "단축코드", "ISU_SRT_CD"])
        pc = _column(raw, ["pbr", "PBR", "주가순자산비율"])
        dc = _column(raw, ["dividend_yield", "배당수익률", "DIV"])
        out = pd.DataFrame({
            "stock_code": _code(raw[cc]), "year": year,
            "pbr": _number(raw[pc]), "dividend_yield": _number(raw[dc]),
        })
        parts.append(out.dropna(subset=["stock_code"]).drop_duplicates("stock_code", keep="last"))
    if not parts:
        return pd.DataFrame(columns=["stock_code", "year", "pbr", "dividend_yield"])
    return pd.concat(parts, ignore_index=True)


def validate_outputs(constituents: pd.DataFrame, yearly: pd.DataFrame,
                     years: Iterable[int]) -> pd.DataFrame:
    expected_years = set(map(int, years))
    got_years = set(pd.to_numeric(yearly.get("year", pd.Series(dtype=float)), errors="coerce").dropna().astype(int))
    got_industries = set(constituents.get("industry", pd.Series(dtype=str)).dropna())
    checks: list[tuple[str, bool, object]] = [
        ("industries_complete", got_industries == set(INDUSTRIES), sorted(set(INDUSTRIES) - got_industries)),
        ("years_complete", got_years == expected_years, sorted(expected_years - got_years)),
        ("constituent_key_unique", not constituents.duplicated(["industry", "stock_code"]).any(),
         int(constituents.duplicated(["industry", "stock_code"]).sum())),
        ("firm_year_key_unique", not yearly.duplicated(["stock_code", "year"]).any(),
         int(yearly.duplicated(["stock_code", "year"]).sum())),
    ]
    for col in ("market_cap", "pbr", "dividend_yield"):
        missing = int(yearly[col].isna().sum()) if col in yearly else len(yearly)
        checks.append((f"{col}_available", len(yearly) > 0 and missing < len(yearly), missing))
    return pd.DataFrame(checks, columns=["check", "passed", "detail"])


def collect_krx_h3(*, start_year: int = 2016, end_year: int = 2025,
                   snapshot_year: int = 2025, raw_dir: Path, interim_dir: Path,
                   manual_dir: Path | None = None, api_key: str | None = None,
                   client: OfficialKRXClient | None = None,
                   force: bool = False) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if start_year > end_year:
        raise ValueError("start_year must be <= end_year")
    paths = CollectionPaths(Path(raw_dir), Path(interim_dir),
                            Path(manual_dir or Path(raw_dir).parent / "krx_manual"))
    for folder in (paths.raw_dir, paths.interim_dir, paths.manual_dir):
        folder.mkdir(parents=True, exist_ok=True)
    years = list(range(start_year, end_year + 1))
    try:
        constituents = load_manual_constituents(paths.manual_dir, snapshot_year)
    except Exception as exc:
        _append_errors(paths.errors, [_error(year=snapshot_year, step="manual_constituents",
                                             request_date="", attempt=0, exc=exc)])
        raise
    valuations = load_manual_valuations(paths.manual_dir, years)
    valuation_years = set(pd.to_numeric(valuations.get("year", pd.Series(dtype=float)),
                                        errors="coerce").dropna().astype(int))
    missing_valuation_years = set(years) - valuation_years
    if missing_valuation_years:
        _append_errors(paths.errors, [
            _error(year=year, step="manual_valuation", request_date="", attempt=0,
                   exc=FileNotFoundError(f"krx_valuation_{year}.[csv|xlsx] 없음"))
            for year in sorted(missing_valuation_years)
        ])
    client = client or OfficialKRXClient(api_key or os.getenv("KRX_API_KEY", ""))
    market_caps = collect_official_market_caps(years, paths=paths, client=client, force=force)

    identity = constituents[["industry", "company_name", "stock_code"]]
    official = identity.merge(market_caps, on="stock_code", how="left", validate="one_to_many")
    yearly = official.merge(valuations, on=["stock_code", "year"], how="left", validate="one_to_one")
    yearly = yearly[YEARLY_COLUMNS].sort_values(["industry", "stock_code", "year"])
    _atomic_csv(constituents[CONSTITUENT_COLUMNS], paths.constituents)
    _atomic_csv(yearly, paths.yearly)
    validation = validate_outputs(constituents, yearly, years)
    _atomic_csv(validation, paths.validation)
    return constituents, yearly, validation


def main() -> None:
    parser = argparse.ArgumentParser(description="Safe official KRX H3 collector")
    parser.add_argument("--start-year", type=int, default=2016)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument("--snapshot-year", type=int, default=2025)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    import config
    from dotenv import load_dotenv
    load_dotenv(config.PROJECT_ROOT / ".env")
    con, yearly, checks = collect_krx_h3(
        start_year=args.start_year, end_year=args.end_year, snapshot_year=args.snapshot_year,
        raw_dir=config.KRX_RAW_DIR, interim_dir=config.KRX_INTERIM_DIR,
        manual_dir=config.KRX_MANUAL_DIR, force=args.force,
    )
    print(f"[KRX 완료] 구성종목 {len(con)}행 · firm-year {len(yearly)}행")
    print(checks.to_string(index=False))
    if not bool(checks["passed"].all()):
        raise SystemExit("검증 미통과: validation과 오류 CSV를 확인하세요.")


if __name__ == "__main__":
    main()
