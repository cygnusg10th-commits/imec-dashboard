"""FRED (Federal Reserve) API — 유가, 환율, 천연가스 가격."""

import requests
import pandas as pd
from typing import Optional
from .db import cache_get, cache_set
from config import FRED_API_KEY, FRED_SERIES, CACHE_TTL

BASE_URL = "https://api.stlouisfed.org/fred/series/observations"


def _fetch_series(series_id: str, limit: int = 365) -> Optional[pd.DataFrame]:
    if not FRED_API_KEY:
        return None
    params = {
        "series_id":   series_id,
        "api_key":     FRED_API_KEY,
        "file_type":   "json",
        "sort_order":  "desc",
        "limit":       limit,
        "observation_start": "2020-01-01",
    }
    try:
        r = requests.get(BASE_URL, params=params, timeout=20)
        r.raise_for_status()
        data = r.json().get("observations", [])
        records = [
            {"date": d["date"], "value": float(d["value"])}
            for d in data if d["value"] != "."
        ]
        df = pd.DataFrame(records)
        df["date"] = pd.to_datetime(df["date"])
        return df.sort_values("date").reset_index(drop=True)
    except Exception:
        return None


def get_brent() -> Optional[pd.DataFrame]:
    key = "fred_brent"
    cached = cache_get(key, CACHE_TTL["daily"])
    if cached is not None:
        cached["date"] = pd.to_datetime(cached["date"])
        return cached
    df = _fetch_series(FRED_SERIES["brent"])
    if df is not None:
        cache_set(key, df)
    return df


def get_wti() -> Optional[pd.DataFrame]:
    key = "fred_wti"
    cached = cache_get(key, CACHE_TTL["daily"])
    if cached is not None:
        cached["date"] = pd.to_datetime(cached["date"])
        return cached
    df = _fetch_series(FRED_SERIES["wti"])
    if df is not None:
        cache_set(key, df)
    return df


def get_natgas() -> Optional[pd.DataFrame]:
    key = "fred_natgas"
    cached = cache_get(key, CACHE_TTL["daily"])
    if cached is not None:
        cached["date"] = pd.to_datetime(cached["date"])
        return cached
    df = _fetch_series(FRED_SERIES["natgas"])
    if df is not None:
        cache_set(key, df)
    return df


def get_usd_inr() -> Optional[pd.DataFrame]:
    key = "fred_usd_inr"
    cached = cache_get(key, CACHE_TTL["daily"])
    if cached is not None:
        cached["date"] = pd.to_datetime(cached["date"])
        return cached
    df = _fetch_series(FRED_SERIES["usd_inr"])
    if df is not None:
        cache_set(key, df)
    return df


def get_usd_eur() -> Optional[pd.DataFrame]:
    key = "fred_usd_eur"
    cached = cache_get(key, CACHE_TTL["daily"])
    if cached is not None:
        cached["date"] = pd.to_datetime(cached["date"])
        return cached
    df = _fetch_series(FRED_SERIES["usd_eur"])
    if df is not None:
        cache_set(key, df)
    return df


def get_latest_value(series_name: str) -> Optional[float]:
    """시리즈의 최신 값 하나만 반환."""
    fetch_map = {
        "brent":   get_brent,
        "wti":     get_wti,
        "natgas":  get_natgas,
        "usd_inr": get_usd_inr,
        "usd_eur": get_usd_eur,
    }
    fn = fetch_map.get(series_name)
    if not fn:
        return None
    df = fn()
    if df is None or df.empty:
        return None
    return df["value"].iloc[-1]
