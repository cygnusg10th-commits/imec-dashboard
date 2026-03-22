"""GDELT Project API — 지정학적 이벤트 뉴스 볼륨 & 감성 지수 (키 불필요)."""

import requests
import pandas as pd
from typing import Optional
from .db import cache_get, cache_set
from config import GDELT_QUERIES, CACHE_TTL

DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"


def _fetch_timeline(query: str, timespan: str = "90d") -> Optional[pd.DataFrame]:
    """GDELT 뉴스 볼륨 타임라인 조회."""
    params = {
        "query":    query,
        "mode":     "timelinevolinfo",
        "timespan": timespan,
        "format":   "json",
    }
    try:
        r = requests.get(DOC_API, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        timeline = data.get("timeline", [])
        if not timeline:
            return None
        # 첫 번째 시리즈 사용 (ALL ARTICLES)
        series_data = timeline[0].get("data", [])
        records = []
        for item in series_data:
            records.append({
                "date":  pd.to_datetime(item["date"], format="%Y%m%dT%H%M%S"),
                "value": float(item.get("value", 0)),
            })
        return pd.DataFrame(records) if records else None
    except Exception:
        return None


def _fetch_articles(query: str, max_records: int = 25) -> Optional[pd.DataFrame]:
    """GDELT 최신 뉴스 기사 목록 조회."""
    params = {
        "query":      query,
        "mode":       "artlist",
        "maxrecords": max_records,
        "timespan":   "7d",
        "format":     "json",
        "sort":       "datedesc",
    }
    try:
        r = requests.get(DOC_API, params=params, timeout=30)
        r.raise_for_status()
        articles = r.json().get("articles", [])
        if not articles:
            return None
        records = []
        for a in articles:
            records.append({
                "title":   a.get("title", ""),
                "url":     a.get("url", ""),
                "domain":  a.get("domain", ""),
                "date":    a.get("seendate", ""),
                "lang":    a.get("language", ""),
            })
        return pd.DataFrame(records)
    except Exception:
        return None


def get_timeline(query_key: str, timespan: str = "90d") -> Optional[pd.DataFrame]:
    """쿼리 키로 타임라인 데이터 반환."""
    query = GDELT_QUERIES.get(query_key, query_key)
    key = f"gdelt_timeline_{query_key}_{timespan}"
    cached = cache_get(key, CACHE_TTL["daily"])
    if cached is not None:
        cached["date"] = pd.to_datetime(cached["date"])
        return cached
    df = _fetch_timeline(query, timespan)
    if df is not None:
        cache_set(key, df)
    return df


def get_all_timelines(timespan: str = "90d") -> dict:
    """모든 GDELT 쿼리의 타임라인 반환."""
    results = {}
    for key in GDELT_QUERIES:
        df = get_timeline(key, timespan)
        if df is not None:
            results[key] = df
    return results


def get_articles(query_key: str) -> Optional[pd.DataFrame]:
    """최근 7일 기사 목록 반환."""
    query = GDELT_QUERIES.get(query_key, query_key)
    key = f"gdelt_articles_{query_key}"
    cached = cache_get(key, CACHE_TTL["daily"])
    if cached is not None:
        return cached
    df = _fetch_articles(query)
    if df is not None:
        cache_set(key, df)
    return df


def get_risk_score(query_key: str) -> Optional[float]:
    """최근 7일 vs 이전 7일 볼륨 비교로 리스크 스코어 계산 (0~100)."""
    df = get_timeline(query_key, "30d")
    if df is None or len(df) < 14:
        return None
    recent  = df["value"].tail(7).mean()
    earlier = df["value"].head(7).mean()
    if earlier == 0:
        return 50.0
    ratio = recent / earlier
    # ratio > 1이면 상승, 최대 100으로 스케일
    score = min(100, max(0, (ratio - 0.5) * 50))
    return round(score, 1)
