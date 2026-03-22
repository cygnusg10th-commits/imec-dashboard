"""지정학 탭 — GDELT 리스크 지수, 참여국 증시, TeleGeography 케이블."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from config import GDELT_QUERIES, IMEC_COUNTRIES
from collectors import gdelt, finance


_QUERY_LABELS = {
    "israel_conflict":  "이스라엘 분쟁",
    "suez_red_sea":     "수에즈/홍해 해운",
    "imec_corridor":    "IMEC 회랑",
    "bri_china":        "BRI/중국",
    "saudi_normalize":  "사우디 정상화",
    "india_trade":      "인도 무역",
}

_QUERY_COLORS = {
    "israel_conflict":  "#D32F2F",
    "suez_red_sea":     "#1565C0",
    "imec_corridor":    "#2E7D32",
    "bri_china":        "#E65100",
    "saudi_normalize":  "#6A1B9A",
    "india_trade":      "#00695C",
}


def _risk_scorecard():
    st.markdown("#### 주제별 리스크 스코어 (GDELT 뉴스 볼륨 기반)")
    cols = st.columns(3)
    keys = list(GDELT_QUERIES.keys())
    for i, key in enumerate(keys):
        score = gdelt.get_risk_score(key)
        with cols[i % 3]:
            if score is None:
                st.metric(_QUERY_LABELS.get(key, key), "로딩 중...")
            else:
                color = "🔴" if score > 65 else ("🟡" if score > 35 else "🟢")
                st.metric(_QUERY_LABELS.get(key, key), f"{color} {score}/100")
    st.caption("스코어: 최근 7일 vs 이전 7일 뉴스 볼륨 비율 (0=낮음, 100=높음)")


def _gdelt_timeline_chart():
    st.markdown("#### GDELT 뉴스 볼륨 타임라인 (90일)")
    with st.spinner("GDELT 데이터 로딩 중..."):
        timelines = gdelt.get_all_timelines("90d")

    if not timelines:
        st.warning("GDELT 데이터를 불러올 수 없습니다. 잠시 후 새로고침 해주세요.")
        return

    selected = st.multiselect(
        "표시할 주제 선택",
        options=list(timelines.keys()),
        default=["israel_conflict", "imec_corridor", "bri_china"],
        format_func=lambda k: _QUERY_LABELS.get(k, k),
    )
    if not selected:
        return

    fig = go.Figure()
    for key in selected:
        df = timelines.get(key)
        if df is None or df.empty:
            continue
        fig.add_trace(go.Scatter(
            x=df["date"], y=df["value"],
            mode="lines", name=_QUERY_LABELS.get(key, key),
            line=dict(color=_QUERY_COLORS.get(key, "#666"), width=2),
        ))
    fig.update_layout(
        height=320, xaxis_title="", yaxis_title="뉴스 볼륨 지수",
        margin=dict(l=0, r=0, t=20, b=0),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="top", y=-0.15, title_text=""),
    )
    st.plotly_chart(fig, use_container_width=True)


def _stock_indices_chart():
    st.markdown("#### 참여국 증시 (정규화: 1년 시작=100)")
    indices = {
        "nifty50": "🇮🇳 Nifty 50",
        "ta125":   "🇮🇱 TA-125",
        "aramco":  "🇸🇦 Aramco",
    }
    df = finance.get_multi_index(list(indices.keys()), period="1y")
    if df is None or df.empty:
        st.info("증시 데이터를 불러오는 중입니다.")
        return
    fig = go.Figure()
    colors = {"nifty50": "#FF6F00", "ta125": "#1565C0", "aramco": "#2E7D32"}
    for key, label in indices.items():
        if key not in df.columns:
            continue
        fig.add_trace(go.Scatter(
            x=df["date"], y=df[key],
            mode="lines", name=label,
            line=dict(color=colors.get(key, "#666"), width=2),
        ))
    fig.add_hline(y=100, line_dash="dash", line_color="gray", opacity=0.4)
    fig.update_layout(
        height=300, xaxis_title="", yaxis_title="지수 (시작=100)",
        margin=dict(l=0, r=0, t=20, b=0),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="top", y=-0.1, title_text=""),
    )
    st.plotly_chart(fig, use_container_width=True)


def _cable_map_panel():
    st.markdown("#### TeleGeography — 해저 데이터 케이블")
    st.markdown(
        "IMEC는 인도-중동-유럽을 잇는 해저 데이터 케이블도 포함합니다. "
        "TeleGeography의 인터랙티브 케이블 맵을 통해 현황을 확인할 수 있습니다."
    )
    col1, col2 = st.columns([2, 1])
    with col1:
        st.link_button(
            "TeleGeography SubmarineCableMap 열기",
            "https://www.submarinecablemap.com/",
            width="stretch",
        )
    with col2:
        st.link_button(
            "TeleGeography 데이터",
            "https://www.telegeography.com/research-services/",
            width="stretch",
        )
    st.caption("상세 용량·트래픽 데이터는 TeleGeography 연간 리포트(유료)에서 제공됩니다.")


def render():
    st.subheader("지정학")

    with st.spinner("리스크 스코어 계산 중..."):
        _risk_scorecard()

    st.divider()
    _gdelt_timeline_chart()

    st.divider()
    _stock_indices_chart()

    st.divider()
    _cable_map_panel()

    st.divider()
    st.caption(
        "GDELT 스코어: 뉴스 볼륨 기반 간접 지표 (높을수록 해당 주제 뉴스 급증) | "
        "출처: GDELT Project, Yahoo Finance"
    )
