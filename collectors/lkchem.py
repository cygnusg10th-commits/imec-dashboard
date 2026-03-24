"""엘케이켐(489500) 모니터링 — 주가, DART 공시, 뉴스, 재무."""

import requests
import zipfile
import io
import xml.etree.ElementTree as ET
import yfinance as yf
import pandas as pd
from typing import Optional
from .db import cache_get, cache_set, manual_get, manual_set
from config import get_key, CACHE_TTL

TICKER        = "489500.KQ"
DART_CORP_CODE = "01747977"   # 엘케이켐 DART 기업코드
DART_BASE     = "https://opendart.fss.or.kr/api"

# ---------------------------------------------------------------------------
# 주가 데이터
# ---------------------------------------------------------------------------

def get_stock_history(period: str = "1y") -> Optional[pd.DataFrame]:
    key = f"lkchem_stock_{period}"
    cached = cache_get(key, CACHE_TTL["daily"])
    if cached is not None:
        cached["date"] = pd.to_datetime(cached["date"])
        return cached
    try:
        ticker = yf.Ticker(TICKER)
        df = ticker.history(period=period, interval="1d")
        if df.empty:
            return None
        df = df[["Close", "Volume"]].reset_index()
        df.columns = ["date", "close", "volume"]
        df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
        df = df.dropna().reset_index(drop=True)
        cache_set(key, df)
        return df
    except Exception:
        return None


def get_stock_info() -> dict:
    """최신 주가 및 기본 지표."""
    try:
        ticker = yf.Ticker(TICKER)
        info = ticker.info
        hist = get_stock_history("5d")
        price = hist["close"].iloc[-1] if hist is not None and not hist.empty else None
        prev  = hist["close"].iloc[-2] if hist is not None and len(hist) > 1 else None
        return {
            "price":        price,
            "prev":         prev,
            "change":       ((price - prev) / prev * 100) if price and prev else None,
            "market_cap":   info.get("marketCap"),
            "per":          info.get("trailingPE"),
            "pbr":          info.get("priceToBook"),
            "52w_high":     info.get("fiftyTwoWeekHigh"),
            "52w_low":      info.get("fiftyTwoWeekLow"),
            "volume":       info.get("volume"),
            "avg_volume":   info.get("averageVolume"),
        }
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# DART 전자공시
# ---------------------------------------------------------------------------

def _dart_api_key() -> str:
    return get_key("DART_API_KEY")


def get_dart_corp_code() -> str:
    """DART 기업코드 동적 조회 (캐시 없으면 기본값 반환)."""
    key = "lkchem_dart_corp_code"
    cached = cache_get(key, CACHE_TTL["quarterly"])
    if cached is not None and not cached.empty:
        return cached["corp_code"].iloc[0]

    api_key = _dart_api_key()
    if not api_key:
        return DART_CORP_CODE
    try:
        r = requests.get(
            f"{DART_BASE}/corpCode.xml",
            params={"crtfc_key": api_key},
            timeout=30,
        )
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            xml_data = z.read("CORPCODE.xml")
        root = ET.fromstring(xml_data)
        for item in root.findall("list"):
            name = item.findtext("corp_name", "")
            stock = item.findtext("stock_code", "")
            if stock == "489500" or "엘케이켐" in name:
                corp_code = item.findtext("corp_code", DART_CORP_CODE)
                cache_set(key, pd.DataFrame([{"corp_code": corp_code}]))
                return corp_code
    except Exception:
        pass
    return DART_CORP_CODE


def get_disclosures(limit: int = 15) -> Optional[pd.DataFrame]:
    """최신 공시 목록 조회."""
    key = "lkchem_disclosures"
    cached = cache_get(key, 6)  # 6시간 캐시
    if cached is not None:
        return cached

    api_key = _dart_api_key()
    if not api_key:
        return None
    try:
        corp_code = get_dart_corp_code()
        r = requests.get(
            f"{DART_BASE}/list.json",
            params={
                "crtfc_key":  api_key,
                "corp_code":  corp_code,
                "bgn_de":     "20240101",   # 시작일 필수
                "page_count": limit,
                "page_no":    1,
            },
            timeout=20,
        )
        data = r.json()
        if data.get("status") != "000":
            return None
        items = data.get("list", [])
        df = pd.DataFrame([{
            "날짜":   item.get("rcept_dt", ""),
            "제목":   item.get("report_nm", ""),
            "종류":   item.get("pblntf_ty", ""),
            "공시링크": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={item.get('rcept_no','')}",
        } for item in items])
        cache_set(key, df)
        return df
    except Exception:
        return None


