"""Rejestracja uzycia hasel w labelerze."""

from __future__ import annotations

from backend.catalog import register_labels
from backend.db import bump_tag_usage


def record_tag_usage(labels: list[str]) -> dict[str, int]:
    """Inkrementuje licznik i dopisuje nowe wyjatki do katalogu."""
    cleaned = [t.strip() for t in labels if t and t.strip()]
    bumped = bump_tag_usage(cleaned)
    added = 0
    try:
        added = register_labels(cleaned)
    except OSError:
        pass
    return {"bumped": bumped, "catalog_added": added}
