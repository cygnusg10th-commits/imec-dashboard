"""해운·물류 탭 — BDI, 수에즈 통항량, 항만 처리량, 운임 지수."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from collectors import finance, scraper
from collectors.db import manual_set


def _bdi_chart():
    st.markdown("#### BDRY ETF (Baltic Dry Index 프록시)")
    df = finance.get_series("bdry", period="2y")
    if df is None or df.empty:
        st.warning("BDRY 데이터를 불러올 수 없습니다.")
        return
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["value"],
        mode="lines", name="BDRY",
        line=dict(color="#1976D2", width=2),
        fill="tozeroy", fillcolor="rgba(25,118,210,0.1)",
    ))
    fig.update_layout(
        height=300,
        xaxis_title="", yaxis_title="USD",
        margin=dict(l=0, r=0, t=20, b=0),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)
    latest = df["value"].iloc[-1]
    prev30 = df["value"].iloc[-31] if len(df) > 30 else df["value"].iloc[0]
    delta  = (latest - prev30) / prev30 * 100
    st.caption(f"최신: ${latest:,.2f}  |  30일 변화: {delta:+.1f}%")


def _shipping_indices_chart():
    st.markdown("#### 해운 관련 지수 비교 (정규화: 시작=100)")
    symbols = ["bdry", "brent_f"]
    df = finance.get_multi_index(symbols, period="1y")
    if df is None:
        st.info("데이터를 불러오는 중입니다.")
        return
    fig = go.Figure()
    colors = {"bdry": "#1976D2", "brent_f": "#E65100"}
    labels = {"bdry": "BDRY (해운)", "brent_f": "Brent 선물"}
    for col in [c for c in df.columns if c != "date"]:
        fig.add_trace(go.Scatter(
            x=df["date"], y=df[col],
            mode="lines", name=labels.get(col, col),
            line=dict(color=colors.get(col, "#666"), width=2),
        ))
    fig.add_hline(y=100, line_dash="dash", line_color="gray", opacity=0.5)
    fig.update_layout(
        height=280,
        xaxis_title="", yaxis_title="지수 (시작=100)",
        margin=dict(l=0, r=0, t=20, b=0),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="top", y=-0.15),
    )
    st.plotly_chart(fig, use_container_width=True)


def _suez_panel():
    st.markdown("#### 수에즈 운하 통항량")
    df = scraper.get_suez_stats()
    has_data = df is not None and not df.empty and df["transits"].notna().any()

    if has_data:
        fig = px.bar(df, x="month", y="transits", title="",
                     color_discrete_sequence=["#0288D1"])
        fig.update_layout(height=250, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("수에즈 통항량 데이터가 없습니다. 아래에서 수동 입력하세요.")

    with st.expander("수동 데이터 입력 (UNCTAD / 수에즈 운하청)"):
        st.markdown("**데이터 출처:** [UNCTAD Maritime Statistics](https://unctadstat.unctad.org) | [Suez Canal Authority](https://www.suezcanal.gov.eg/)")
        with st.form("suez_form"):
            month   = st.text_input("월 (YYYY-MM)", placeholder="2024-03")
            transit = st.number_input("통항 횟수", min_value=0, step=1)
            tonnage = st.number_input("순 톤수 (백만 톤)", min_value=0.0, step=0.1)
            if st.form_submit_button("저장"):
                existing = scraper.get_suez_stats()
                new_row = pd.DataFrame([{"month": month, "transits": transit,
                                          "net_tonnage_mt": tonnage, "note": "수동 입력"}])
                if existing is not None and existing["transits"].notna().any():
                    updated = pd.concat([existing, new_row], ignore_index=True)
                else:
                    updated = new_row
                manual_set("suez_stats", updated, "수에즈 통항량")
                st.success("저장되었습니다.")
                st.rerun()


def _port_panel():
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 제벨알리 TEU (DP World)")
        df = scraper.get_jebel_ali_teu()
        has_data = df is not None and df["teu_000s"].notna().any()
        if has_data:
            fig = px.bar(df, x="quarter", y="teu_000s",
                         color_discrete_sequence=["#388E3C"])
            fig.update_layout(height=220, margin=dict(l=0, r=0, t=10, b=0),
                              yaxis_title="TEU (천)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("DP World 분기 보고서에서 수동 입력 필요")
        with st.expander("입력"):
            with st.form("dpw_form"):
                qtr = st.text_input("분기 (예: 2024Q1)")
                teu = st.number_input("TEU (천 단위)", min_value=0.0, step=100.0)
                if st.form_submit_button("저장"):
                    existing = scraper.get_jebel_ali_teu()
                    new_row = pd.DataFrame([{"quarter": qtr, "teu_000s": teu, "note": "수동 입력"}])
                    updated = pd.concat([existing[existing["teu_000s"].notna()], new_row], ignore_index=True) if has_data else new_row
                    manual_set("jebel_ali_teu", updated)
                    st.success("저장되었습니다.")
                    st.rerun()

    with col2:
        st.markdown("#### 하이파 항구 (이스라엘)")
        df = scraper.get_haifa_port()
        has_data = df is not None and df["containers"].notna().any()
        if has_data:
            fig = px.line(df, x="month", y="containers",
                          color_discrete_sequence=["#7B1FA2"])
            fig.update_layout(height=220, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("이스라엘 항만청 월간 통계 수동 입력 필요")
        with st.expander("입력"):
            with st.form("haifa_form"):
                mnth = st.text_input("월 (YYYY-MM)")
                cont = st.number_input("컨테이너 (TEU)", min_value=0, step=1000)
                if st.form_submit_button("저장"):
                    existing = scraper.get_haifa_port()
                    new_row = pd.DataFrame([{"month": mnth, "containers": cont,
                                             "cargo_tons": None, "note": "수동 입력"}])
                    updated = pd.concat([existing[existing["containers"].notna()], new_row], ignore_index=True) if has_data else new_row
                    manual_set("haifa_port", updated)
                    st.success("저장되었습니다.")
                    st.rerun()


def render():
    st.subheader("해운 & 물류")

    _bdi_chart()
    st.divider()
    _shipping_indices_chart()
    st.divider()
    _suez_panel()
    st.divider()
    _port_panel()

    st.divider()
    st.caption(
        "📌 BDRY: Breakwave Dry Bulk Shipping ETF (BDI 프록시) | "
        "수에즈/항만 데이터: 수동 입력 필요 (UNCTAD, DP World, 이스라엘 항만청)"
    )
