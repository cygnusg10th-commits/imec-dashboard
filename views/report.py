"""일일 분석 보고서 탭 — 전체 지표 종합 분석 & 게시판."""

import streamlit as st
from datetime import datetime, timezone
from collectors import fred, finance, gdelt, news
from collectors.db import (
    save_report, get_report_list, get_report_content, report_exists_today
)

# ---------------------------------------------------------------------------
# 분석 텍스트 생성 헬퍼
# ---------------------------------------------------------------------------

def _fmt(v, decimals=2, prefix="", suffix=""):
    if v is None:
        return "데이터 없음"
    return f"{prefix}{v:,.{decimals}f}{suffix}"


def _trend(delta, up_good=True):
    """변화율 → 방향·색 텍스트."""
    if delta is None:
        return ""
    if abs(delta) < 1:
        return f"(보합 {delta:+.1f}%)"
    if (delta > 0) == up_good:
        return f"(▲ {delta:+.1f}% ↑)"
    return f"(▼ {delta:+.1f}% ↓)"


def _analyze_energy(brent, brent_d, wti, natgas):
    lines = []
    if brent:
        if brent > 95:
            lines.append("유가 고공행진 지속 — 중동 에너지 수출 수익 증가, IMEC 파이프라인 수요 부각.")
        elif brent > 80:
            lines.append("유가 안정권 유지 — 에너지 시장 균형 상태.")
        else:
            lines.append("유가 약세 — 산유국 재정 압박 우려, 사우디·UAE IMEC 투자 여력 주시 필요.")
        if brent_d and abs(brent_d) > 5:
            lines.append(f"유가 30일 변동 {brent_d:+.1f}% — 급변동으로 시장 불안 요인.")
    if natgas and natgas > 4:
        lines.append("천연가스 가격 상승 — 유럽 에너지 안보 우려 심화, IMEC 가스관 가치 상승.")
    elif natgas:
        lines.append("천연가스 가격 안정 — 유럽 에너지 수급 우려 완화.")
    return " ".join(lines) if lines else "에너지 데이터 수집 중."


def _analyze_shipping(bdry, bdry_d):
    if bdry is None:
        return "해운 데이터 수집 중."
    if bdry_d and bdry_d > 15:
        return f"BDRY {bdry_d:+.1f}% 급등 — 글로벌 벌크 화물 수요 급증, IMEC 물동량 증가 가능성 주시."
    elif bdry_d and bdry_d > 5:
        return f"BDRY {bdry_d:+.1f}% 상승 — 해운 시장 회복 흐름, 인도·중동 교역 활성화 신호."
    elif bdry_d and bdry_d < -10:
        return f"BDRY {bdry_d:+.1f}% 하락 — 글로벌 무역 위축 우려, IMEC 물동량 전망 신중."
    return f"BDRY ${bdry:,.0f} 수준 유지 — 해운 시장 안정적."


def _analyze_geopolitics(israel, imec, suez, bri):
    lines = []
    if israel is not None:
        if israel > 70:
            lines.append(f"이스라엘 분쟁 리스크 {israel:.0f}/100 — 고위험 구간. IMEC 하이파 구간 진행 심각한 난항 예상.")
        elif israel > 45:
            lines.append(f"이스라엘 분쟁 리스크 {israel:.0f}/100 — 중간 수준. 지속 모니터링 필요.")
        else:
            lines.append(f"이스라엘 분쟁 리스크 {israel:.0f}/100 — 비교적 안정.")
    if imec is not None:
        if imec > 60:
            lines.append(f"IMEC 뉴스 활성도 {imec:.0f}/100 — 주요 이벤트 또는 진전 발생 가능성.")
        elif imec > 35:
            lines.append(f"IMEC 관련 뉴스 {imec:.0f}/100 — 꾸준한 관심 유지.")
        else:
            lines.append(f"IMEC 뉴스 활성도 {imec:.0f}/100 — 주요 이슈 미발생.")
    if suez is not None and suez > 55:
        lines.append(f"수에즈/홍해 리스크 {suez:.0f}/100 — 해운 우회로 압박 심화, IMEC 대안 경로 가치 부각.")
    if bri is not None and bri > 55:
        lines.append(f"BRI 관련 뉴스 {bri:.0f}/100 — 일대일로 동향 활발, IMEC와의 경쟁 구도 주목.")
    return " ".join(lines) if lines else "지정학 데이터 수집 중."


