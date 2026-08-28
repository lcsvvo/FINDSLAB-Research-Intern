"""
config.py — 프로젝트 공통 환경설정 (경로 단일 관리)

이 모듈은 분석 로직을 담지 않는다. notebooks/, src/ 가 동일한 경로·동일한
산출물에 접근하도록 "경로만" 정의한다.

설계 원칙
1. PROJECT_ROOT는 이 파일의 위치(__file__)에서 결정한다.
   - Path.cwd()에 의존하지 않는다. Jupyter/VS Code에서 cwd가 노트북 폴더나
     사용자 홈으로 잡혀도 결과가 달라지지 않는다.
   - 사용자 PC의 특정 경로(Desktop, OneDrive, C:\\Users ...)를 전혀 참조하지
     않으므로, 저장소를 어느 위치에 두든 팀원 모두 동일하게 동작한다.
2. 파일 탐색은 반드시 PROJECT_ROOT 하위로 제한한다.
   - 프로젝트 밖(예: 다른 프로젝트의 ecos_yields.csv)이 잡히는 사고를 구조적으로
     차단한다. 탐색 루트가 프로젝트 밖이면 예외를 던진다.
3. 파일명·폴더명을 하드코딩하지 않는다.
   - 표준 경로가 있으면 그대로 쓰고, 없으면 별칭(alias) 기반으로 탐색한다.
   - .csv / .xlsx / .xls 를 모두 인식하고, 영문/국문/KOSPI 접두 폴더명을 모두
     같은 산업으로 인식한다. 팀원별 명명 차이를 config 한 곳에서 흡수한다.
4. 어떤 파일이 선택됐는지 추적 가능해야 한다.
   - 자동 탐색 결과는 DISCOVERY_LOG에 기록되고 describe()로 확인한다.
   - 재현성 검증 시 "무엇을 읽었는지"를 반드시 확인할 수 있어야 하기 때문이다.

Notebook 사용법:
    import config          # 경로는 전부 config에서만 가져온다
    config.describe()      # 실제로 어떤 경로/파일이 잡혔는지 점검

`import config`가 실패한다면 저장소 루트에서 한 번만 실행한다:
    pip install -e .
"""
from __future__ import annotations

import warnings
from pathlib import Path
from typing import Iterable, Sequence

# =====================================================================
# 1. PROJECT_ROOT — 이 파일의 위치로 고정 (cwd 비의존)
# =====================================================================
#: 저장소 루트를 식별하는 마커. 존재 검증용이며 탐색 기준으로는 쓰지 않는다.
ROOT_MARKERS: tuple[str, ...] = ("requirements.txt", ".git", "src", "notebooks")

PROJECT_ROOT: Path = Path(__file__).resolve().parent

if not any((PROJECT_ROOT / m).exists() for m in ROOT_MARKERS):
    warnings.warn(
        f"PROJECT_ROOT({PROJECT_ROOT})에서 {ROOT_MARKERS} 중 어떤 마커도 찾지 못했습니다. "
        "config.py가 저장소 루트에 있는지 확인하세요.",
        RuntimeWarning,
        stacklevel=2,
    )


def find_project_root(marker: str = "requirements.txt") -> Path:
    """[하위호환] 항상 PROJECT_ROOT를 반환한다.

    이전 구현은 Path.cwd()에서 위로 올라가며 marker를 찾았고, cwd가 저장소 밖일
    때 잘못된 루트를 반환했다. 현재는 __file__ 기준으로 결정되므로 marker 인자는
    무시되며, 호출부 수정 없이 동작만 안전해진다.
    """
    return PROJECT_ROOT


# =====================================================================
# 2. 고정 디렉터리 (기존 변수명 유지)
# =====================================================================
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"

RESULTS_ROOT = PROJECT_ROOT / "results"
RESULTS_DIR = RESULTS_ROOT / "EDA"
FIGDIR = RESULTS_DIR / "figures"
TABDIR = RESULTS_DIR / "tables"

