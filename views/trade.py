"""무역·경제 탭 — GDP 비교, 교역 히트맵, 환율, FDI."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from config import IMEC_COUNTRIES
from collectors import worldbank, fred, finance, comtrade


def _gdp_growth_chart():
    st.markdown("#### 참여국 GDP 성장률 (%)")
    df = worldbank.get_gdp_growth()
    if df is None or df.empty:
        st.info("World Bank 데이터를 불러오는 중입니다.")
        return
    # 최근 5년
    recent = df[df["year"] >= df["year"].max() - 4]
    country_names = {k: v["flag"] + " " + v["name"] for k, v in IMEC_COUNTRIES.items()}
    recent = recent.copy()
    recent["country_name"] = recent["country"].map(country_names).fillna(recent["country"])

    fig = px.line(
        recent, x="year", y="value", color="country_name",
        markers=True, labels={"value": "GDP 성장률 (%)", "year": "", "country_name": "국가"},
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    fig.update_layout(
        height=320, margin=dict(l=0, r=0, t=20, b=0),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="top", y=-0.15, title_text=""),
    )
    st.plotly_chart(fig, use_container_width=True)


def _gdp_bar_chart():
    st.markdown("#### 참여국 GDP 규모 (조 달러, 최신 연도)")
    df = worldbank.get_gdp_usd()
    if df is None or df.empty:
        st.info("데이터를 불러오는 중입니다.")
        return
    latest_year = df["year"].max()
    latest = df[df["year"] == latest_year].copy()
    country_names = {k: v["flag"] + " " + v["name"] for k, v in IMEC_COUNTRIES.items()}
    latest["country_name"] = latest["country"].map(country_names).fillna(latest["country"])
    latest = latest.sort_values("value", ascending=True)

    fig = px.bar(latest, x="value", y="country_name", orientation="h",
                 color="value", color_continuous_scale="Blues",
                 labels={"value": "GDP (조 USD)", "country_name": ""})
    fig.update_layout(
        height=280, margin=dict(l=0, r=0, t=20, b=0),
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"기준 연도: {latest_year}")


def _trade_heatmap():
    st.markdown("#### 양자 교역 매트릭스 (수출 USD)")
    df = comtrade.get_trade_matrix()
    if df is None or df.empty:
        st.info("UN Comtrade 데이터를 불러오는 중입니다. 잠시 후 새로고침 해주세요.")
        return
    latest_year = df["year"].max()
    df_year = df[df["year"] == latest_year]
    pivot = df_year.pivot_table(index="reporter", columns="partner", values="trade_usd", aggfunc="sum")
    pivot_bn = pivot / 1e9  # 십억 달러

    fig = px.imshow(
        pivot_bn, text_auto=".1f",
        color_continuous_scale="YlOrRd",
        labels=dict(x="수입국", y="수출국", color="십억 USD"),
        aspect="auto",
    )
    fig.update_layout(
        height=300, margin=dict(l=0, r=0, t=20, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"기준 연도: {latest_year} | 출처: UN Comtrade")


def _fx_table():
    st.markdown("#### 환율 현황")
    pairs = [
        ("inr_usd",  "INR/USD",  "🇮🇳 인도 루피"),
        ("ils_usd",  "ILS/USD",  "🇮🇱 이스라엘 세켈"),
        ("eur_usd",  "EUR/USD",  "🇪🇺 유로"),
    ]
    rows = []
    for key, label, flag_name in pairs:
        df = finance.get_series(key, period="6mo")
        if df is not None and not df.empty:
            latest = df["value"].iloc[-1]
            delta  = finance.get_pct_change(key, 30) or 0
            rows.append({"통화": flag_name, "심볼": label, "현재": f"{latest:.4f}", "30일 변화": f"{delta:+.2f}%"})
    # FRED USD/INR (역수)
    usd_inr = fred.get_usd_inr()
    if usd_inr is not None and not usd_inr.empty:
        v = 1 / usd_inr["value"].iloc[-1]
        rows.append({"통화": "🇮🇳 인도 루피 (FRED)", "심볼": "INR/USD", "현재": f"{v:.4f}", "30일 변화": "—"})

    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("환율 데이터를 불러올 수 없습니다.")


def _fdi_chart():
    st.markdown("#### FDI 순유입 (GDP 대비 %)")
    df = worldbank.get_fdi()
    if df is None or df.empty:
        st.info("데이터를 불러오는 중입니다.")
        return
    recent = df[df["year"] >= df["year"].max() - 4]
    country_names = {k: v["flag"] + " " + v["name"] for k, v in IMEC_COUNTRIES.items()}
    recent = recent.copy()
    recent["country_name"] = recent["country"].map(country_names).fillna(recent["country"])

    fig = px.bar(
        recent, x="year", y="value", color="country_name", barmode="group",
        labels={"value": "FDI (% GDP)", "year": "", "country_name": "국가"},
    )
    fig.update_layout(
        height=280, margin=dict(l=0, r=0, t=20, b=0),
        legend=dict(orientation="h", yanchor="top", y=-0.2, title_text=""),
    )
    st.plotly_chart(fig, use_container_width=True)


def render():
    st.subheader("무역 & 경제")

    col1, col2 = st.columns(2)
    with col1:
        _gdp_growth_chart()
    with col2:
        _gdp_bar_chart()

    st.divider()
    _trade_heatmap()

    st.divider()
    col3, col4 = st.columns(2)
    with col3:
        _fx_table()
    with col4:
        _fdi_chart()

    st.divider()
    st.caption("데이터 출처: World Bank Open Data, UN Comtrade, Yahoo Finance, FRED")
