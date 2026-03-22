"""개요 탭 — IMEC 경로 지도 + 핵심 KPI 카드 + 최신 뉴스."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from config import ROUTE_NODES, ROUTE_LINES, IMEC_COUNTRIES
from collectors import fred, finance, gdelt, news


# ---------------------------------------------------------------------------
# 지도
# ---------------------------------------------------------------------------

def _build_map() -> go.Figure:
    fig = go.Figure()

    # 경로 선 (해상=파랑 점선, 육상=주황 실선)
    colors = ["#2196F3", "#FF9800", "#2196F3"]
    dashes  = ["dot", "solid", "dot"]
    labels  = ["해상 (Indian Ocean)", "육상 (Rail/Road)", "해상 (Mediterranean)"]

    for i, waypoints in enumerate(ROUTE_LINES):
        lats = [p[0] for p in waypoints]
        lons = [p[1] for p in waypoints]
        fig.add_trace(go.Scattergeo(
            lat=lats, lon=lons,
            mode="lines",
            line=dict(width=3, color=colors[i], dash=dashes[i]),
            name=labels[i],
            hoverinfo="name",
        ))

    # 노드 마커
    node_lats  = [n["lat"]   for n in ROUTE_NODES]
    node_lons  = [n["lon"]   for n in ROUTE_NODES]
    node_texts = [n["label"] for n in ROUTE_NODES]

    fig.add_trace(go.Scattergeo(
        lat=node_lats, lon=node_lons,
        mode="markers+text",
        marker=dict(size=12, color="#E91E63", symbol="circle"),
        text=node_texts,
        textposition="top center",
        name="주요 항구/도시",
        hoverinfo="text",
    ))

    fig.update_layout(
        geo=dict(
            projection_type="natural earth",
            showland=True,  landcolor="#F5F5F5",
            showocean=True, oceancolor="#E3F2FD",
            showcoastlines=True, coastlinecolor="#BDBDBD",
            showcountries=True, countrycolor="#E0E0E0",
            center=dict(lat=25, lon=45),
            projection_scale=2.5,
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=380,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


# ---------------------------------------------------------------------------
# KPI 카드
# ---------------------------------------------------------------------------

def _kpi_card(col, label: str, value, unit: str = "", delta=None, delta_suffix: str = "%"):
    with col:
        if value is None:
            st.metric(label, "데이터 없음")
        else:
            v_str = f"{value:,.2f} {unit}".strip()
            d_str = f"{delta:+.1f}{delta_suffix}" if delta is not None else None
            st.metric(label, v_str, d_str)


def _load_kpis():
    kpis = {}

    brent = fred.get_brent()
    if brent is not None and not brent.empty:
        kpis["brent"]       = brent["value"].iloc[-1]
        kpis["brent_delta"] = (brent["value"].iloc[-1] - brent["value"].iloc[-31]) / brent["value"].iloc[-31] * 100 if len(brent) > 30 else None
    else:
        kpis["brent"] = finance.get_latest("brent_f")
        kpis["brent_delta"] = finance.get_pct_change("brent_f", 30)

    kpis["natgas"]       = fred.get_latest_value("natgas")
    kpis["bdry"]         = finance.get_latest("bdry")
    kpis["bdry_delta"]   = finance.get_pct_change("bdry", 30)
    kpis["nifty"]        = finance.get_latest("nifty50")
    kpis["nifty_delta"]  = finance.get_pct_change("nifty50", 30)
    kpis["ils_usd"]      = finance.get_latest("ils_usd")
    kpis["inr_usd"]      = finance.get_latest("inr_usd")
    kpis["israel_risk"]  = gdelt.get_risk_score("israel_conflict")
    kpis["imec_score"]   = gdelt.get_risk_score("imec_corridor")
    return kpis


# ---------------------------------------------------------------------------
# 메인 렌더링
# ---------------------------------------------------------------------------

def render():
    st.subheader("IMEC 경로")
    with st.spinner("지도 로딩 중..."):
        fig = _build_map()
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("핵심 지표")
    with st.spinner("지표 로딩 중..."):
        kpis = _load_kpis()

    cols = st.columns(4)
    _kpi_card(cols[0], "Brent 원유 ($/bbl)",    kpis.get("brent"),       "$",   kpis.get("brent_delta"))
    _kpi_card(cols[1], "천연가스 ($/MMBtu)",     kpis.get("natgas"),      "$")
    _kpi_card(cols[2], "BDRY (BDI 프록시)",      kpis.get("bdry"),        "",    kpis.get("bdry_delta"))
    _kpi_card(cols[3], "Nifty 50 (인도)",        kpis.get("nifty"),       "",    kpis.get("nifty_delta"))

    cols2 = st.columns(4)
    _kpi_card(cols2[0], "ILS/USD (이스라엘)",    kpis.get("ils_usd"),     "₪")
    _kpi_card(cols2[1], "INR/USD (인도)",         kpis.get("inr_usd"),     "₹")
    _kpi_card(cols2[2], "이스라엘 리스크 지수",   kpis.get("israel_risk"), "/100")
    _kpi_card(cols2[3], "IMEC 뉴스 활성도",       kpis.get("imec_score"),  "/100")

    st.divider()
    st.subheader("최근 주요 뉴스")
    with st.spinner("뉴스 로딩 중..."):
        df = news.get_news("IMEC")
    if df is not None and not df.empty:
        for _, row in df.head(5).iterrows():
            sentiment_color = {"긍정": "🟢", "부정": "🔴", "중립": "⚪"}.get(row.get("sentiment", "중립"), "⚪")
            st.markdown(f"{sentiment_color} **[{row['title']}]({row['url']})** — *{row.get('source', '')}* `{row.get('date', '')}`")
    else:
        st.info("뉴스 데이터를 불러올 수 없습니다. NewsAPI 키를 확인하거나 잠시 후 새로고침 해주세요.")

    st.divider()
    st.caption("참여국: " + " | ".join(
        f"{v['flag']} {v['name']} ({v['role']})" for v in IMEC_COUNTRIES.values()
    ))
