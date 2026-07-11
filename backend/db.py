"""SQLite — projekty, adnotacje, wersje modeli.

GT (grafy SchematicGraph) = źródło prawdy w plikach ``gt/*.json`` (prompt 030);
tabela ``schematic_graph`` to tylko cache odbudowywalny z gt/.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

from backend import gt_store
from backend.paths import DB_PATH, ensure_data_dirs


def _connect() -> sqlite3.Connection:
    ensure_data_dirs()
    # timeout: czeka na blokade zamiast rzucac "database is locked"
    # (autosave co 500 ms + zapytania GET z watkow threadpool)
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    # WAL + NORMAL: znacznie mniejsze ryzyko korupcji przy wspolbieznym
    # zapisie i lepsza rownoleglosc czytanie/pisanie.
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=30000")
    except sqlite3.DatabaseError:
        pass
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
            CREATE TABLE IF NOT EXISTS tag_usage (
                label_key TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                usage_count INTEGER NOT NULL DEFAULT 0,
                last_used_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS schematic_graph (
                page_id TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
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


def _upsert_graph_cache(page_id: str, payload: dict[str, Any]) -> None:
    """Wpis do cache SQLite (nie dotyka pliku gt/)."""
    now = datetime.now(timezone.utc).isoformat()
    with db_session() as conn:
        conn.execute(
            """
            INSERT INTO schematic_graph (page_id, payload_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(page_id) DO UPDATE SET
                payload_json=excluded.payload_json,
                updated_at=excluded.updated_at
            """,
            (page_id, json.dumps(payload, ensure_ascii=False), now),
        )


def save_schematic_graph(
    page_id: str, payload: dict[str, Any], allow_empty: bool = False
) -> dict[str, Any]:
    """Zapis GT: plik ``gt/<page_id>.json`` (źródło prawdy) + cache SQLite.

    Guard empty-overwrite egzekwowany na podstawie PLIKU JSON: pusty graf
    (0 symboli i 0 linii) nie nadpisuje istniejącego niepustego pliku, chyba
    że ``allow_empty=True``. Zwraca status: ``saved`` lub ``skipped_empty_overwrite``.
    """
    init_db()
    if gt_store._is_empty_payload(payload) and not allow_empty:
        existing = gt_store.read_gt_json(page_id)
        if not gt_store._is_empty_payload(existing):
            return {"status": "skipped_empty_overwrite", "page_id": page_id}
    # źródło prawdy: plik JSON (atomowo), potem cache
    gt_store.write_gt_json(page_id, payload)
    _upsert_graph_cache(page_id, payload)
    return {"status": "saved", "page_id": page_id}


def load_schematic_graph(page_id: str) -> dict[str, Any] | None:
    """Czytaj z cache; przy braku — z ``gt/<page_id>.json`` (i odbuduj cache)."""
    init_db()
    with db_session() as conn:
        row = conn.execute(
            "SELECT payload_json FROM schematic_graph WHERE page_id = ?",
            (page_id,),
        ).fetchone()
    if row:
        return json.loads(row["payload_json"])
    # cache miss / świeża baza — sięgnij do źródła prawdy
    payload = gt_store.read_gt_json(page_id)
    if payload is not None:
        _upsert_graph_cache(page_id, payload)
    return payload


def has_schematic_graph(page_id: str) -> bool:
    init_db()
    with db_session() as conn:
        row = conn.execute(
            "SELECT 1 FROM schematic_graph WHERE page_id = ?",
            (page_id,),
        ).fetchone()
    if row is not None:
        return True
    return gt_store.gt_path(page_id).exists()


def rebuild_cache_from_gt() -> int:
    """Skan ``gt/*.json`` → cache SQLite. Zwraca liczbę odbudowanych stron.

    Wołane na starcie aplikacji, by świeża/uszkodzona baza sama się odbudowała
    ze źródła prawdy (plików GT wersjonowanych gitem).
    """
    init_db()
    count = 0
    for page_id, payload in gt_store.iter_gt_payloads():
        _upsert_graph_cache(page_id, payload)
        count += 1
    return count


def list_pages() -> list[dict[str, str]]:
    init_db()
    with db_session() as conn:
        rows = conn.execute(
            """
            SELECT p.id, p.filename, p.status,
                   g.updated_at AS graph_updated_at,
                   a.updated_at AS annotation_updated_at
            FROM pages p
            LEFT JOIN schematic_graph g ON g.page_id = p.id
            LEFT JOIN annotations a ON a.page_id = p.id
            ORDER BY p.id
            """
        ).fetchall()
    return [dict(row) for row in rows]


def bump_tag_usage(labels: list[str]) -> int:
    """Zwieksza licznik uzycia hasel (case-insensitive klucz). Zwraca ile zaktualizowano."""
    init_db()
    now = datetime.now(timezone.utc).isoformat()
    updated = 0
    with db_session() as conn:
        for raw in labels:
            label = raw.strip()
            if not label:
                continue
            key = label.casefold()
            conn.execute(
                """
                INSERT INTO tag_usage (label_key, label, usage_count, last_used_at)
                VALUES (?, ?, 1, ?)
                ON CONFLICT(label_key) DO UPDATE SET
                    usage_count = usage_count + 1,
                    last_used_at = excluded.last_used_at,
                    label = excluded.label
                """,
                (key, label, now),
            )
            updated += 1
    return updated


def get_tag_usage_map() -> dict[str, tuple[str, int]]:
    """Mapa casefold(label) -> (kanoniczne_haslo, usage_count)."""
    init_db()
    with db_session() as conn:
        rows = conn.execute(
            "SELECT label_key, label, usage_count FROM tag_usage ORDER BY usage_count DESC"
        ).fetchall()
    return {row["label_key"]: (row["label"], row["usage_count"]) for row in rows}