def get_financials_dart(year: int = 2024) -> Optional[pd.DataFrame]:
    """DART 재무제표 조회."""
    key = f"lkchem_fin_{year}"
    cached = cache_get(key, CACHE_TTL["monthly"])
    if cached is not None:
        return cached

    api_key = _dart_api_key()
    if not api_key:
        return None
    try:
        corp_code = get_dart_corp_code()
        r = requests.get(
            f"{DART_BASE}/fnlttSinglAcntAll.json",
            params={
                "crtfc_key":  api_key,
                "corp_code":  corp_code,
                "bsns_year":  str(year),
                "reprt_code": "11011",   # 사업보고서
                "fs_div":     "CFS",     # 연결
            },
            timeout=20,
        )
        data = r.json()
        if data.get("status") != "000":
            return None
        df = pd.DataFrame(data.get("list", []))
        cache_set(key, df)
        return df
    except Exception:
        return None


# ---------------------------------------------------------------------------
# 하드코딩 재무 데이터 (DART 키 없을 때 폴백)
# ---------------------------------------------------------------------------

def get_financials_static() -> pd.DataFrame:
    """공개 자료 기반 알려진 재무 데이터."""
    return pd.DataFrame([
        {"연도": "2022", "매출(억)": 129, "영업이익(억)": 47,  "순이익(억)": 36,  "영업이익률(%)": 36.4},
        {"연도": "2023", "매출(억)": 160, "영업이익(억)": 35,  "순이익(억)": 28,  "영업이익률(%)": 21.9},
        {"연도": "2024", "매출(억)": 250, "영업이익(억)": 100, "순이익(억)": 73,  "영업이익률(%)": 40.0},
        {"연도": "2025E","매출(억)": 258, "영업이익(억)": 82,  "순이익(억)": None, "영업이익률(%)": 31.8},
    ])


# ---------------------------------------------------------------------------
# 뉴스
# ---------------------------------------------------------------------------

def get_news(limit: int = 20) -> Optional[pd.DataFrame]:
    """엘케이켐 관련 뉴스 — GDELT (영문 쿼리)."""
    key = "lkchem_news"
    cached = cache_get(key, CACHE_TTL["daily"])
    if cached is not None:
        return cached
    # GDELT는 영문 기사만 인덱싱 — 영문 쿼리 사용
    queries = [
        "perovskite solar cell Korea semiconductor",
        "hafnium chloride semiconductor precursor Korea",
        "Korea KOSDAQ specialty chemicals semiconductor material",
    ]
    records = []
    for q in queries:
        try:
            r = requests.get(
                "https://api.gdeltproject.org/api/v2/doc/doc",
                params={"query": q, "mode": "artlist", "maxrecords": 10,
                        "timespan": "30d", "format": "json", "sort": "datedesc"},
                timeout=20,
            )
            r.raise_for_status()
            for a in r.json().get("articles", []):
                title = a.get("title", "")
                if not title:
                    continue
                records.append({
                    "title":  title,
                    "url":    a.get("url", "#"),
                    "source": a.get("domain", ""),
                    "date":   str(a.get("seendate", ""))[:8],
                })
        except Exception:
            continue
    if not records:
        return None
    df = pd.DataFrame(records).drop_duplicates("title").head(limit)
    cache_set(key, df)
    return df


# ---------------------------------------------------------------------------
# 연구 파이프라인 (수동 입력)
# ---------------------------------------------------------------------------

def get_pipeline() -> pd.DataFrame:
    df = manual_get("lkchem_pipeline")
    if df is not None and not df.empty:
        return df
    # 기본 파이프라인 (공개 자료 기반)
    return pd.DataFrame([
        {"단계": "완료", "항목": "PCP 리간드 국내 유일 상업 생산",         "목표 시기": "2020~",    "비고": "현재 주력 제품"},
        {"단계": "완료", "항목": "DIS 프리커서 세계 최대 단일 캐파 확보",   "목표 시기": "2024",     "비고": "연 600억 원 생산 능력"},
        {"단계": "진행", "항목": "DIS 신규 고객사 (I사·M사) 납품 테스트",  "목표 시기": "2026 H1",  "비고": "5nm 공정 적용"},
        {"단계": "진행", "항목": "HfCl4 국산화 개발",                       "목표 시기": "2026~2027","비고": "일본 TCLC 특허 만료 대응"},
        {"단계": "진행", "항목": "3공장 신축 (천안)",                        "목표 시기": "2026",     "비고": "공모자금 40억 투자"},
        {"단계": "진행", "항목": "건식 페로브스카이트 소재 개발",            "목표 시기": "2026~2028","비고": "KRICT 기술이전, 연구용 샘플 공급 중"},
        {"단계": "예정", "항목": "HfCl4 본격 판매",                         "목표 시기": "2027",     "비고": "ZrO2/HfO2 병행"},
        {"단계": "예정", "항목": "페로브스카이트 소재 상업화",               "목표 시기": "2028+",    "비고": "탠덤 태양전지 상부셀 소재"},
        {"단계": "예정", "항목": "우주용 페로브스카이트 (서리대 공동연구)",  "목표 시기": "2028+",    "비고": "2026.02 협약 체결"},
    ])
