"""SQLite 기반 데이터 캐시 — API 요청 횟수를 최소화하고 앱 재시작 시에도 데이터를 유지합니다."""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

DB_PATH = Path(__file__).parent.parent / "data" / "cache.db"


def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            key        TEXT PRIMARY KEY,
            data       TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS manual_data (
            key        TEXT PRIMARY KEY,
            data       TEXT NOT NULL,
            label      TEXT,
            updated_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            report_date TEXT NOT NULL,
            title       TEXT NOT NULL,
            summary     TEXT NOT NULL,
            risk_level  TEXT NOT NULL,
            content     TEXT NOT NULL,
            created_at  TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# 보고서 저장 / 조회
# ---------------------------------------------------------------------------

def save_report(report_date: str, title: str, summary: str,
                risk_level: str, content: str) -> int:
    """일일 보고서 저장. 같은 날짜 보고서가 있으면 덮어씀. report id 반환."""
    with _get_conn() as conn:
        conn.execute(
            "DELETE FROM reports WHERE report_date=?", (report_date,)
        )
        cur = conn.execute(
            "INSERT INTO reports (report_date, title, summary, risk_level, content, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (report_date, title, summary, risk_level, content, datetime.utcnow().isoformat()),
        )
        return cur.lastrowid


def get_report_list(limit: int = 60) -> list:
    """보고서 목록 반환 (최신순). content 제외."""
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT id, report_date, title, summary, risk_level, created_at "
            "FROM reports ORDER BY report_date DESC LIMIT ?", (limit,)
        ).fetchall()
    return [
        {"id": r[0], "date": r[1], "title": r[2],
         "summary": r[3], "risk_level": r[4], "created_at": r[5]}
        for r in rows
    ]


def get_report_content(report_id: int) -> Optional[str]:
    """보고서 본문 반환."""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT content FROM reports WHERE id=?", (report_id,)
        ).fetchone()
    return row[0] if row else None


def report_exists_today() -> bool:
    """오늘 날짜 보고서가 이미 있는지 확인."""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM reports WHERE report_date=?", (today,)
        ).fetchone()
    return row is not None


def cache_get(key: str, max_age_hours: float = 24) -> Optional[pd.DataFrame]:
    """캐시에서 데이터 읽기. 만료됐거나 없으면 None 반환."""
    try:
        with _get_conn() as conn:
            row = conn.execute(
                "SELECT data, updated_at FROM cache WHERE key=?", (key,)
            ).fetchone()
        if not row:
            return None
        updated_at = datetime.fromisoformat(row[1])
        if datetime.utcnow() - updated_at > timedelta(hours=max_age_hours):
            return None
        import io
        return pd.read_json(io.StringIO(row[0]), orient="records")
    except Exception:
        return None


def cache_set(key: str, df: pd.DataFrame) -> None:
    """데이터를 캐시에 저장."""
    try:
        with _get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache (key, data, updated_at) VALUES (?, ?, ?)",
                (key, df.to_json(orient="records", date_format="iso"), datetime.utcnow().isoformat()),
            )
    except Exception:
        pass


def cache_last_updated(key: str) -> Optional[datetime]:
    """마지막 캐시 갱신 시각 반환."""
    try:
        with _get_conn() as conn:
            row = conn.execute(
                "SELECT updated_at FROM cache WHERE key=?", (key,)
            ).fetchone()
        return datetime.fromisoformat(row[0]) if row else None
    except Exception:
        return None


def manual_set(key: str, df: pd.DataFrame, label: str = "") -> None:
    """수동 입력 데이터 저장 (DP World, IEA 등)."""
    try:
        with _get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO manual_data (key, data, label, updated_at) VALUES (?, ?, ?, ?)",
                (key, df.to_json(orient="records", date_format="iso"), label, datetime.utcnow().isoformat()),
            )
    except Exception:
        pass


def manual_get(key: str) -> Optional[pd.DataFrame]:
    """수동 입력 데이터 읽기."""
    try:
        with _get_conn() as conn:
            row = conn.execute(
                "SELECT data FROM manual_data WHERE key=?", (key,)
            ).fetchone()
        import io
        return pd.read_json(io.StringIO(row[0]), orient="records") if row else None
    except Exception:
        return None
