"""SQLite — projekty, adnotacje, wersje modeli."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

from backend.paths import DB_PATH, ensure_data_dirs


def _connect() -> sqlite3.Connection:
    ensure_data_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS pages (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                status TEXT DEFAULT 'new',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS annotations (
                page_id TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS model_versions (
                version TEXT PRIMARY KEY,
                onnx_path TEXT NOT NULL,
                metrics_json TEXT,
                trained_at TEXT NOT NULL
            );
            """
        )
        conn.commit()


@contextmanager
def db_session() -> Iterator[sqlite3.Connection]:
    conn = _connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def upsert_page(page_id: str, filename: str, status: str = "new") -> None:
    init_db()
    now = datetime.now(timezone.utc).isoformat()
    with db_session() as conn:
        conn.execute(
            """
            INSERT INTO pages (id, filename, status, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET filename=excluded.filename, status=excluded.status
            """,
            (page_id, filename, status, now),
        )


def save_annotation(page_id: str, payload: dict[str, Any]) -> None:
    init_db()
    now = datetime.now(timezone.utc).isoformat()
    with db_session() as conn:
        conn.execute(
            """
            INSERT INTO annotations (page_id, payload_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(page_id) DO UPDATE SET
                payload_json=excluded.payload_json,
                updated_at=excluded.updated_at
            """,
            (page_id, json.dumps(payload, ensure_ascii=False), now),
        )


def load_annotation(page_id: str) -> dict[str, Any] | None:
    init_db()
    with db_session() as conn:
        row = conn.execute(
            "SELECT payload_json FROM annotations WHERE page_id = ?",
            (page_id,),
        ).fetchone()
    if not row:
        return None
    return json.loads(row["payload_json"])


def list_pages() -> list[dict[str, str]]:
    init_db()
    with db_session() as conn:
        rows = conn.execute(
            "SELECT id, filename, status FROM pages ORDER BY created_at"
        ).fetchall()
    return [dict(row) for row in rows]
