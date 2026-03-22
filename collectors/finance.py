"""yfinance — 주가 지수, 환율, 원자재 선물."""

import yfinance as yf
import pandas as pd
from typing import Optional
from .db import cache_get, cache_set
from config import YFINANCE_SYMBOLS, CACHE_TTL


def _fetch(symbol: str, period: str = "1y", interval: str = "1d") -> Optional[pd.DataFrame]:
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if df.empty:
            return None
        df = df[["Close"]].rename(columns={"Close": "value"}).reset_index()
        df.columns = ["date", "value"]
        df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
        return df.dropna().reset_index(drop=True)
    except Exception:
        return None


def get_series(name: str, period: str = "1y") -> Optional[pd.DataFrame]:
    """심볼 이름으로 시계열 데이터 가져오기."""
    symbol = YFINANCE_SYMBOLS.get(name)
    if not symbol:
        return None
    key = f"yf_{name}_{period}"
    cached = cache_get(key, CACHE_TTL["daily"])
    if cached is not None:
        cached["date"] = pd.to_datetime(cached["date"])
        return cached
    df = _fetch(symbol, period=period)
    if df is not None:
        cache_set(key, df)
    return df


def get_latest(name: str) -> Optional[float]:
    """최신 종가 반환."""
    df = get_series(name, period="5d")
    if df is None or df.empty:
        return None
    return df["value"].iloc[-1]


def get_pct_change(name: str, days: int = 30) -> Optional[float]:
    """n일 전 대비 변화율(%) 반환."""
    df = get_series(name, period="6mo")
    if df is None or len(df) < 2:
        return None
    recent = df["value"].iloc[-1]
    past = df["value"].iloc[max(0, len(df) - days - 1)]
    return (recent - past) / past * 100 if past else None


def get_multi_index(names: list, period: str = "1y") -> Optional[pd.DataFrame]:
    """여러 지수를 하나의 DataFrame으로 반환 (정규화: 시작점=100)."""
    dfs = {}
    for name in names:
        df = get_series(name, period=period)
        if df is not None and not df.empty:
            dfs[name] = df.set_index("date")["value"]
    if not dfs:
        return None
    combined = pd.DataFrame(dfs).dropna(how="all")
    # 기준 정규화 (첫 유효값 = 100)
    first_valid = combined.apply(lambda s: s.dropna().iloc[0] if not s.dropna().empty else 1)
    return (combined / first_valid * 100).reset_index()
