"""엘케이켐(489500) 모니터링 탭."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from collectors import lkchem


def _delta_color(val):
    if val is None:
        return "off"
    return "normal" if val >= 0 else "inverse"


def render():
    st.header("📈 엘케이켐 (489500) 모니터링")
    st.caption("반도체 소재(DIS·PCP·HfCl₄) 전문기업 | 코스닥 상장")

    # -----------------------------------------------------------------------
    # 주가 KPI
    # -----------------------------------------------------------------------
    info = lkchem.get_stock_info()
    price   = info.get("price")
    change  = info.get("change")
    mktcap  = info.get("market_cap")
    per     = info.get("per")
    pbr     = info.get("pbr")
    hi52    = info.get("52w_high")
    lo52    = info.get("52w_low")

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric(
            "현재 주가 (KRW)",
            f"{price:,.0f}" if price else "N/A",
            delta=f"{change:+.2f}%" if change is not None else None,
            delta_color=_delta_color(change),
        )
    with c2:
        st.metric("시가총액", f"{mktcap/1e8:,.0f}억" if mktcap else "N/A")
    with c3:
        st.metric("PER", f"{per:.1f}x" if per else "N/A")
    with c4:
        st.metric("PBR", f"{pbr:.2f}x" if pbr else "N/A")
    with c5:
        hi_str = f"{hi52:,.0f}" if hi52 else "N/A"
        lo_str = f"{lo52:,.0f}" if lo52 else "N/A"
        st.metric("52주 고/저", f"{hi_str} / {lo_str}")

    st.divider()

    # -----------------------------------------------------------------------
    # 주가 차트 + 재무 트렌드
    # -----------------------------------------------------------------------
    col_chart, col_fin = st.columns([3, 2])

    with col_chart:
        st.subheader("주가 추이 (1년)")
        period_opt = st.radio(
            "기간", ["6mo", "1y", "2y"], index=1, horizontal=True,
            key="lkchem_period",
        )
        hist = lkchem.get_stock_history(period_opt)
        if hist is not None and not hist.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hist["date"], y=hist["close"],
                mode="lines", name="종가",
                line=dict(color="#4C9BE8", width=2),
                fill="tozeroy", fillcolor="rgba(76,155,232,0.1)",
            ))
            fig.update_layout(
                height=300,
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis_title=None, yaxis_title="KRW",
                hovermode="x unified",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("주가 데이터를 불러올 수 없습니다.")

    with col_fin:
        st.subheader("연간 재무 요약")
        fin = lkchem.get_financials_static()
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=fin["연도"], y=fin["매출(억)"], name="매출",
            marker_color="#4C9BE8",
        ))
        fig2.add_trace(go.Bar(
            x=fin["연도"], y=fin["영업이익(억)"], name="영업이익",
            marker_color="#F4A261",
        ))
        fig2.add_trace(go.Scatter(
            x=fin["연도"], y=fin["영업이익률(%)"], name="영업이익률(%)",
            yaxis="y2", mode="lines+markers",
            line=dict(color="#E76F51", dash="dash"),
        ))
        fig2.update_layout(
            height=300,
            barmode="group",
            margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", y=1.1),
            yaxis=dict(title="억 원"),
            yaxis2=dict(title="%", overlaying="y", side="right", showgrid=False),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.caption("※ 2025E는 증권사 컨센서스 추정치")

    st.divider()

    # -----------------------------------------------------------------------
    # 연구·제품 파이프라인
    # -----------------------------------------------------------------------
    st.subheader("🔬 연구·제품 파이프라인")
    pipeline = lkchem.get_pipeline()
    stage_colors = {"완료": "🟢", "진행": "🔵", "예정": "⚪"}
    pipeline["단계"] = pipeline["단계"].map(lambda s: f"{stage_colors.get(s, '')} {s}")
    st.dataframe(
        pipeline,
        use_container_width=True,
        hide_index=True,
        column_config={
            "단계":     st.column_config.TextColumn("단계", width=80),
            "항목":     st.column_config.TextColumn("항목", width=280),
            "목표 시기": st.column_config.TextColumn("목표 시기", width=100),
            "비고":     st.column_config.TextColumn("비고", width=240),
        },
    )

    # 수동 파이프라인 편집 (펼침)
    with st.expander("✏️ 파이프라인 수동 편집"):
        st.caption("아래 영역에 JSON 형식으로 파이프라인을 입력하면 저장됩니다.")
        import json
        from collectors.db import manual_set
        default_json = pipeline.assign(
            단계=pipeline["단계"].str.lstrip("🟢🔵⚪ ")
        ).to_json(orient="records", force_ascii=False, indent=2)
        new_json = st.text_area("파이프라인 JSON", value=default_json, height=300)
        if st.button("저장", key="pipeline_save"):
            try:
                df_new = pd.DataFrame(json.loads(new_json))
                manual_set("lkchem_pipeline", df_new)
                st.success("저장되었습니다.")
                st.rerun()
            except Exception as e:
                st.error(f"저장 실패: {e}")

    st.divider()

    # -----------------------------------------------------------------------
    # DART 공시 + 뉴스
    # -----------------------------------------------------------------------
    col_dart, col_news = st.columns(2)

    with col_dart:
        st.subheader("📋 최신 DART 공시")
        disclosures = lkchem.get_disclosures(15)
        if disclosures is not None and not disclosures.empty:
            for _, row in disclosures.iterrows():
                st.markdown(
                    f"**{row['날짜']}** · [{row['제목']}]({row['공시링크']})  \n"
                    f"<small>{row['종류']}</small>",
                    unsafe_allow_html=True,
                )
        else:
            st.warning("DART API 키가 설정되지 않았습니다.")
            st.markdown(
                "공시 데이터를 보려면 [DART OpenAPI](https://opendart.fss.or.kr)에서 "
                "무료 API 키를 발급받고 Streamlit Cloud → Settings → Secrets에 추가하세요."
            )
            st.code("DART_API_KEY = \"발급받은_키\"")
            st.markdown("**DART 바로가기:** [엘케이켐 공시 목록](https://dart.fss.or.kr/corp/searchCorpInfo.do?selectKey=489500)")

    with col_news:
        st.subheader("📰 관련 뉴스 (GDELT)")
        news_df = lkchem.get_news(20)
        if news_df is not None and not news_df.empty:
            for _, row in news_df.iterrows():
                title = row.get("title", "")
                url   = row.get("url", "#")
                src   = row.get("source", "")
                date  = row.get("date", "")
                st.markdown(
                    f"**{date}** · [{title}]({url})  \n<small>{src}</small>",
                    unsafe_allow_html=True,
                )
        else:
            st.info("현재 관련 뉴스가 없습니다. (GDELT 30일 기준)")
            st.markdown(
                "페로브스카이트·반도체 소재 관련 최신 동향:  \n"
                "- [Google 뉴스: LKChem](https://news.google.com/search?q=LKChem+semiconductor)  \n"
                "- [네이버 뉴스: 엘케이켐](https://search.naver.com/search.naver?where=news&query=엘케이켐)"
            )
