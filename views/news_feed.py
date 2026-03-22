"""뉴스 탭 — 키워드별 최신 헤드라인 + 감성 분석."""

import streamlit as st
import plotly.express as px
import pandas as pd
from config import NEWS_QUERIES
from collectors import news, gdelt


_QUERY_ICONS = {
    "IMEC":   "🛤️",
    "중동 정세": "⚔️",
    "해운":   "🚢",
    "에너지": "⚡",
    "BRI 경쟁": "🇨🇳",
}


def _sentiment_bar(summary: dict, label: str):
    total = sum(summary.values())
    if total == 0:
        return
    df = pd.DataFrame([
        {"감성": "긍정", "비율": summary["긍정"], "color": "#4CAF50"},
        {"감성": "중립", "비율": summary["중립"], "color": "#9E9E9E"},
        {"감성": "부정", "비율": summary["부정"], "color": "#F44336"},
    ])
    fig = px.bar(df, x="비율", y="감성", orientation="h",
                 color="감성", color_discrete_map={"긍정": "#4CAF50", "중립": "#9E9E9E", "부정": "#F44336"},
                 text="비율")
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="inside")
    fig.update_layout(
        height=120, margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False, xaxis_title="%", yaxis_title="",
        xaxis_range=[0, 100],
    )
    st.plotly_chart(fig, use_container_width=True)


def _news_section(query_key: str):
    icon = _QUERY_ICONS.get(query_key, "📰")
    with st.expander(f"{icon} {query_key}", expanded=(query_key == "IMEC")):
        with st.spinner("뉴스 로딩 중..."):
            df       = news.get_news(query_key)
            summary  = news.get_sentiment_summary(query_key)

        col1, col2 = st.columns([3, 1])
        with col1:
            if df is not None and not df.empty:
                for _, row in df.head(8).iterrows():
                    s = row.get("sentiment", "중립")
                    badge = {"긍정": "🟢", "부정": "🔴", "중립": "⚪"}.get(s, "⚪")
                    source = row.get("source", row.get("domain", ""))
                    date   = str(row.get("date", ""))[:10]
                    title  = row.get("title", "")
                    url    = row.get("url", "#")
                    st.markdown(f"{badge} [{title}]({url})  \n`{source}` · `{date}`")
            else:
                st.info("뉴스를 불러올 수 없습니다. NewsAPI 키 확인 또는 새로고침 해주세요.")

        with col2:
            st.caption("감성 분포")
            _sentiment_bar(summary, query_key)
            pos = summary.get("긍정", 0)
            neg = summary.get("부정", 0)
            net = pos - neg
            color = "green" if net > 0 else ("red" if net < 0 else "gray")
            st.markdown(f"**순 감성:** :{color}[{net:+.1f}%]")


def _gdelt_recent_articles():
    st.markdown("#### GDELT 최근 IMEC 관련 기사 (키 불필요)")
    with st.spinner("GDELT 기사 로딩 중..."):
        df = gdelt.get_articles("imec_corridor")
    if df is None or df.empty:
        st.info("GDELT 기사를 불러올 수 없습니다.")
        return
    for _, row in df.head(10).iterrows():
        date  = str(row.get("date", ""))[:8]
        title = row.get("title", "")
        url   = row.get("url", "#")
        dom   = row.get("domain", "")
        st.markdown(f"📄 [{title}]({url})  \n`{dom}` · `{date}`")


def render():
    st.subheader("뉴스 & 감성 분석")

    tab1, tab2 = st.tabs(["NewsAPI / GDELT 키워드별", "GDELT IMEC 최근 기사"])

    with tab1:
        for query_key in NEWS_QUERIES:
            _news_section(query_key)

    with tab2:
        _gdelt_recent_articles()

    st.divider()
    st.caption(
        "감성 분석: VADER (영문 기사) | "
        "출처: NewsAPI (유료 키 필요, 무료 100req/일) → 없을 경우 GDELT 자동 대체"
    )
