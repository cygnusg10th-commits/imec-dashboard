"""UN Comtrade API v1 — 양자 교역 데이터."""

import requests
import pandas as pd
from typing import Optional
from .db import cache_get, cache_set
from config import CACHE_TTL

BASE_URL = "https://comtradeapi.un.org/data/v1/get/C/A/HS"

# 관심 국가쌍
TRADE_PAIRS = [
    ("699", "784"),   # 인도 → UAE
    ("699", "682"),   # 인도 → 사우디
    ("784", "682"),   # UAE → 사우디
    ("376", "699"),   # 이스라엘 → 인도
    ("376", "251"),   # 이스라엘 → 프랑스(EU 대표)
    ("699", "276"),   # 인도 → 독일
]

COUNTRY_NAMES = {
    "699": "India", "784": "UAE", "682": "Saudi Arabia",
    "376": "Israel", "251": "France", "276": "Germany",
    "300": "Greece", "380": "Italy",
}


def _fetch_pair(reporter: str, partner: str, year: int = 2023) -> Optional[pd.DataFrame]:
    """특정 국가쌍의 연간 교역 데이터 조회 (무료, 인증 불필요)."""
    params = {
        "reporterCode": reporter,
        "partnerCode":  partner,
        "period":       str(year),
        "cmdCode":      "TOTAL",
        "flowCode":     "X",     # 수출
        "maxRecords":   1,
    }
    try:
        r = requests.get(BASE_URL, params=params, timeout=30)
        if r.status_code != 200:
            return None
        data = r.json().get("data", [])
        if not data:
            return None
        row = data[0]
        return pd.DataFrame([{
            "reporter": COUNTRY_NAMES.get(reporter, reporter),
            "partner":  COUNTRY_NAMES.get(partner, partner),
            "year":     year,
            "trade_usd": float(row.get("primaryValue", 0)),
        }])
    except Exception:
        return None


def get_trade_matrix(years: list = None) -> Optional[pd.DataFrame]:
    """주요 국가쌍 교역 매트릭스 반환."""
    if years is None:
        years = [2022, 2023]
    key = f"comtrade_matrix_{'_'.join(map(str, years))}"
    cached = cache_get(key, CACHE_TTL["monthly"])
    if cached is not None:
        return cached

    records = []
    for reporter, partner in TRADE_PAIRS:
        for year in years:
            df = _fetch_pair(reporter, partner, year)
            if df is not None:
                records.append(df)

    if not records:
        return None
    result = pd.concat(records, ignore_index=True)
    cache_set(key, result)
    return result
