"""Archiwizuje stare bboxy WRT01 i resetuje dataset (SQLite + data/labeled).

Użycie:
    python scripts/archive_wrt01_reset.py          # dry-run
    python scripts/archive_wrt01_reset.py --apply
"""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DB_PATH = DATA / "schemagen.db"
LABELED = DATA / "labeled"
ARCHIVE_ROOT = DATA / "archive"
PREFIX = "SchematWRT01"
ARCHIVE_NAME = "wrt01-legacy-2026-06-15"


def _wrt01_pages(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT id, filename, status, created_at FROM pages WHERE id LIKE ? ORDER BY id",
        (f"{PREFIX}%",),
    ).fetchall()
    return [dict(r) for r in rows]


def _wrt01_annotations(conn: sqlite3.Connection) -> list[tuple[str, str, str]]:
    return conn.execute(
        """
        SELECT page_id, payload_json, updated_at
        FROM annotations
        WHERE page_id LIKE ?
        ORDER BY page_id
        """,
        (f"{PREFIX}%",),
    ).fetchall()


def _bbox_stats(payload_json: str) -> dict:
    data = json.loads(payload_json)
    bboxes = data.get("bboxes", [])
    tagged = sum(1 for b in bboxes if (b.get("tag") or "").strip())
    return {
        "bboxes": len(bboxes),
        "tagged": tagged,
        "lines": len(data.get("lines", [])),
        "texts": len(data.get("texts", [])),
    }


def _labeled_wrt01_files() -> list[Path]:
    if not LABELED.exists():
        return []
    out: list[Path] = []
    for path in LABELED.rglob("*"):
        if not path.is_file():
            continue
        if PREFIX in path.name:
            out.append(path)
    return sorted(out)


def build_manifest(
    pages: list[dict],
    annotations: list[tuple[str, str, str]],
    labeled_files: list[Path],
) -> dict:
    per_page: list[dict] = []
    total_bboxes = 0
    for page_id, payload_json, updated_at in annotations:
        stats = _bbox_stats(payload_json)
        total_bboxes += stats["bboxes"]
        per_page.append({"page_id": page_id, "updated_at": updated_at, **stats})

    return {
        "archived_at": datetime.now(timezone.utc).isoformat(),
        "reason": "Reset WRT01 — workflow bbox-first + paleta (prompt 010), stare opisy przed paletą",
        "prefix": PREFIX,
        "pages_in_db": len(pages),
        "annotated_pages": len(annotations),
        "total_bboxes": total_bboxes,
        "labeled_export_files": len(labeled_files),
        "per_page": per_page,
        "note": "Stary model symbols_v1.onnx trenowany na tym GT — do ponownego treningu po nowych bboxach.",
    }


def archive_and_reset(apply: bool) -> dict:
    if not DB_PATH.exists():
        raise SystemExit(f"Brak bazy: {DB_PATH}")

    archive_dir = ARCHIVE_ROOT / ARCHIVE_NAME
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    pages = _wrt01_pages(conn)
    annotations = _wrt01_annotations(conn)
    labeled_files = _labeled_wrt01_files()
    manifest = build_manifest(pages, annotations, labeled_files)

    print(f"WRT01: {manifest['annotated_pages']} stron z adnotacjami, {manifest['total_bboxes']} bboxów")
    print(f"Eksport labeled: {len(labeled_files)} plików")
    print(f"Archiwum: {archive_dir}")

    if not apply:
        print("\nDry-run — dodaj --apply aby wykonać.")
        conn.close()
        return manifest

    archive_dir.mkdir(parents=True, exist_ok=True)
    ann_dir = archive_dir / "annotations"
    ann_dir.mkdir(exist_ok=True)

    for page_id, payload_json, updated_at in annotations:
        dest = ann_dir / f"{page_id}.label.json"
        dest.write_text(payload_json, encoding="utf-8")

    if labeled_files:
        labeled_archive = archive_dir / "labeled"
        labeled_archive.mkdir(exist_ok=True)
        for src in labeled_files:
            rel = src.relative_to(LABELED)
            dest = labeled_archive / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)

    (archive_dir / "pages.json").write_text(
        json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (archive_dir / "MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    conn.execute("DELETE FROM annotations WHERE page_id LIKE ?", (f"{PREFIX}%",))
    conn.execute(
        "UPDATE pages SET status = 'new' WHERE id LIKE ?",
        (f"{PREFIX}%",),
    )
    conn.commit()
    conn.close()

    for path in labeled_files:
        path.unlink()

    for cache in LABELED.rglob("*.cache"):
        cache.unlink(missing_ok=True)

    export_manifest = LABELED / "export-manifest.json"
    if export_manifest.exists():
        export_manifest.write_text(
            json.dumps(
                {
                    "archived": ARCHIVE_NAME,
                    "archived_at": manifest["archived_at"],
                    "note": "Wyczyszczone przy resecie WRT01 — nowy eksport po oznaczeniu stron.",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    data_yaml = LABELED / "data.yaml"
    if data_yaml.exists():
        data_yaml.unlink()

    print("\nGotowe:")
    print(f"  Archiwum: {archive_dir}")
    print(f"  SQLite: usunięto {len(annotations)} adnotacji WRT01, status stron → new")
    print(f"  data/labeled: usunięto {len(labeled_files)} plików WRT01")
    print("  Labeler: wyczyść szkice w przeglądarce (localStorage) lub Ctrl+Shift+R")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Wykonaj archiwizację i reset (domyślnie dry-run)",
    )
    args = parser.parse_args()
    archive_and_reset(apply=args.apply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