# results/ 는 가설 기준(Baseline/H1/H2/H3)으로 관리한다. 폴더명은 바뀌어도
# notebook 번호(04, 06, 07 ...)는 분석 수행 순서를 의미하므로 연결하지 않는다.
BASELINE_DIR = RESULTS_ROOT / "Baseline_industry_beta"   # 04_rate_beta_estimation
H1_DIR = RESULTS_ROOT / "H1_yield_curve"                 # 06_yield_curve_exposure (모형 B)
H2_DIR = RESULTS_ROOT / "H2_asymmetry_regime"            # 07_asymmetric_rate_response (모형 C)
H3_DIR = RESULTS_ROOT / "H3_firm_characteristics"        # 예정

# 가설별 figures/tables 를 노트북에서 매번 조립하지 않도록 이름을 부여한다.
# 노트북마다 TABLE_DIR / TAB_DIR / TABDIR 처럼 제각각 만들면 셀 실행 순서에 따라
# NameError가 나고, 저장 위치도 갈린다. 이름은 EDA의 FIGDIR/TABDIR 규칙을 따른다.
BASELINE_FIGDIR = BASELINE_DIR / "figures"
BASELINE_TABDIR = BASELINE_DIR / "tables"
H1_FIGDIR = H1_DIR / "figures"
H1_TABDIR = H1_DIR / "tables"
H2_FIGDIR = H2_DIR / "figures"
H2_TABDIR = H2_DIR / "tables"
H3_FIGDIR = H3_DIR / "figures"
H3_TABDIR = H3_DIR / "tables"

# H3 KRX 수집은 요청 단위 원본(raw)과 정규화·결합 결과(interim)를 분리한다.
# 분석 노트북은 KRX_INTERIM_DIR의 표준 CSV만 소비한다.
KRX_MANUAL_DIR = RAW_DIR / "firm" / "krx_manual"  # 09/10에서 실제 사용 (구성종목·시총가중·의약품 R&D 수기 입력)

# --- 아래 5개는 src/krx_collector.py(공식 KRX API만으로 PBR·배당수익률·구성종목을 받으려던 A안) 전용 ---
# A안은 KRX 화면 다운로드 파일(krx_valuation_YYYY.csv 등)이 확보되지 않아 pbr·dividend_yield를
# 채우지 못하고 중단됨(krx_validation_report.csv: pbr_available/dividend_yield_available 모두 FAIL,
# 639건 결측). 현재 09/10 노트북은 이 경로를 전혀 참조하지 않고 DART 기반 수집으로 대체했다.
# 삭제하지 않고 남겨두는 이유: src/krx_collector.py 자체가 참조하므로, 그 모듈을 완전히
# 제거하기 전까지는 상수만 지우면 ImportError가 난다. 2026-08-23 기준 미사용(deprecated).
KRX_RAW_DIR = RAW_DIR / "firm" / "krx"
KRX_INTERIM_DIR = INTERIM_DIR / "firm" / "krx"
KRX_CONSTITUENTS_FILE = KRX_INTERIM_DIR / "industry_constituents.csv"
KRX_FIRM_YEARLY_FILE = KRX_INTERIM_DIR / "krx_firm_yearly.csv"
KRX_ERROR_LOG_FILE = KRX_INTERIM_DIR / "krx_collection_errors.csv"
KRX_VALIDATION_FILE = KRX_INTERIM_DIR / "krx_validation_report.csv"

#: 팀원마다 csv/xlsx가 섞여 있어도 동작하도록 허용 확장자를 넓게 잡는다.
DATA_EXTENSIONS: tuple[str, ...] = (".csv", ".xlsx", ".xls")

#: 자동 탐색으로 결정된 항목의 기록: (이름, 선택된 경로, 표준경로 여부)
DISCOVERY_LOG: list[tuple[str, Path | None, bool]] = []


# =====================================================================
# 3. 프로젝트 내부 한정 탐색 유틸
# =====================================================================
def _ensure_inside_project(path: Path) -> Path:
    """path가 PROJECT_ROOT 하위인지 검증한다. 아니면 예외를 던진다.

    탐색 루트가 실수로 프로젝트 밖(홈 디렉터리 등)을 가리키면 다른 프로젝트의
    파일을 읽어버린다. 조용히 넘어가지 않고 즉시 실패시키는 편이 안전하다.
    """
    resolved = Path(path).resolve()
    if resolved != PROJECT_ROOT and PROJECT_ROOT not in resolved.parents:
        raise ValueError(
            f"프로젝트 외부 경로 탐색은 허용되지 않습니다.\n"
            f"  요청: {resolved}\n  PROJECT_ROOT: {PROJECT_ROOT}"
        )
    return resolved