def _analyze_market(nifty_d, ils, inr):
    lines = []
    if nifty_d is not None:
        if nifty_d > 5:
            lines.append(f"인도 Nifty50 {nifty_d:+.1f}% — 인도 경제 강세, IMEC 투자 환경 우호적.")
        elif nifty_d < -5:
            lines.append(f"인도 Nifty50 {nifty_d:+.1f}% — 인도 시장 약세, IMEC 추진 동력 주시.")
        else:
            lines.append(f"인도 Nifty50 {nifty_d:+.1f}% — 안정적.")
    if ils is not None:
        if ils > 3.8:
            lines.append(f"ILS/USD {ils:.4f} — 세켈 약세, 이스라엘 경제 불안 반영.")
        else:
            lines.append(f"ILS/USD {ils:.4f} — 이스라엘 통화 안정.")
    if inr is not None:
        lines.append(f"INR/USD {inr:.2f} — 인도 루피 현황.")
    return " ".join(lines) if lines else "시장 데이터 수집 중."


def _calc_risk_level(israel, imec, suez, brent_d, bdry_d):
    """종합 리스크 레벨 계산."""
    score = 0
    weights = [
        (israel, 35),
        (suez, 25),
        (abs(brent_d) if brent_d else 0, 0.5),
        (imec, 10),
    ]
    total_w = 0
    for val, w in weights[:2]:
        if val is not None:
            score += val * w / 100
            total_w += w
    # brent 변동성
    if brent_d and abs(brent_d) > 5:
        score += 5
    if bdry_d and abs(bdry_d) > 15:
        score += 5

    if score > 55:
        return "🔴 위험"
    elif score > 35:
        return "🟠 높음"
    elif score > 18:
        return "🟡 보통"
    return "🟢 낮음"


def _get_top_news(n=5):
    """주요 뉴스 5건 수집."""
    items = []
    for key in ["IMEC", "중동 정세", "해운"]:
        df = news.get_news(key)
        if df is not None and not df.empty:
            for _, row in df.head(2).iterrows():
                items.append({
                    "title":  row.get("title", ""),
                    "source": row.get("source", row.get("domain", "")),
                    "date":   str(row.get("date", ""))[:10],
                    "url":    row.get("url", "#"),
                    "sentiment": row.get("sentiment", "중립"),
                })
        if len(items) >= n:
            break
    return items[:n]


# ---------------------------------------------------------------------------
# 보고서 생성
# ---------------------------------------------------------------------------

