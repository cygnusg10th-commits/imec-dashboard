"""백그라운드 데이터 갱신 스케줄러.

Streamlit 앱과 별도로 실행하거나, app.py 시작 시 백그라운드 스레드로 구동합니다.

독립 실행: python scheduler.py
"""

import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 갱신 작업 정의
# ---------------------------------------------------------------------------

def refresh_daily():
    """일간 갱신: 유가, 환율, 증시, GDELT."""
    log.info("일간 갱신 시작...")
    try:
        from collectors import fred, finance, gdelt
        fred.get_brent()
        fred.get_wti()
        fred.get_natgas()
        fred.get_usd_inr()
        fred.get_usd_eur()
        for name in ["nifty50", "ta125", "aramco", "bdry", "brent_f", "natgas_f", "ils_usd", "inr_usd", "eur_usd"]:
            finance.get_series(name)
        for key in gdelt.GDELT_QUERIES:
            gdelt.get_timeline(key)
        log.info("일간 갱신 완료")
    except Exception as e:
        log.error(f"일간 갱신 오류: {e}")


def refresh_weekly():
    """주간 갱신: 뉴스."""
    log.info("주간 갱신 시작...")
    try:
        from collectors import news
        for key in news.NEWS_QUERIES:
            news.get_news(key)
        log.info("주간 갱신 완료")
    except Exception as e:
        log.error(f"주간 갱신 오류: {e}")


def refresh_monthly():
    """월간 갱신: World Bank, EIA, Comtrade."""
    log.info("월간 갱신 시작...")
    try:
        from collectors import worldbank, eia, comtrade
        worldbank.get_gdp_growth()
        worldbank.get_gdp_usd()
        worldbank.get_fdi()
        worldbank.get_lpi()
        worldbank.get_trade_pct()
        eia.get_saudi_production()
        eia.get_india_imports()
        eia.get_uae_production()
        comtrade.get_trade_matrix()
        log.info("월간 갱신 완료")
    except Exception as e:
        log.error(f"월간 갱신 오류: {e}")


# ---------------------------------------------------------------------------
# 스케줄러 설정
# ---------------------------------------------------------------------------

def get_background_scheduler() -> BackgroundScheduler:
    """Streamlit 앱에서 백그라운드로 실행할 스케줄러 반환."""
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(refresh_daily,   "interval", hours=24,  id="daily")
    scheduler.add_job(refresh_weekly,  "interval", hours=168, id="weekly")
    scheduler.add_job(refresh_monthly, "interval", hours=720, id="monthly")
    return scheduler


if __name__ == "__main__":
    log.info("IMEC Monitor 스케줄러 시작")
    # 시작 시 즉시 전체 갱신
    refresh_daily()
    refresh_monthly()

    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(refresh_daily,   "interval", hours=24,  id="daily")
    scheduler.add_job(refresh_weekly,  "interval", hours=168, id="weekly")
    scheduler.add_job(refresh_monthly, "interval", hours=720, id="monthly")

    log.info("스케줄 등록 완료. 실행 중... (Ctrl+C로 종료)")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("스케줄러 종료")
