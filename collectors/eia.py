"""EIA (U.S. Energy Information Administration) API v2 — 원유 생산, 수입 데이터."""

import requests
import pandas as pd
from typing import Optional
from .db import cache_get, cache_set
from config import EIA_API_KEY, CACHE_TTL

BASE_URL = "https://api.eia.gov/v2/international/data/"


def _fetch(activity_id: str, country_code: str, product_id: str = "57",
           unit: str = "TBPD", length: int = 36) -> Optional[pd.DataFrame]:
    """국제 석유 데이터 조회. activity: 1=생산, 2=수입, 4=수출."""
    if not EIA_API_KEY:
        return None
    params = {
        "api_key":               EIA_API_KEY,
        "frequency":             "monthly",
        "data[0]":               "value",
        "facets[activityId][]":  activity_id,
        "facets[productId][]":   product_id,
        "facets[countryRegionId][]": country_code,
        "facets[unit][]":        unit,
        "sort[0][column]":       "period",
        "sort[0][direction]":    "desc",
        "length":                length,
    }
    try:
        r = requests.get(BASE_URL, params=params, timeout=20)
        r.raise_for_status()
        data = r.json().get("response", {}).get("data", [])
        if not data:
            return None
        df = pd.DataFrame(data)[["period", "value", "unit"]].copy()
        df["period"] = pd.to_datetime(df["period"], format="%Y-%m")
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        return df.dropna().sort_values("period").reset_index(drop=True)
    except Exception:
        return None


def get_saudi_production() -> Optional[pd.DataFrame]:
    """사우디아라비아 원유 생산량 (천 배럴/일)."""
    key = "eia_saudi_prod"
    cached = cache_get(key, CACHE_TTL["monthly"])
    if cached is not None:
        cached["period"] = pd.to_datetime(cached["period"])
        return cached
    df = _fetch("1", "SAU")
    if df is not None:
        cache_set(key, df)
    return df


def get_india_imports() -> Optional[pd.DataFrame]:
    """인도 원유 수입량 (천 배럴/일)."""
    key = "eia_india_imports"
    cached = cache_get(key, CACHE_TTL["monthly"])
    if cached is not None:
        cached["period"] = pd.to_datetime(cached["period"])
        return cached
    df = _fetch("2", "IND")
    if df is not None:
        cache_set(key, df)
    return df


def get_uae_production() -> Optional[pd.DataFrame]:
    """UAE 원유 생산량 (천 배럴/일)."""
    key = "eia_uae_prod"
    cached = cache_get(key, CACHE_TTL["monthly"])
    if cached is not None:
        cached["period"] = pd.to_datetime(cached["period"])
        return cached
    df = _fetch("1", "UAE")
    if df is not None:
        cache_set(key, df)
    return df
