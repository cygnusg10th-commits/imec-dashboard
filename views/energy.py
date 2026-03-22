"""에너지 탭 — 유가, 천연가스, 원유 생산·수입, IEA 리포트."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from collectors import fred, eia, scraper
from collectors.db import manual_set


def _oil_price_chart():
    st.markdown("#### 국제 유가 추이")
    brent_df = fred.get_brent()
    wti_df   = fred.get_wti()

    if brent_df is None and wti_df is None:
        # FRED 키 없을 때 안내
        st.warning("FRED API 키가 설정되지 않았습니다. `.env` 파일에 `FRED_API_KEY`를 입력해주세요.")
        return

    fig = go.Figure()
    if brent_df is not None:
        fig.add_trace(go.Scatter(
            x=brent_df["date"], y=brent_df["value"],
            mode="lines", name="Brent ($/bbl)",
            line=dict(color="#D32F2F", width=2),
        ))
    if wti_df is not None:
        fig.add_trace(go.Scatter(
            x=wti_df["date"], y=wti_df["value"],
            mode="lines", name="WTI ($/bbl)",
            line=dict(color="#F57C00", width=2),
        ))
    fig.update_layout(
        height=320, xaxis_title="", yaxis_title="USD/bbl",
        margin=dict(l=0, r=0, t=20, b=0),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="top", y=-0.1),
    )
    st.plotly_chart(fig, use_container_width=True)


def _natgas_chart():
    st.markdown("#### 천연가스 가격 (Henry Hub)")
    df = fred.get_natgas()
    if df is None:
        st.info("FRED API 키 설정 후 데이터를 불러올 수 있습니다.")
        return
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["value"],
        mode="lines", name="Henry Hub ($/MMBtu)",
        line=dict(color="#1565C0", width=2),
        fill="tozeroy", fillcolor="rgba(21,101,192,0.1)",
    ))
    fig.update_layout(
        height=260, xaxis_title="", yaxis_title="USD/MMBtu",
        margin=dict(l=0, r=0, t=20, b=0),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)


def _production_chart():
    st.markdown("#### 사우디아라비아 & UAE 원유 생산량")
    saudi_df = eia.get_saudi_production()
    uae_df   = eia.get_uae_production()

    if saudi_df is None and uae_df is None:
        st.warning("EIA API 키가 설정되지 않았습니다. `.env` 파일에 `EIA_API_KEY`를 입력해주세요.")
        return

    fig = go.Figure()
    if saudi_df is not None:
        fig.add_trace(go.Scatter(
            x=saudi_df["period"], y=saudi_df["value"],
            mode="lines+markers", name="사우디 (천 배럴/일)",
            line=dict(color="#388E3C", width=2),
        ))
    if uae_df is not None:
        fig.add_trace(go.Scatter(
            x=uae_df["period"], y=uae_df["value"],
            mode="lines+markers", name="UAE (천 배럴/일)",
            line=dict(color="#0288D1", width=2),
        ))
    fig.update_layout(
        height=300, xaxis_title="", yaxis_title="천 배럴/일 (TBPD)",
        margin=dict(l=0, r=0, t=20, b=0),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="top", y=-0.1),
    )
    st.plotly_chart(fig, use_container_width=True)


def _india_imports_chart():
    st.markdown("#### 인도 원유 수입량")
    df = eia.get_india_imports()
    if df is None:
        st.info("EIA API 키 설정 후 데이터를 불러올 수 있습니다.")
        return
    fig = px.bar(df.tail(24), x="period", y="value",
                 color_discrete_sequence=["#7B1FA2"])
    fig.update_layout(
        height=260, xaxis_title="", yaxis_title="천 배럴/일",
        margin=dict(l=0, r=0, t=20, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)


def _iea_panel():
    st.markdown("#### IEA 중동 에너지 흐름 리포트")
    df = scraper.get_iea_summary()
    has_data = df is not None and df["lng_exports_bcm"].notna().any()

    if has_data:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("IEA Gas Market Report 데이터가 없습니다. 아래에서 월간 요약을 입력하세요.")

    with st.expander("IEA 리포트 수동 입력"):
        st.markdown("**출처:** [IEA Gas Market Report](https://www.iea.org/reports/gas-market-report)")
        with st.form("iea_form"):
            month    = st.text_input("리포트 월 (YYYY-MM)")
            lng_exp  = st.number_input("중동 LNG 수출 (BCM)", min_value=0.0, step=0.1)
            finding  = st.text_area("핵심 내용 요약")
            if st.form_submit_button("저장"):
                new_row = pd.DataFrame([{
                    "report_month": month,
                    "lng_exports_bcm": lng_exp,
                    "pipeline_flows": None,
                    "key_finding": finding,
                }])
                existing = scraper.get_iea_summary()
                if has_data:
                    updated = pd.concat([existing[existing["lng_exports_bcm"].notna()], new_row], ignore_index=True)
                else:
                    updated = new_row
                manual_set("iea_summary", updated, "IEA 에너지 흐름")
                st.success("저장되었습니다.")
                st.rerun()


def render():
    st.subheader("에너지")

    col1, col2 = st.columns([3, 2])
    with col1:
        _oil_price_chart()
    with col2:
        _natgas_chart()

    st.divider()
    col3, col4 = st.columns(2)
    with col3:
        _production_chart()
    with col4:
        _india_imports_chart()

    st.divider()
    _iea_panel()

    st.divider()
    st.caption("데이터 출처: FRED API (유가·가스), EIA API (생산·수입), IEA (수동 입력)")
