"""Wykrywanie IDENTYCZNEJ zawartości GT na różnych page_id (prompt 025, F1).

Wyścig `selectPage` w labelerze zapisuje graf strony A pod page_id strony B.
Jeśli to się działo, w danych zostaje ślad: **ta sama lista bboxów pod kilkoma
page_id**. Ten skrypt to wykrywa — read-only, po `gt/*.json`, po cache SQLite
i po katalogach ratunkowych `gt/_rescue_*`.

    python -m tools.gt_dup_scan
    python -m tools.gt_dup_scan --json

Podpis strony = SHA1 z posortowanej listy zaokrąglonych bboxów. Dwie strony
schematu nigdy nie mają przypadkiem identycznych bboxów co do piksela — kolizja
oznacza kopię, nie zbieg okoliczności.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterator

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.paths import DB_PATH, GT  # noqa: E402


def signature(payload: dict[str, Any]) -> tuple[str, int, int]:
    """(hash bboxów, liczba symboli, liczba linii)."""
    boxes = []
    for s in payload.get("symbols") or []:
        bbox = s.get("bbox") or []
        if len(bbox) >= 4:
            boxes.append(tuple(round(float(v), 1) for v in bbox[:4]))
    boxes.sort()
    h = hashlib.sha1(json.dumps(boxes).encode()).hexdigest()[:12]
    return h, len(payload.get("symbols") or []), len(payload.get("lines") or [])


def _iter_sources() -> Iterator[tuple[str, str, dict[str, Any]]]:
    """(źródło, page_id, payload)."""
    if GT.is_dir():
        for p in sorted(GT.glob("*.json")):
            try:
                yield "gt/", p.stem, json.loads(p.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
        for d in sorted(GT.glob("_rescue_*")):
            if not d.is_dir():
                continue
            for p in sorted(d.glob("*.json")):
                try:
                    yield f"{d.name}/", p.stem, json.loads(p.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    continue
    if DB_PATH.exists():
        try:
            conn = sqlite3.connect(f"file:{DB_PATH}?immutable=1", uri=True, timeout=10.0)
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT page_id, payload_json, updated_at FROM schematic_graph"
            ).fetchall()
            conn.close()
        except sqlite3.DatabaseError:
            rows = []
        for r in rows:
            try:
                payload = json.loads(r["payload_json"])
            except json.JSONDecodeError:
                continue
            payload["__updated_at__"] = r["updated_at"]
            yield "cache", r["page_id"], payload


def scan() -> dict[str, Any]:
    by_sig: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen: set[tuple[str, str]] = set()
    for source, page_id, payload in _iter_sources():
        key = (source, page_id)
        if key in seen:
            continue
        seen.add(key)
        h, n_sym, n_lin = signature(payload)
        if n_sym == 0:
            continue
        by_sig[h].append(
            {
                "source": source,
                "page_id": page_id,
                "symbols": n_sym,
                "lines": n_lin,
                "updated_at": payload.get("__updated_at__") or "",
            }
        )

    groups = []
    for h, items in by_sig.items():
        distinct_pages = {i["page_id"] for i in items}
        if len(distinct_pages) < 2:
            continue
        groups.append(
            {
                "signature": h,
                "symbols": items[0]["symbols"],
                "pages": sorted(distinct_pages),
                "entries": sorted(items, key=lambda i: (i["page_id"], i["source"])),
            }
        )
    groups.sort(key=lambda g: (-len(g["pages"]), -g["symbols"]))
    return {
        "groups": groups,
        "duplicate_pages": sum(len(g["pages"]) for g in groups),
        "wasted_pages": sum(len(g["pages"]) - 1 for g in groups),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Duplikaty zawartości GT między stronami")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    report = scan()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    if not report["groups"]:
        print("Brak duplikatów zawartości — każda strona ma własne bboxy. Czysto.")
        return 0

    print(
        f"Grup duplikatów: {len(report['groups'])} | stron dotkniętych: "
        f"{report['duplicate_pages']} | nadmiarowych kopii: {report['wasted_pages']}"
    )
    print()
    print("Identyczne bboxy pod różnymi page_id = ślad wyścigu selectPage (F1).")
    print("Tylko JEDNA strona z grupy zawiera prawdziwe dane; reszta to kopie.")
    print()
    for g in report["groups"]:
        print(f"--- sygnatura {g['signature']} · {g['symbols']} symboli · {len(g['pages'])} stron")
        for e in g["entries"]:
            print(
                f"      [{e['source']:>22}] {e['page_id']:48} "
                f"{e['symbols']:4} sym./{e['lines']:3} linii  {e['updated_at']}"
            )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
