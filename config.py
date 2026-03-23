import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

def get_key(name: str) -> str:
    """API 키를 호출 시점에 읽음 — 로컬 .env 우선, 없으면 st.secrets."""
    val = os.environ.get(name, "")
    if val:
        return val
    try:
        import streamlit as st
        # st.secrets는 dict-like; .get() 또는 [] 모두 시도
        try:
            v = st.secrets[name]
            return v if v else ""
        except (KeyError, AttributeError):
            return st.secrets.get(name, "")
    except Exception:
        return ""

# 하위 호환용 모듈 __getattr__ — 함수 호출 시마다 최신 값 반환
def __getattr__(name: str) -> str:
    _key_map = {
        "FRED_API_KEY":  "FRED_API_KEY",
        "EIA_API_KEY":   "EIA_API_KEY",
        "NEWS_API_KEY":  "NEWS_API_KEY",
        "COMTRADE_KEY":  "COMTRADE_API_KEY",
        "DART_API_KEY":  "DART_API_KEY",
    }
    if name in _key_map:
        return get_key(_key_map[name])
    raise AttributeError(f"module 'config' has no attribute {name!r}")

# --- IMEC 참여국 ---
IMEC_COUNTRIES = {
    "IN": {"name": "인도",          "name_en": "India",                "flag": "🇮🇳", "role": "동쪽 기점"},
    "AE": {"name": "UAE",           "name_en": "United Arab Emirates", "flag": "🇦🇪", "role": "환적 허브"},
    "SA": {"name": "사우디아라비아", "name_en": "Saudi Arabia",         "flag": "🇸🇦", "role": "철도/에너지"},
    "JO": {"name": "요르단",         "name_en": "Jordan",               "flag": "🇯🇴", "role": "통과 국가"},
    "IL": {"name": "이스라엘",       "name_en": "Israel",               "flag": "🇮🇱", "role": "지중해 연결"},
    "GR": {"name": "그리스",         "name_en": "Greece",               "flag": "🇬🇷", "role": "유럽 진입점"},
    "IT": {"name": "이탈리아",       "name_en": "Italy",                "flag": "🇮🇹", "role": "유럽 종착점"},
}

# World Bank ISO3 코드 매핑
WB_COUNTRY_CODES = {
    "IN": "IND", "AE": "ARE", "SA": "SAU",
    "JO": "JOR", "IL": "ISR", "GR": "GRC", "IT": "ITA",
}

# --- IMEC 경로 노드 (지도용) ---
ROUTE_NODES = [
    {"label": "Mumbai 🇮🇳",           "lat": 19.076,  "lon": 72.877,  "type": "port"},
    {"label": "Dubai (Jebel Ali) 🇦🇪", "lat": 25.010,  "lon": 55.065,  "type": "port"},
    {"label": "Abu Dhabi 🇦🇪",         "lat": 24.466,  "lon": 54.366,  "type": "city"},
    {"label": "Riyadh 🇸🇦",            "lat": 24.687,  "lon": 46.722,  "type": "city"},
    {"label": "Haifa 🇮🇱",             "lat": 32.794,  "lon": 34.989,  "type": "port"},
    {"label": "Piraeus 🇬🇷",           "lat": 37.942,  "lon": 23.647,  "type": "port"},
    {"label": "Genoa 🇮🇹",             "lat": 44.405,  "lon": 8.946,   "type": "port"},
]

# IMEC 경로 선 (waypoints)
ROUTE_LINES = [
    # 인도 → UAE (해상)
    [(19.076, 72.877), (21.0, 65.0), (23.5, 58.5), (25.010, 55.065)],
    # UAE → 사우디 → 이스라엘 (육상)
    [(25.010, 55.065), (24.466, 54.366), (24.687, 46.722), (29.5, 37.5), (32.0, 36.5), (32.794, 34.989)],
    # 이스라엘 → 그리스 → 이탈리아 (해상)
    [(32.794, 34.989), (35.5, 28.0), (37.942, 23.647), (39.0, 20.0), (40.5, 15.5), (44.405, 8.946)],
]

# --- FRED 시리즈 ID ---
FRED_SERIES = {
    "brent":      "DCOILBRENTEU",   # Brent 원유 ($/bbl)
    "wti":        "DCOILWTICO",     # WTI 원유 ($/bbl)
    "natgas":     "DHHNGSP",        # Henry Hub 천연가스 ($/MMBtu)
    "usd_inr":    "DEXINUS",        # USD당 INR
    "usd_eur":    "DEXUSEU",        # EUR당 USD
}

# --- Yahoo Finance 심볼 ---
YFINANCE_SYMBOLS = {
    "nifty50":    "^NSEI",          # 인도 Nifty 50
    "ta125":      "^TA125.TA",      # 이스라엘 TA-125
    "aramco":     "2222.SR",        # 사우디 Aramco
    "bdry":       "BDRY",           # BDI 프록시 ETF (Breakwave Dry Bulk)
    "brent_f":    "BZ=F",           # Brent 선물
    "natgas_f":   "NG=F",           # 천연가스 선물
    "ils_usd":    "ILS=X",          # ILS/USD
    "inr_usd":    "INR=X",          # INR/USD
    "eur_usd":    "EURUSD=X",       # EUR/USD
}

# --- GDELT 모니터링 쿼리 ---
GDELT_QUERIES = {
    "israel_conflict":    "Israel Gaza conflict war",
    "suez_red_sea":       "Suez Canal Red Sea shipping",
    "imec_corridor":      "IMEC India Middle East Europe corridor",
    "bri_china":          "Belt Road Initiative China BRI",
    "saudi_normalize":    "Saudi Arabia normalization Israel",
    "india_trade":        "India trade export corridor",
}

# --- NewsAPI 검색 키워드 ---
NEWS_QUERIES = {
    "IMEC":       "IMEC OR \"India Middle East Europe Corridor\"",
    "중동 정세":   "Israel OR Hamas OR \"Saudi Arabia\" normalization",
    "해운":       "Suez Canal OR \"Red Sea\" shipping",
    "에너지":     "Saudi Aramco OR OPEC OR \"oil production\"",
    "BRI 경쟁":   "\"Belt and Road\" OR BRI China corridor",
}

# --- 캐시 TTL (시간) ---
CACHE_TTL = {
    "daily":    24,
    "weekly":   168,
    "monthly":  720,
    "quarterly": 2160,
}
