"""NewsAPI + GDELT 뉴스 수집 — 키워드별 최신 헤드라인."""

import requests
import pandas as pd
from typing import Optional
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from .db import cache_get, cache_set
from .gdelt import get_articles as gdelt_articles
import config
from config import NEWS_QUERIES, CACHE_TTL

NEWSAPI_URL = "https://newsapi.org/v2/everything"
_analyzer = SentimentIntensityAnalyzer()


def _sentiment(text: str) -> str:
    score = _analyzer.polarity_scores(text)["compound"]
    if score >= 0.05:
        return "긍정"
    elif score <= -0.05:
        return "부정"
    return "중립"


def _fetch_newsapi(query: str, page_size: int = 20) -> Optional[pd.DataFrame]:
    NEWS_API_KEY = config.get_key("NEWS_API_KEY")
    if not NEWS_API_KEY:
        return None
    params = {
        "q":        query,
        "apiKey":   NEWS_API_KEY,
        "language": "en",
        "sortBy":   "publishedAt",
        "pageSize": page_size,
    }
    try:
        r = requests.get(NEWSAPI_URL, params=params, timeout=20)
        r.raise_for_status()
        articles = r.json().get("articles", [])
        records = []
        for a in articles:
            title = a.get("title") or ""
            records.append({
                "title":     title,
                "url":       a.get("url", ""),
                "source":    a.get("source", {}).get("name", ""),
                "date":      a.get("publishedAt", "")[:10],
                "sentiment": _sentiment(title),
            })
        return pd.DataFrame(records) if records else None
    except Exception:
        return None


def get_news(query_key: str) -> Optional[pd.DataFrame]:
    """NewsAPI → 실패 시 GDELT fallback으로 뉴스 반환."""
    query = NEWS_QUERIES.get(query_key, query_key)
    key = f"news_{query_key}"
    cached = cache_get(key, CACHE_TTL["daily"])
    if cached is not None:
        return cached

    df = _fetch_newsapi(query)
    if df is None or df.empty:
        # GDELT fallback
        gdelt_key_map = {
            "IMEC":   "imec_corridor",
            "중동 정세": "israel_conflict",
            "해운":   "suez_red_sea",
            "에너지": "saudi_normalize",
            "BRI 경쟁": "bri_china",
        }
        gdelt_key = gdelt_key_map.get(query_key, "imec_corridor")
        raw = gdelt_articles(gdelt_key)
        if raw is not None and not raw.empty:
            raw["sentiment"] = raw["title"].apply(_sentiment)
            raw["source"] = raw["domain"]
            df = raw[["title", "url", "source", "date", "sentiment"]].copy()

    if df is not None and not df.empty:
        cache_set(key, df)
    return df


def get_all_news() -> dict:
    """모든 키워드 그룹의 뉴스 반환."""
    return {key: get_news(key) for key in NEWS_QUERIES}


def get_sentiment_summary(query_key: str) -> dict:
    """감성 비율 요약 반환."""
    df = get_news(query_key)
    if df is None or df.empty:
        return {"긍정": 0, "부정": 0, "중립": 0}
    counts = df["sentiment"].value_counts()
    total = len(df)
    return {
        "긍정": round(counts.get("긍정", 0) / total * 100, 1),
        "부정": round(counts.get("부정", 0) / total * 100, 1),
        "중립": round(counts.get("중립", 0) / total * 100, 1),
    }
