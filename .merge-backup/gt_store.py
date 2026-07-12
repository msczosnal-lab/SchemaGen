"""GT jako pliki JSON w repo — źródło prawdy (SQLite = cache).

Każda strona = jeden plik ``gt/<page_id>.json``. Zapis ZAWSZE atomowo
(tmp w tym samym katalogu + ``os.replace``), nigdy w miejscu. JSON czytelny:
``indent=2``, ``ensure_ascii=False``, końcówki LF.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from backend import paths

_SAFE_RE = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_page_id(page_id: str) -> str:
    """page_id -> nazwa pliku bezpieczna dla FS ([A-Za-z0-9._-], reszta -> _)."""
    s = (page_id or "").strip()
    safe = _SAFE_RE.sub("_", s)
    return safe or "_"


def gt_dir() -> Path:
    """Katalog gt/ (odczyt dynamiczny — pozwala monkeypatch w testach)."""
    return paths.GT


def gt_path(page_id: str) -> Path:
    return gt_dir() / f"{sanitize_page_id(page_id)}.json"


def _dumps(payload: dict[str, Any]) -> str:
    # Kolejność kluczy z model_dump jest stabilna (schemat Pydantic) — nie
    # sortujemy, by version/page_id były na górze i diff gita był czytelny.
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def write_gt_json(page_id: str, payload: dict[str, Any]) -> Path:
    """Atomowy zapis gt/<page_id>.json. Zwraca ścieżkę pliku."""
    target = gt_path(page_id)
    target.parent.mkdir(parents=True, exist_ok=True)
    data = _dumps(payload)
    # tmp w TYM SAMYM katalogu (os.replace atomowy tylko w obrębie FS/dir).
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{target.stem}.", suffix=".tmp", dir=str(target.parent)
    )
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, target)  # atomowa podmiana
    except BaseException:
        # sprzątanie połowicznego tmp — plik docelowy pozostaje nienaruszony
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
        raise
    return target


def read_gt_json(page_id: str) -> dict[str, Any] | None:
    """Czyta gt/<page_id>.json. Brak pliku -> None."""
    target = gt_path(page_id)
    if not target.exists():
        return None
    with target.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def list_gt_page_ids() -> list[str]:
    """Lista page_id na podstawie plików gt/*.json (posortowana)."""
    d = gt_dir()
    if not d.exists():
        return []
    return sorted(p.stem for p in d.glob("*.json"))


def _is_empty_payload(payload: dict[str, Any] | None) -> bool:
    if not payload:
        return True
    return not payload.get("symbols") and not payload.get("lines")


def iter_gt_payloads():
    """Generator (page_id_z_pliku, payload) po wszystkich gt/*.json."""
    for pid in list_gt_page_ids():
        payload = read_gt_json(pid)
        if payload is not None:
            yield pid, payload
