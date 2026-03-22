"""수동/반자동 데이터 수집 — UNCTAD, DP World, 하이파 항만청, IEA.

이 모듈은 공식 API가 없거나 PDF/웹 형식으로만 제공되는 데이터를 다룹니다.
자동 수집이 가능한 경우 함수를 구현하고, 그렇지 않으면 수동 입력 인터페이스를
대시보드에서 제공합니다.
"""

import requests
import pandas as pd
from bs4 import BeautifulSoup
from typing import Optional
from .db import cache_get, cache_set, manual_get
from config import CACHE_TTL


# ---------------------------------------------------------------------------
# UNCTAD — 수에즈 운하 통항 통계
# ---------------------------------------------------------------------------

def get_suez_stats() -> Optional[pd.DataFrame]:
    """수에즈 운하 통항량 — 수동 입력 데이터 반환."""
    df = manual_get("suez_stats")
    if df is not None:
        return df
    # 데이터 없을 때 구조 예시 반환 (실제 값은 수동 입력 필요)
    return pd.DataFrame({
        "month":          ["2024-01", "2024-02", "2024-03"],
        "transits":       [None, None, None],
        "net_tonnage_mt": [None, None, None],
        "note":           ["수동 입력 필요", "수동 입력 필요", "수동 입력 필요"],
    })


# ---------------------------------------------------------------------------
# DP World — 제벨알리 TEU (분기 실적 보고서)
# ---------------------------------------------------------------------------

def get_jebel_ali_teu() -> Optional[pd.DataFrame]:
    """제벨알리 항구 TEU — 수동 입력 데이터 반환."""
    df = manual_get("jebel_ali_teu")
    if df is not None:
        return df
    return pd.DataFrame({
        "quarter":  ["2023Q1", "2023Q2", "2023Q3", "2023Q4"],
        "teu_000s": [None, None, None, None],
        "note":     ["DP World 분기 보고서 입력 필요"] * 4,
    })


# ---------------------------------------------------------------------------
# 이스라엘 항만청 — 하이파 항구 물동량
# ---------------------------------------------------------------------------

def get_haifa_port() -> Optional[pd.DataFrame]:
    """하이파 항구 물동량 — 수동 입력 데이터 반환."""
    df = manual_get("haifa_port")
    if df is not None:
        return df
    return pd.DataFrame({
        "month":      ["2024-01", "2024-02", "2024-03"],
        "containers": [None, None, None],
        "cargo_tons": [None, None, None],
        "note":       ["이스라엘 항만청 월간 통계 입력 필요"] * 3,
    })


# ---------------------------------------------------------------------------
# IEA — 중동 에너지 흐름 리포트 요약
# ---------------------------------------------------------------------------

def get_iea_summary() -> Optional[pd.DataFrame]:
    """IEA 중동 에너지 흐름 — 수동 요약 입력 데이터 반환."""
    df = manual_get("iea_summary")
    if df is not None:
        return df
    return pd.DataFrame({
        "report_month": ["2024-03"],
        "lng_exports_bcm": [None],
        "pipeline_flows":  [None],
        "key_finding":     ["IEA Gas Market Report 요약 입력 필요"],
    })


# ---------------------------------------------------------------------------
# Freightos Baltic Index (FBX) — 컨테이너 운임
# ---------------------------------------------------------------------------

def scrape_fbx() -> Optional[pd.DataFrame]:
    """Freightos 웹사이트에서 FBX 글로벌 컨테이너 운임 스크래핑."""
    key = "fbx_rate"
    cached = cache_get(key, CACHE_TTL["daily"])
    if cached is not None:
        return cached
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get("https://fbx.freightos.com/", headers=headers, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
        # 실제 FBX 값 파싱 (사이트 구조 변경 시 업데이트 필요)
        # 현재는 수동 입력으로 폴백
        return None
    except Exception:
        return None