def _normalize(text: str) -> str:
    """비교용 정규화: 소문자화 + 영숫자/한글 외 문자 제거.

    'treasury_yield_3y_10y' / 'Treasury Yield 3Y-10Y' / 'treasuryyield3y10y' 와
    'KOSPI 화학' / 'kospi_화학' / '화학' 을 같은 형태로 만든다.
    """
    return "".join(ch for ch in text.lower() if ch.isalnum())


def _strip_market_prefix(text: str) -> str:
    """정규화된 이름에서 'kospi'/'코스피' 접두를 제거한다."""
    for prefix in ("kospi", "코스피"):
        if text.startswith(prefix) and len(text) > len(prefix):
            return text[len(prefix):]
    return text


def _match_forms(name: str) -> tuple[str, str]:
    """이름 비교용 두 형태를 반환한다: 정규화형, 시장 접두 제거형.

    'KOSPI 화학'은 접두를 떼야 '화학'과 매칭되고, '코스피지수'는 접두를 떼면
    안 되므로('지수'만 남음) 두 형태를 모두 후보로 둔다.
    """
    normalized = _normalize(name)
    return normalized, _strip_market_prefix(normalized)


def _rel(path: Path) -> str:
    """PROJECT_ROOT 기준 상대경로 문자열. 사용자 PC 경로를 로그에 남기지 않는다."""
    try:
        return str(Path(path).resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def iter_data_files(
    folder: Path,
    extensions: Sequence[str] = DATA_EXTENSIONS,
    recursive: bool = True,
) -> list[Path]:
    """folder 안의 데이터 파일을 확장자 무관하게 정렬해 반환한다.

    - 임시/숨김 파일(~$, . 시작)과 .ipynb_checkpoints 하위는 제외한다.
    - recursive=True면 바로 아래에 파일이 없을 때만 하위 폴더까지 훑는다.
      (팀원이 연도별 하위 폴더를 하나 더 파는 경우를 흡수하되, 평소에는
       기존과 동일하게 폴더 바로 아래만 본다.)
    """
    folder = _ensure_inside_project(folder)
    if not folder.is_dir():
        return []

    exts = {e.lower() for e in extensions}

    def _ok(p: Path) -> bool:
        return (
            p.is_file()
            and p.suffix.lower() in exts
            and not p.name.startswith((".", "~$"))
            and ".ipynb_checkpoints" not in p.parts
        )

    direct = sorted(p for p in folder.iterdir() if _ok(p))
    if direct or not recursive:
        return direct
    return sorted((p for p in folder.rglob("*") if _ok(p)), key=lambda p: (len(p.parts), str(p)))


def find_data_files(
    keywords: Iterable[str],
    base: Path | None = None,
    extensions: Sequence[str] = DATA_EXTENSIONS,
) -> list[Path]:
    """base 하위에서 파일명에 keywords를 '모두' 포함하는 데이터 파일을 찾는다.

    - base 기본값은 RAW_DIR이며, 항상 PROJECT_ROOT 하위로 제한된다.
    - 정렬 기준: 경로 깊이 -> 파일명 길이 -> 사전순. 가장 얕고 단순한 후보가
      먼저 오므로 결과가 실행 환경과 무관하게 결정적이다.
    """
    base = _ensure_inside_project(base if base is not None else RAW_DIR)
    if not base.is_dir():
        return []

    keys = [_normalize(k) for k in keywords if k]
    exts = {e.lower() for e in extensions}

    matches = [
        p for p in base.rglob("*")
        if p.is_file()
        and p.suffix.lower() in exts
        and not p.name.startswith((".", "~$"))
        and ".ipynb_checkpoints" not in p.parts
        and all(k in _normalize(p.stem) for k in keys)
    ]
    return sorted(matches, key=lambda p: (len(p.relative_to(base).parts), len(p.name), str(p)))


def find_data_file(
    keyword_sets: Sequence[Sequence[str]],
    base: Path | None = None,
    extensions: Sequence[str] = DATA_EXTENSIONS,
) -> Path | None:
    """keyword_sets를 앞에서부터 시도해 첫 번째로 매칭되는 파일 1개를 반환한다.

    keyword_sets는 '우선순위가 있는 후보 규칙' 목록이다. 예를 들어
    [("treasury", "3y", "10y"), ("국고채",), ("yield",)] 는 정확한 이름을 먼저
    시도하고, 팀원이 다른 이름을 썼을 경우 점점 느슨한 규칙으로 넘어간다.
    후보가 여러 개면 첫 번째를 쓰되 경고로 알린다(조용한 오선택 방지).
    """
    for keywords in keyword_sets:
        found = find_data_files(keywords, base=base, extensions=extensions)
        if not found:
            continue
        if len(found) > 1:
            names = ", ".join(p.name for p in found)
            warnings.warn(
                f"키워드 {tuple(keywords)} 에 {len(found)}개 파일이 매칭되어 "
                f"'{found[0].name}' 을 사용합니다. (후보: {names})",
                RuntimeWarning,
                stacklevel=2,
            )
        return found[0]
    return None


def find_dir(aliases: Sequence[str], base: Path | None = None) -> Path | None:
    """base 하위에서 이름이 aliases 중 하나와 매칭되는 폴더를 찾는다.

    데이터 파일을 하나라도 가진 폴더만 후보로 삼는다(빈 껍데기 폴더 방지).
    우선순위는 (1) 폴더 바로 아래에 데이터 파일이 있는 곳, (2) 얕은 경로 순이다.
    상위 폴더도 하위 파일 때문에 후보가 되는데, 실제로 파일을 담고 있는 말단
    폴더를 골라야 하기 때문이다(예: '시장/' 보다 '시장/코스피지수/').
    """
    base = _ensure_inside_project(base if base is not None else RAW_DIR)
    if not base.is_dir():
        return None

    keys = [_normalize(a) for a in aliases if a]
    candidates = [
        d for d in base.rglob("*")
        if d.is_dir()
        and not d.name.startswith(".")
        and ".ipynb_checkpoints" not in d.parts
        and any(k in form for k in keys for form in _match_forms(d.name))
        and iter_data_files(d)
    ]
    if not candidates:
        return None
    return sorted(
        candidates,
        key=lambda d: (0 if iter_data_files(d, recursive=False) else 1, len(d.parts), str(d)),
    )[0]


def _resolve_file(
    name: str,
    default: Path,
    keyword_sets: Sequence[Sequence[str]],
    base: Path,
) -> Path:
    """표준 경로를 우선 사용하고, 없으면 base 하위를 키워드로 탐색한다.

    끝까지 못 찾으면 표준 경로를 그대로 반환한다. None을 반환하면 호출부에서
    NoneType 오류가 나 원인 파악이 어려우므로, "있어야 할 위치"를 담은 Path를
    돌려주어 FileNotFoundError 메시지가 바로 문제를 가리키게 한다.
    """
    if default.exists():
        DISCOVERY_LOG.append((name, default, True))
        return default

    found = find_data_file(keyword_sets, base=base)
    DISCOVERY_LOG.append((name, found, False))
    return found if found is not None else default


def _resolve_raw_file(
    name: str,
    default_relpath: str,
    keyword_sets: Sequence[Sequence[str]],
) -> Path:
    """RAW_DIR 하위 원본 파일 해석 (기존 호출부 유지용 얇은 래퍼)."""
    return _resolve_file(name, RAW_DIR / default_relpath, keyword_sets, RAW_DIR)


# =====================================================================
# 4. 원본(raw) 데이터 경로 — 기존 변수명 유지, 값은 자동 탐색
# =====================================================================
#: 산업/시장 원본 폴더의 표준 위치. 없으면 별칭으로 RAW_DIR 하위를 탐색한다.
RAW_INDUSTRY_DIR = RAW_DIR / "industry"
if not RAW_INDUSTRY_DIR.is_dir():
    RAW_INDUSTRY_DIR = find_dir(("industry", "industries", "sector", "산업", "업종")) or RAW_INDUSTRY_DIR

RAW_MARKET_DIR = RAW_DIR / "market" / "kospi_index"
if not iter_data_files(RAW_MARKET_DIR):
    RAW_MARKET_DIR = find_dir(("kospiindex", "kospi", "코스피", "market", "시장")) or RAW_MARKET_DIR

RAW_YIELD_FILE = _resolve_raw_file(
    "RAW_YIELD_FILE",
    "rates/treasury_yield_3y_10y.csv",
    [
        ("treasury", "yield", "3y", "10y"),
        ("treasury", "3y", "10y"),
        ("yield", "3y", "10y"),
        ("국고채", "3", "10"),
        ("국고채",),
    ],
)

# H1(수익률곡선·신용스프레드) 전용 원본. Baseline의 RAW_YIELD_FILE(3y·10y)과는
# 별개로 유지한다 — Baseline 재현성을 건드리지 않기 위함(2026-07-16 회의 반영).
RAW_YIELD_CURVE_FILE = _resolve_raw_file(
    "RAW_YIELD_CURVE_FILE",
    "rates/treasury_yield_curve_1_3_5_10y.csv",
    [
        ("treasury", "yield", "curve"),
        ("yield", "curve"),
        ("curve", "1", "3", "5", "10"),
        ("국고채", "커브"),
        ("수익률곡선",),
    ],
)

RAW_CREDIT_SPREAD_FILE = _resolve_raw_file(
    "RAW_CREDIT_SPREAD_FILE",
    "rates/corporate_bond_aa_minus_3y.csv",
    [
        ("corporate", "bond", "aa"),
        ("corporate", "aa"),
        ("credit", "spread"),
        ("회사채", "aa"),
        ("회사채",),
    ],
)


# =====================================================================
# 4-1. 가공(processed) 데이터 경로
# =====================================================================
# 노트북 03·04·05·06이 공통으로 읽는 최종 분석 패널. 각 노트북이
# PROCESSED_DIR / "..." 를 따로 조립하면 파일명이 바뀔 때마다 전부 고쳐야 하므로
# config에서 한 번만 정의한다.
#
# 주의: 키워드에 "daily"를 반드시 포함한다. "industry_rate_panel"까지만 주면
# 파생변수가 없는 industry_rate_panel_raw.csv 가 함께 매칭되어, 파일명이 더 짧은
# raw 쪽이 선택된다(정렬 규칙상). 그 파일에는 industry_return·d_y3 등이 없어
# 후속 회귀가 엉뚱한 지점에서 실패한다.
#
# 파일이 아직 없으면(clone 직후) 표준 경로를 그대로 반환한다.
# 01_data_preparation → 02_variable_generation 을 실행하면 생성된다.
PANEL_PATH = _resolve_file(
    "PANEL_PATH",
    PROCESSED_DIR / "industry_rate_panel_daily.csv",
    [
        ("industry", "rate", "panel", "daily"),
        ("industry", "panel", "daily"),
        ("panel", "daily"),
    ],
    base=PROCESSED_DIR,
)

#: 06_yield_curve_exposure 가 만드는 확장 패널(1·3·5·10년 금리 결합).
EXTENDED_PANEL_PATH = _resolve_file(
    "EXTENDED_PANEL_PATH",
    PROCESSED_DIR / "industry_rate_panel_extended.csv",
    [
        ("industry", "rate", "panel", "extended"),
        ("panel", "extended"),
    ],
    base=PROCESSED_DIR,
)


# =====================================================================
# 5. 산업 폴더명 매핑
# =====================================================================
# data/raw/industry 폴더명(영문) -> 원본 데이터 폴더명(KOSPI 접두 + 국문) 매핑.
# 01_data_preparation의 기존 로직이 "KOSPI " 접두를 제거하고 "금속"을
# "철강금속"으로 치환하는 방식을 그대로 쓰므로, 여기서 원본과 동일한
# 폴더명 형태로 맞춰주면 이후 코드를 전혀 수정하지 않아도 된다.
LOCAL_INDUSTRY_FOLDER_MAP = {
    "chemicals": "KOSPI 화학",
    "construction": "KOSPI 건설업",
    "electronics": "KOSPI 전기전자",
    "financials": "KOSPI 금융업",
    "metal": "KOSPI 금속",
    "pharma": "KOSPI 의약품",
    "transport_equipment": "KOSPI 운수장비",
}

# 팀원마다 폴더명이 영문/국문/축약형으로 갈리므로 표준 이름 하나에 여러 별칭을
# 붙여 흡수한다. 매칭은 '정규화 후 부분 문자열' 기준이며, 여러 별칭이 걸리면
# 가장 긴(=구체적인) 별칭이 이긴다.
INDUSTRY_ALIASES: dict[str, tuple[str, ...]] = {
    "KOSPI 화학": ("chemicals", "chemical", "chem", "화학"),
    "KOSPI 건설업": ("construction", "construct", "건설업", "건설"),
    "KOSPI 전기전자": ("electronics", "electronic", "elec", "전기전자", "전기·전자"),
    "KOSPI 금융업": ("financials", "financial", "finance", "금융업", "금융"),
    "KOSPI 금속": ("steelmetal", "metals", "metal", "steel", "철강금속", "철강", "금속"),
    "KOSPI 의약품": ("pharmaceuticals", "pharmaceutical", "pharma", "medicine", "의약품", "의약"),
    "KOSPI 운수장비": (
        "transportequipment", "transportation", "transport", "운수장비", "운수",
    ),
}


def canonical_industry_name(folder_name: str) -> str | None:
    """폴더명을 표준 산업명("KOSPI 화학" 등)으로 변환한다. 못 찾으면 None.

    1) LOCAL_INDUSTRY_FOLDER_MAP 정확 일치를 먼저 본다(기존 동작 보존).
    2) 실패하면 INDUSTRY_ALIASES로 부분 매칭한다.
    """
    if folder_name in LOCAL_INDUSTRY_FOLDER_MAP:
        return LOCAL_INDUSTRY_FOLDER_MAP[folder_name]

    forms = _match_forms(folder_name)
    if not any(forms):
        return None

    best: tuple[int, str] | None = None
    for canonical, aliases in INDUSTRY_ALIASES.items():
        for alias in aliases:
            key = _normalize(alias)
            if key and any(key in form for form in forms):
                if best is None or len(key) > best[0]:
                    best = (len(key), canonical)
    return best[1] if best else None


# =====================================================================
# 5-b. 모형 파라미터 (분석 전역 상수)
# =====================================================================
# Nelson-Siegel 감쇠계수 lambda.
#
# lambda 는 곡률(Curvature) loading 이 어느 만기에서 최대가 되는지를 정한다.
# 정점 만기 ~= 1.7932 / lambda 이므로, lambda 가 커질수록 곡률이 보는 지점이
# 짧은 만기 쪽으로 이동한다.
#
# 기본값 0.5 (곡률 정점 약 3.6년) — B-1/B-2 합의(2026-07-21).
#   선택 기준: '산업별 요인 분리'.
#   이 모형의 목적은 곡선을 정확히 묘사하는 것이 아니라 Level/Slope/Curvature
#   각각에 대한 산업별 노출을 분리해 추정하는 것이다. 요인이 서로 분리되지
#   않으면 '어느 요인 때문인가'라는 질문 자체에 답할 수 없다.
#   요인 간 다중공선성(최대 VIF)을 최소화하는 값은 0.52 부근이며, 소수점을
#   끌고 다니지 않도록 0.5 로 고정한다(결과 차이는 무시할 수준).
#
# 비교값 0.8041 (곡률 정점 약 2.2년)
#   선택 기준: '곡선 재구성 오차(SSE) 최소'. 곡선 적합도는 가장 좋지만
#   Slope VIF 가 9.5 로 요인이 잘 분리되지 않는다.
#
# 두 값은 곡선 묘사와 요인 분리 사이의 절충 관계에 있다. 어느 한쪽이
# 절대적으로 옳은 것은 아니므로 보고서에는 두 값을 병렬로 제시한다.
#
# lambda 선택에는 주가·검정통계량이 개입하지 않는다. 국고채 금리만으로 정한다.
NS_LAMBDA: float = 0.5
NS_LAMBDA_COMPARE: float = 0.8041

#: 곡률 loading 이 최대가 되는 만기(년). tau ~= 1.7932 / lambda
NS_CURVATURE_PEAK_YEARS: float = 1.7932 / NS_LAMBDA

#: HAC(Newey-West) 표준오차 시차. Baseline·H1 공통.
HAC_MAXLAGS: int = 5

#: BH(FDR) 보정 유의수준.
BH_ALPHA: float = 0.05


# =====================================================================
# 5-c. 시각화 공통 설정
# =====================================================================
# 노트북마다 폰트 코드를 따로 두면 한 곳만 빠져도 알아채기 어렵다.
# 실제로 STEP5 만 Windows 경로 하나만 보고 있어서 다른 환경에서 그래프
# 한글이 모두 네모로 깨졌다(2026-07-21 확인). 공통 설정을 여기 한 곳에 둔다.
#
# 적용 대상: 이 시점 이후 새로 만드는 노트북. 기존 노트북은 각자의 설정을
# 그대로 두고, 손볼 일이 생길 때 옮긴다.

#: 부호 색상 규칙 (docs/STYLE_GUIDE.md 12절).
#: 색만으로 정보를 전달하지 않는다. 부호(+/-)·기호를 반드시 함께 표기한다.
SIGN_COLORS: dict[str, str] = {
    "neg": "#c0392b",   # 음(-)
    "pos": "#1f6feb",   # 양(+)
    "ns": "#9aa0a6",    # 통계적으로 비유의
}

#: 한글 폰트 후보 경로. OS 별로 순서대로 시도한다.
KOREAN_FONT_PATHS: tuple[str, ...] = (
    "C:/Windows/Fonts/malgun.ttf",                          # Windows
    "/Library/Fonts/AppleGothic.ttf",                       # macOS
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",           # macOS
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",      # Linux
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
)

#: 경로 탐색이 모두 실패했을 때 설치된 폰트 이름으로 찾아볼 후보.
KOREAN_FONT_NAMES: tuple[str, ...] = (
    "Malgun Gothic", "AppleGothic", "AppleSDGothicNeo",
    "NanumGothic", "Noto Sans CJK KR", "Noto Sans CJK JP",
)


def setup_korean_font(verbose: bool = True) -> str | None:
    """matplotlib 한글 폰트를 설정하고 적용된 폰트명을 돌려준다.

    폰트를 찾지 못해도 예외를 던지지 않는다. 그래프 한글이 깨질 뿐이고
    분석 자체는 진행되어야 하기 때문이다.
    """
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    applied: str | None = None
    for font_path in KOREAN_FONT_PATHS:
        if Path(font_path).exists():
            font_manager.fontManager.addfont(font_path)
            applied = font_manager.FontProperties(fname=font_path).get_name()
            break

    if applied is None:
        installed = {f.name for f in font_manager.fontManager.ttflist}
        applied = next(
            (name for name in KOREAN_FONT_NAMES
             if any(name in found for found in installed)),
            None,
        )

    if applied is not None:
        plt.rcParams["font.family"] = applied
    elif verbose:
        print("한글 폰트를 찾지 못했습니다. 그래프의 한글이 깨질 수 있습니다.")

    # 음수 기호가 네모로 표시되는 것을 막는다.
    plt.rcParams["axes.unicode_minus"] = False

    if verbose and applied is not None:
        print(f"그래프 폰트: {applied}")
    return applied


def sign_color(value: float, significant: bool = True) -> str:
    """부호와 유의성에 따른 색을 돌려준다 (STYLE_GUIDE 12절).

    비유의면 부호와 무관하게 회색을 쓴다.
    """
    if not significant:
        return SIGN_COLORS["ns"]
    return SIGN_COLORS["neg"] if value < 0 else SIGN_COLORS["pos"]


# =====================================================================
# 6. 출력 디렉터리 생성 (모두 PROJECT_ROOT 하위이므로 안전)
# =====================================================================
for _d in (INTERIM_DIR, PROCESSED_DIR, FIGDIR, TABDIR):
    _d.mkdir(parents=True, exist_ok=True)

for _hd in (BASELINE_DIR, H1_DIR, H2_DIR, H3_DIR):
    (_hd / "figures").mkdir(parents=True, exist_ok=True)
    (_hd / "tables").mkdir(parents=True, exist_ok=True)


# =====================================================================
# 7. 산업 원본 폴더 목록
# =====================================================================
def get_industry_source_folders() -> list[tuple[str, Path]]:
    """(산업 폴더명, 경로) 목록을 반환한다.

    산업 원본 폴더를 표준 산업명으로 변환하고, KOSPI 시장지수 폴더를 'KOSPI'로
    추가한다. 반환 이름 규칙은 원본 데이터 명명과 동일("KOSPI 건설업", "KOSPI",
    ...)하므로 데이터 로드 이후 처리 코드는 손대지 않아도 된다.

    이전 구현과의 차이:
    - 폴더명이 영문/국문/축약형이어도 canonical_industry_name으로 흡수한다.
    - 별칭에도 걸리지 않으면 폴더명을 그대로 쓰되 경고한다(조용한 누락 방지).
    - 데이터 파일이 없는 폴더는 제외한다(.ipynb_checkpoints 등 방지).
    - 폴더가 없으면 예외 대신 경고 후 건너뛴다(팀원별 부분 데이터 허용).
    """
    folders: list[tuple[str, Path]] = []

    if RAW_INDUSTRY_DIR.is_dir():
        unmatched: list[str] = []
        for p in sorted(RAW_INDUSTRY_DIR.iterdir()):
            if not p.is_dir() or p.name.startswith(".") or not iter_data_files(p):
                continue
            name = canonical_industry_name(p.name)
            if name is None:
                unmatched.append(p.name)
                name = p.name
            folders.append((name, p))
        if unmatched:
            warnings.warn(
                f"표준 산업명으로 매칭되지 않은 폴더: {unmatched}. "
                "config.INDUSTRY_ALIASES에 별칭을 추가하세요.",
                RuntimeWarning,
                stacklevel=2,
            )
    else:
        warnings.warn(f"산업 원본 폴더를 찾지 못했습니다: {_rel(RAW_INDUSTRY_DIR)}", RuntimeWarning, stacklevel=2)

    if iter_data_files(RAW_MARKET_DIR):
        folders.append(("KOSPI", RAW_MARKET_DIR))
    else:
        warnings.warn(f"KOSPI 원본 폴더를 찾지 못했습니다: {_rel(RAW_MARKET_DIR)}", RuntimeWarning, stacklevel=2)

    return folders


# =====================================================================
# 8. 점검용
# =====================================================================
def describe() -> None:
    """실제로 어떤 경로/파일이 잡혔는지 출력한다. 노트북 첫 셀 점검용."""
    # 개인 PC 절대경로(Desktop, OneDrive, C:\Users ...)를 출력에 남기지 않는다 — 폴더명만 확인한다.
    print(f"PROJECT_ROOT : {PROJECT_ROOT.name}")
    print(f"DATA_DIR     : {_rel(DATA_DIR)}  (exists={DATA_DIR.exists()})")

    print("\n[raw 파일]")
    standard = {name: is_std for name, _, is_std in DISCOVERY_LOG}
    for name, path in (
        ("RAW_YIELD_FILE", RAW_YIELD_FILE),
        ("RAW_YIELD_CURVE_FILE", RAW_YIELD_CURVE_FILE),
        ("RAW_CREDIT_SPREAD_FILE", RAW_CREDIT_SPREAD_FILE),
    ):
        if not path.exists():
            mark = "MISSING"
        elif standard.get(name, False):
            mark = "OK     "
        else:
            mark = "OK(탐색)"
        print(f"  [{mark}] {name}: {_rel(path)}")

    print("\n[가공 데이터]")
    for name, path in (("PANEL_PATH", PANEL_PATH), ("EXTENDED_PANEL_PATH", EXTENDED_PANEL_PATH)):
        mark = "OK     " if path.exists() else "미생성 "
        print(f"  [{mark}] {name}: {_rel(path)}")

    print("\n[산업 원본 폴더]")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for industry, folder in get_industry_source_folders():
            print(f"  {industry:<12} {_rel(folder):<40} ({len(iter_data_files(folder))} files)")


if __name__ == "__main__":
    describe()