def generate_report() -> dict:
    """현재 데이터를 종합해 보고서 딕셔너리 반환."""
    now_kst = datetime.now(timezone.utc)
    report_date = now_kst.strftime("%Y-%m-%d")

    # — 데이터 수집 —
    brent   = fred.get_latest_value("brent")
    brent_d = None
    brent_df = fred.get_brent()
    if brent_df is not None and len(brent_df) > 30:
        brent_d = (brent_df["value"].iloc[-1] - brent_df["value"].iloc[-31]) / brent_df["value"].iloc[-31] * 100

    wti     = fred.get_latest_value("wti")
    natgas  = fred.get_latest_value("natgas")

    bdry    = finance.get_latest("bdry")
    bdry_d  = finance.get_pct_change("bdry", 30)
    nifty_d = finance.get_pct_change("nifty50", 30)
    ta125_d = finance.get_pct_change("ta125", 30)
    ils     = finance.get_latest("ils_usd")
    inr     = finance.get_latest("inr_usd")

    israel  = gdelt.get_risk_score("israel_conflict")
    imec_s  = gdelt.get_risk_score("imec_corridor")
    suez    = gdelt.get_risk_score("suez_red_sea")
    bri     = gdelt.get_risk_score("bri_china")
    saudi_n = gdelt.get_risk_score("saudi_normalize")

    top_news = _get_top_news(5)

    # — 분석 텍스트 —
    energy_text  = _analyze_energy(brent, brent_d, wti, natgas)
    ship_text    = _analyze_shipping(bdry, bdry_d)
    geo_text     = _analyze_geopolitics(israel, imec_s, suez, bri)
    market_text  = _analyze_market(nifty_d, ils, inr)
    risk_level   = _calc_risk_level(israel, imec_s, suez, brent_d, bdry_d)

    # — 종합 시사점 —
    implications = []
    if israel and israel > 60:
        implications.append("이스라엘 분쟁 고조로 IMEC 핵심 구간(UAE→이스라엘→그리스) 진행이 지연될 수 있으며, 대안 경로 논의 가능성 주시.")
    if suez and suez > 55:
        implications.append("홍해·수에즈 리스크 상승은 IMEC 대안 경로로서의 가치를 높이는 역설적 효과 — 인도→UAE→사우디 육상 구간 주목.")
    if brent and brent > 90:
        implications.append("고유가 국면은 사우디·UAE의 IMEC 인프라 투자 재원 확보에 유리한 환경을 제공.")
    if imec_s and imec_s > 55:
        implications.append("IMEC 관련 뉴스 급증 — 외교 협상 또는 인프라 착공 관련 발표 가능성.")
    if bri and bri > 55:
        implications.append("BRI 관련 뉴스 활발 — 미·중 지경학 경쟁 심화, IMEC의 전략적 중요성 재부각.")
    if not implications:
        implications.append("현재 특이 동향 없음. IMEC 추진 일정 및 참여국 외교 동향 지속 모니터링 권고.")

    # 요약 한 줄
    summary = f"{risk_level} | Brent ${_fmt(brent, 2)} | BDRY ${_fmt(bdry, 0)} | 이스라엘 리스크 {_fmt(israel, 0, suffix='/100')}"

    # — 마크다운 본문 생성 —
    news_md = ""
    for i, item in enumerate(top_news, 1):
        badge = {"긍정": "🟢", "부정": "🔴", "중립": "⚪"}.get(item["sentiment"], "⚪")
        news_md += f"{i}. {badge} [{item['title']}]({item['url']})  \n   `{item['source']}` · `{item['date']}`\n\n"
    if not news_md:
        news_md = "*뉴스 데이터를 불러올 수 없습니다.*\n"

    content = f"""## ⚡ 에너지 시장

| 지표 | 값 | 30일 변화 |
|---|---|---|
| Brent 원유 | {_fmt(brent, 2, "$", "/bbl")} | {_trend(brent_d)} |
| WTI 원유 | {_fmt(wti, 2, "$", "/bbl")} | — |
| 천연가스 | {_fmt(natgas, 2, "$", "/MMBtu")} | — |

**분석:** {energy_text}

---

## 🚢 해운·물류

| 지표 | 값 | 30일 변화 |
|---|---|---|
| BDRY (BDI 프록시) | {_fmt(bdry, 2, "$")} | {_trend(bdry_d)} |

**분석:** {ship_text}

---

## 🌍 지정학적 리스크

| 주제 | 리스크 스코어 |
|---|---|
| 이스라엘 분쟁 | {_fmt(israel, 0, suffix="/100")} |
| 수에즈/홍해 해운 | {_fmt(suez, 0, suffix="/100")} |
| IMEC 뉴스 활성도 | {_fmt(imec_s, 0, suffix="/100")} |
| BRI/중국 | {_fmt(bri, 0, suffix="/100")} |
| 사우디 정상화 | {_fmt(saudi_n, 0, suffix="/100")} |

**분석:** {geo_text}

---

## 📈 참여국 시장

| 지표 | 값 | 30일 변화 |
|---|---|---|
| Nifty 50 (인도) | — | {_trend(nifty_d)} |
| TA-125 (이스라엘) | — | {_trend(ta125_d)} |
| ILS/USD | {_fmt(ils, 4)} | — |
| INR/USD | {_fmt(inr, 2)} | — |

**분석:** {market_text}

---

## 📰 주요 뉴스

{news_md}
---

## 🔍 종합 시사점

{"  ".join(f"- {line}" for line in implications)}

---
*생성: {now_kst.strftime("%Y-%m-%d %H:%M")} UTC | 데이터 출처: FRED · EIA · GDELT · NewsAPI · Yahoo Finance*
"""

    title = f"IMEC Monitor 일일 분석 보고서 — {report_date}"
    return {
        "date":       report_date,
        "title":      title,
        "summary":    summary,
        "risk_level": risk_level,
        "content":    content,
    }


