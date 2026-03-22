"""World Bank Open Data API — GDP, FDI, LPI, 교역량."""

import requests
import pandas as pd
from typing import Optional
from .db import cache_get, cache_set
from config import WB_COUNTRY_CODES, CACHE_TTL

BASE_URL = "https://api.worldbank.org/v2"
COUNTRIES_ISO3 = list(WB_COUNTRY_CODES.values())
COUNTRIES_PARAM = ";".join(COUNTRIES_ISO3)

WB_INDICATORS = {
    "gdp_growth":  "NY.GDP.MKTP.KD.ZG",   # GDP 성장률 (%)
    "gdp_usd":     "NY.GDP.MKTP.CD",       # GDP (현재 USD)
    "fdi_pct":     "BX.KLT.DINV.WD.GD.ZS",# FDI 순유입 (GDP 대비 %)
    "trade_pct":   "NE.TRD.GNFS.ZS",       # 무역 비중 (GDP 대비 %)
    "lpi":         "LP.LPI.OVRL.XQ",       # 물류 성과지수
}

ISO3_TO_ISO2 = {v: k for k, v in WB_COUNTRY_CODES.items()}


def _fetch_indicator(indicator: str, years: int = 10) -> Optional[pd.DataFrame]:
    url = f"{BASE_URL}/country/{COUNTRIES_PARAM}/indicator/{indicator}"
    params = {"format": "json", "per_page": 200, "mrv": years}
    try:
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        payload = r.json()
        if len(payload) < 2 or not payload[1]:
            return None
        records = []
        for item in payload[1]:
            if item.get("value") is None:
                continue
            records.append({
                "country_iso3": item["countryiso3code"],
                "country":      ISO3_TO_ISO2.get(item["countryiso3code"], item["countryiso3code"]),
                "year":         int(item["date"]),
                "value":        float(item["value"]),
            })
        return pd.DataFrame(records) if records else None
    except Exception:
        return None


def get_gdp_growth() -> Optional[pd.DataFrame]:
    key = "wb_gdp_growth"
    cached = cache_get(key, CACHE_TTL["monthly"])
    if cached is not None:
        return cached
    df = _fetch_indicator(WB_INDICATORS["gdp_growth"])
    if df is not None:
        cache_set(key, df)
    return df


def get_gdp_usd() -> Optional[pd.DataFrame]:
    key = "wb_gdp_usd"
    cached = cache_get(key, CACHE_TTL["monthly"])
    if cached is not None:
        return cached
    df = _fetch_indicator(WB_INDICATORS["gdp_usd"])
    if df is not None:
        df["value"] = df["value"] / 1e12  # USD → 조 달러
        cache_set(key, df)
    return df


def get_fdi() -> Optional[pd.DataFrame]:
    key = "wb_fdi"
    cached = cache_get(key, CACHE_TTL["monthly"])
    if cached is not None:
        return cached
    df = _fetch_indicator(WB_INDICATORS["fdi_pct"])
    if df is not None:
        cache_set(key, df)
    return df


def get_lpi() -> Optional[pd.DataFrame]:
    key = "wb_lpi"
    cached = cache_get(key, CACHE_TTL["quarterly"])
    if cached is not None:
        return cached
    df = _fetch_indicator(WB_INDICATORS["lpi"], years=5)
    if df is not None:
        cache_set(key, df)
    return df


def get_trade_pct() -> Optional[pd.DataFrame]:
    key = "wb_trade_pct"
    cached = cache_get(key, CACHE_TTL["monthly"])
    if cached is not None:
        return cached
    df = _fetch_indicator(WB_INDICATORS["trade_pct"])
    if df is not None:
        cache_set(key, df)
    return df
