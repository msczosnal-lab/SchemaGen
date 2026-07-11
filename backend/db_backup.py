"""Kopia zapasowa data/schemagen.db — harmonogram Windows + start labelera."""

from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from backend.paths import BACKUPS_DIR, DB_PATH

KEEP_BACKUPS = 14


def backup_schemagen_db() -> Path | None:
    """Checkpoint WAL, kopia do data/backups/schemagen-YYYYMMDD.db, przycina do KEEP_BACKUPS."""
    if not DB_PATH.exists():
        return None
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    dest = BACKUPS_DIR / f"schemagen-{stamp}.db"
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        try:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        finally:
            conn.close()
    except sqlite3.DatabaseError:
        pass
    shutil.copy2(DB_PATH, dest)
    _prune_old_backups()
    return dest


def _prune_old_backups() -> None:
    backups = sorted(
        BACKUPS_DIR.glob("schemagen-*.db"),
        key=lambda p: p.name,
        reverse=True,
    )
    for old in backups[KEEP_BACKUPS:]:
        old.unlink(missing_ok=True)
