"""IMEC Monitor — 메인 Streamlit 앱.

실행: streamlit run app.py
"""

import streamlit as st
from datetime import datetime
from collectors.db import cache_last_updated
from views import overview, shipping, energy, trade, geopolitics, news_feed, report, lkchem

# ---------------------------------------------------------------------------
# 페이지 설정
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="IMEC Monitor",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# 헤더
# ---------------------------------------------------------------------------
col_title, col_refresh = st.columns([8, 1])
with col_title:
    st.title("🌐 IMEC Monitor")
    st.caption("India – Middle East – Europe Economic Corridor | 세계 정세 모니터링 대시보드")

with col_refresh:
    st.write("")  # 수직 정렬용 여백
    if st.button("🔄 새로고침", width="stretch"):
        st.cache_data.clear()
        st.rerun()

# 마지막 갱신 시각
last_updated = cache_last_updated("fred_brent")
if last_updated:
    st.caption(f"마지막 데이터 갱신: {last_updated.strftime('%Y-%m-%d %H:%M')} UTC")

st.divider()

# ---------------------------------------------------------------------------
# 탭
# ---------------------------------------------------------------------------
tabs = st.tabs([
    "📊 개요",
    "🚢 해운·물류",
    "⚡ 에너지",
    "📈 무역·경제",
    "🌍 지정학",
    "📰 뉴스",
    "📋 일일 보고서",
    "🔬 엘케이켐",
])

with tabs[0]:
    overview.render()

with tabs[1]:
    shipping.render()

with tabs[2]:
    energy.render()

with tabs[3]:
    trade.render()

with tabs[4]:
    geopolitics.render()

with tabs[5]:
    news_feed.render()

with tabs[6]:
    report.render()

with tabs[7]:
    lkchem.render()

# ---------------------------------------------------------------------------
# 푸터
# ---------------------------------------------------------------------------
st.divider()
st.caption(
    "📌 데이터 출처: World Bank · IMF · FRED · EIA · GDELT · NewsAPI · Yahoo Finance · UN Comtrade  \n"
    "⚠️ 일부 지표는 API 키 설정 또는 수동 입력이 필요합니다. `.env.example` 참고  \n"
    "🔄 새로고침 버튼으로 캐시를 초기화하고 최신 데이터를 불러올 수 있습니다."
)