# ---------------------------------------------------------------------------
# 렌더링
# ---------------------------------------------------------------------------

_RISK_COLOR = {
    "🟢 낮음": "green",
    "🟡 보통": "orange",
    "🟠 높음": "red",
    "🔴 위험": "red",
}


def render():
    st.subheader("일일 분석 보고서")

    # 보고서 생성 버튼
    col1, col2 = st.columns([4, 1])
    with col1:
        st.caption("전체 지표를 종합 분석한 일일 보고서입니다. 하루 1회 생성·갱신됩니다.")
    with col2:
        force = st.button("📝 오늘 보고서 생성", width="stretch")

    if force or not report_exists_today():
        with st.spinner("데이터 수집 및 보고서 작성 중..."):
            rpt = generate_report()
            save_report(
                report_date=rpt["date"],
                title=rpt["title"],
                summary=rpt["summary"],
                risk_level=rpt["risk_level"],
                content=rpt["content"],
            )
        st.success(f"보고서 생성 완료 — {rpt['date']}")

    st.divider()

    # 게시판 목록
    reports = get_report_list(60)
    if not reports:
        st.info("보고서가 없습니다. 위의 버튼으로 첫 보고서를 생성해주세요.")
        return

    st.markdown(f"**총 {len(reports)}건의 보고서**")

    # 선택된 보고서 세션 상태
    if "selected_report_id" not in st.session_state:
        st.session_state.selected_report_id = reports[0]["id"]

    # 게시판 목록 테이블
    for rpt in reports:
        risk   = rpt["risk_level"]
        date   = rpt["date"]
        summ   = rpt["summary"]
        is_sel = st.session_state.selected_report_id == rpt["id"]

        col_date, col_risk, col_summ, col_btn = st.columns([1.5, 1.2, 5, 1.2])
        with col_date:
            st.markdown(f"**{date}**")
        with col_risk:
            st.markdown(risk)
        with col_summ:
            st.caption(summ)
        with col_btn:
            label = "▼ 보기중" if is_sel else "▶ 열기"
            if st.button(label, key=f"rpt_{rpt['id']}", width="stretch"):
                st.session_state.selected_report_id = rpt["id"]
                st.rerun()

    st.divider()

    # 선택된 보고서 본문
    content = get_report_content(st.session_state.selected_report_id)
    selected = next((r for r in reports if r["id"] == st.session_state.selected_report_id), None)
    if content and selected:
        st.markdown(f"### {selected['title']}")
        st.markdown(f"**종합 리스크:** {selected['risk_level']}")
        st.divider()
        st.markdown(content, unsafe_allow_html=False)

        # 다운로드 버튼
        st.download_button(
            label="📥 보고서 다운로드 (.md)",
            data=f"# {selected['title']}\n\n{content}",
            file_name=f"IMEC_report_{selected['date']}.md",
            mime="text/markdown",
        )
