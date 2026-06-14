"""Katalog elementow — slownik opisow z labelera."""

from __future__ import annotations

import re
from datetime import datetime, timezone

import yaml

from backend.paths import CONFIG

CATALOG_PATH = CONFIG / "element-catalog.yaml"


def _slug(label: str) -> str:
    s = label.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"[\s_-]+", "_", s).strip("_")
    return s or "element"


def load_catalog() -> dict:
    if not CATALOG_PATH.exists():
        return {"elements": []}
    data = yaml.safe_load(CATALOG_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {"elements": []}
    data.setdefault("elements", [])
    return data


def list_element_labels() -> list[str]:
    return [str(e.get("label", "")).strip() for e in load_catalog()["elements"] if e.get("label")]


def register_labels(labels: list[str], yolo_class: str = "element") -> int:
    """Dopisuje nowe etykiety do katalogu. Zwraca liczbe dodanych."""
    labels = [t.strip() for t in labels if t and t.strip()]
    if not labels:
        return 0

    data = load_catalog()
    elements: list[dict] = data["elements"]
    known = {str(e.get("label", "")).strip().casefold() for e in elements}
    now = datetime.now(timezone.utc).isoformat()
    added = 0

    for label in labels:
        key = label.casefold()
        if key in known:
            continue
        base = _slug(label)
        elem_id = base
        n = 2
        existing_ids = {e.get("id") for e in elements}
        while elem_id in existing_ids:
            elem_id = f"{base}_{n}"
            n += 1
        elements.append(
            {
                "id": elem_id,
                "label": label,
                "yolo_class": yolo_class,
                "created_at": now,
            }
        )
        known.add(key)
        existing_ids.add(elem_id)
        added += 1

    if added:
        CATALOG_PATH.write_text(
            yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
            encoding="utf-8",
        )
    return added
