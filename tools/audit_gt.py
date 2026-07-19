"""Audyt integralności GT (prompt 025, Faza A1) — READ-ONLY.

Nic nie zapisuje do gt/ ani do bazy. Sprawdza:

* ``page_id`` w pliku == nazwa pliku (stem)
* rozmiar obrazu w GT == faktyczny PNG w ``data/raw/`` (jeśli obraz jest)
* bboxy / terminale / wierzchołki linii poza kadrem strony
* duplikaty ID symboli, terminali i linii w obrębie strony
* ID symboli współdzielone MIĘDZY stronami (trop na przemieszane rekordy)
* cache SQLite ``schematic_graph`` vs ``gt/*.json`` (rozjazd = "zła strona")
* strony z ``config/val-pages.yaml`` bez pliku GT (trop p040)
* kolizje ``sanitize_page_id`` (dwa page_id -> jeden plik)
* czy ``gt/_backup_*`` wpada w glob ``gt/*.json``

Użycie::

    python -m tools.audit_gt              # raport tekstowy
    python -m tools.audit_gt --json       # maszynowo
    python -m tools.audit_gt --md out.md  # raport markdown
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend import gt_store  # noqa: E402
from backend.paths import DB_PATH, GT, RAW, VAL_PAGES  # noqa: E402

Finding = dict[str, Any]


def _add(out: list[Finding], sev: str, code: str, page: str, msg: str, **extra) -> None:
    out.append({"severity": sev, "code": code, "page_id": page, "message": msg, **extra})


def _png_size(page_id: str) -> tuple[int, int] | None:
    """Rozmiar PNG bez OpenCV (czysty nagłówek IHDR). None = brak pliku."""
    for ext in (".png",):
        p = RAW / f"{page_id}{ext}"
        if not p.exists():
            continue
        with p.open("rb") as fh:
            head = fh.read(33)
        if len(head) < 33 or head[12:16] != b"IHDR":
            return None
        w = int.from_bytes(head[16:20], "big")
        h = int.from_bytes(head[20:24], "big")
        return w, h
    for ext in (".jpg", ".jpeg"):
        if (RAW / f"{page_id}{ext}").exists():
            return None  # JPEG: pomijamy (rzadkie w projekcie)
    return None


def _load_cache() -> dict[str, dict[str, Any]] | None:
    if not DB_PATH.exists():
        return None
    try:
        # immutable=1: czytamy nawet gdy leży hot journal (nie próbujemy rollbacku,
        # bo audyt jest read-only i nie wolno mu ruszyć bazy).
        conn = sqlite3.connect(f"file:{DB_PATH}?immutable=1", uri=True, timeout=5.0)
        conn.row_factory = sqlite3.Row
        names = {
            r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        if "schematic_graph" not in names:
            conn.close()
            return {"__no_table__": {"tables": sorted(names)}}
        rows = conn.execute(
            "SELECT page_id, payload_json FROM schematic_graph"
        ).fetchall()
        conn.close()
    except sqlite3.DatabaseError as exc:
        return {"__error__": {"error": str(exc)}}
    out: dict[str, dict[str, Any]] = {}
    for r in rows:
        try:
            out[r["page_id"]] = json.loads(r["payload_json"])
        except json.JSONDecodeError:
            out[r["page_id"]] = {"__unparsable__": True}
    return out


def _counts(payload: dict[str, Any]) -> tuple[int, int]:
    return len(payload.get("symbols") or []), len(payload.get("lines") or [])


def audit() -> dict[str, Any]:
    findings: list[Finding] = []
    pages: dict[str, dict[str, Any]] = {}
    sym_owner: dict[str, list[str]] = defaultdict(list)
    sanitize_map: dict[str, list[str]] = defaultdict(list)

    if not GT.is_dir():
        _add(findings, "CRIT", "gt_dir_missing", "-", f"Brak katalogu GT: {GT}")
        return {"findings": findings, "pages": {}}

    files = sorted(GT.glob("*.json"))
    backup_dirs = [d.name for d in GT.iterdir() if d.is_dir()]
    nested = sorted(GT.glob("*/*.json"))
    if backup_dirs:
        _add(
            findings,
            "INFO",
            "gt_backup_dirs",
            "-",
            f"Podkatalogi w gt/: {backup_dirs} — glob('*.json') ich NIE łapie "
            f"({len(nested)} plików w podkatalogach pominiętych). OK.",
        )

    for path in files:
        stem = path.stem
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            _add(findings, "CRIT", "gt_unreadable", stem, f"Nie da się wczytać: {exc}")
            continue

        pages[stem] = payload
        sanitize_map[gt_store.sanitize_page_id(stem)].append(stem)

        inner = str(payload.get("page_id") or "")
        if inner != stem:
            _add(
                findings,
                "CRIT",
                "page_id_mismatch",
                stem,
                f"page_id w pliku = {inner!r}, nazwa pliku = {stem!r}",
                file_page_id=inner,
            )

        gw = int(payload.get("image_width") or 0)
        gh = int(payload.get("image_height") or 0)
        if gw <= 0 or gh <= 0:
            _add(findings, "WARN", "bad_image_size", stem, f"image_size = {gw}x{gh}")
        real = _png_size(stem)
        if real is None:
            _add(
                findings,
                "WARN",
                "png_missing",
                stem,
                "Brak PNG w data/raw/ — nie da się zweryfikować skali GT",
            )
        elif real != (gw, gh):
            _add(
                findings,
                "CRIT",
                "image_size_mismatch",
                stem,
                f"GT {gw}x{gh} != PNG {real[0]}x{real[1]} — WSZYSTKIE współrzędne "
                "tej strony są w złej skali",
                gt_size=[gw, gh],
                png_size=list(real),
            )

        W = gw or (real[0] if real else 0)
        H = gh or (real[1] if real else 0)

        symbols = payload.get("symbols") or []
        lines = payload.get("lines") or []

        seen_sym: dict[str, int] = defaultdict(int)
        out_of_frame = 0
        bad_bbox = 0
        for s in symbols:
            sid = str(s.get("id"))
            seen_sym[sid] += 1
            sym_owner[sid].append(stem)
            bbox = s.get("bbox") or []
            if len(bbox) < 4:
                bad_bbox += 1
                continue
            x1, y1, x2, y2 = (float(v) for v in bbox[:4])
            if x2 <= x1 or y2 <= y1:
                bad_bbox += 1
            if W and H and (x1 < 0 or y1 < 0 or x2 > W or y2 > H):
                out_of_frame += 1
            tids: dict[str, int] = defaultdict(int)
            for t in s.get("terminals") or []:
                tids[str(t.get("id"))] += 1
                tx, ty = float(t.get("x", 0)), float(t.get("y", 0))
                if not (-0.001 <= tx <= 1.001 and -0.001 <= ty <= 1.001):
                    _add(
                        findings,
                        "WARN",
                        "terminal_not_relative",
                        stem,
                        f"symbol {sid}: terminal {t.get('id')} = ({tx}, {ty}) "
                        "poza [0,1] — terminale są względne wobec bbox",
                    )
            dup_t = [k for k, v in tids.items() if v > 1]
            if dup_t:
                _add(
                    findings,
                    "CRIT",
                    "dup_terminal_id",
                    stem,
                    f"symbol {sid}: zduplikowane ID terminali {dup_t}",
                )

        dup_sym = [k for k, v in seen_sym.items() if v > 1]
        if dup_sym:
            _add(
                findings,
                "CRIT",
                "dup_symbol_id",
                stem,
                f"Zduplikowane ID symboli w obrębie strony: {dup_sym}",
            )
        if bad_bbox:
            _add(findings, "CRIT", "bad_bbox", stem, f"{bad_bbox} bboxów zdegenerowanych/niepełnych")
        if out_of_frame:
            _add(
                findings,
                "CRIT" if out_of_frame > len(symbols) * 0.1 else "WARN",
                "bbox_out_of_frame",
                stem,
                f"{out_of_frame}/{len(symbols)} bboxów poza kadrem {W}x{H}",
                count=out_of_frame,
            )

        seen_line: dict[str, int] = defaultdict(int)
        dangling = 0
        vert_out = 0
        sym_ids = {str(s.get("id")) for s in symbols}
        for ln in lines:
            seen_line[str(ln.get("id"))] += 1
            for ref_key in ("from", "to"):
                ref = ln.get(ref_key) or {}
                if isinstance(ref, dict):
                    ref_sym = str(ref.get("symbol_id") or ref.get("symbol") or "")
                else:
                    ref_sym = str(ref).split(":")[0]
                if ref_sym and ref_sym not in sym_ids:
                    dangling += 1
            for v in ln.get("vertices") or []:
                if len(v) < 2:
                    continue
                if W and H and not (0 <= float(v[0]) <= W and 0 <= float(v[1]) <= H):
                    vert_out += 1
        dup_line = [k for k, v in seen_line.items() if v > 1]
        if dup_line:
            _add(findings, "CRIT", "dup_line_id", stem, f"Zduplikowane ID linii: {dup_line}")
        if dangling:
            _add(
                findings,
                "CRIT",
                "dangling_line_ref",
                stem,
                f"{dangling} końców linii wskazuje na nieistniejący symbol",
                count=dangling,
            )
        if vert_out:
            _add(
                findings,
                "WARN",
                "vertex_out_of_frame",
                stem,
                f"{vert_out} wierzchołków linii poza kadrem {W}x{H}",
                count=vert_out,
            )
        if not symbols and not lines:
            _add(findings, "WARN", "gt_empty", stem, "GT pusty (0 symboli, 0 linii)")

    # ID symboli współdzielone między stronami (sym_0 jest wspólne z natury —
    # zgłaszamy tylko ID wyglądające na unikalne, nie sekwencyjne sym_N)
    for sid, owners in sym_owner.items():
        if len(set(owners)) > 1 and not sid.startswith("sym_"):
            _add(
                findings,
                "WARN",
                "symbol_id_cross_page",
                ",".join(sorted(set(owners))),
                f"ID symbolu {sid!r} występuje na {len(set(owners))} stronach",
            )

    for safe, originals in sanitize_map.items():
        if len(originals) > 1:
            _add(
                findings,
                "CRIT",
                "sanitize_collision",
                ",".join(originals),
                f"{len(originals)} page_id mapuje się na jeden plik {safe}.json",
            )

    # stan bazy: hot journal / tryb dziennika
    if DB_PATH.exists():
        hot = DB_PATH.with_name(DB_PATH.name + "-journal")
        wal = DB_PATH.with_name(DB_PATH.name + "-wal")
        if hot.exists():
            _add(
                findings,
                "CRIT",
                "db_hot_journal",
                "-",
                f"Leży {hot.name} ({hot.stat().st_size} B) — baza po nieczystym "
                "zamknięciu (rollback przy następnym otwarciu). Tryb DELETE, nie WAL.",
            )
        if not wal.exists() and not hot.exists():
            _add(
                findings,
                "INFO",
                "db_no_wal",
                "-",
                "Brak pliku -wal — baza prawdopodobnie w trybie DELETE "
                "(PRAGMA journal_mode=WAL w backend/db.py jest połykana przez except)",
            )

    # cache SQLite vs pliki
    cache = _load_cache()
    if cache is None:
        _add(findings, "INFO", "db_missing", "-", f"Brak bazy {DB_PATH} (cache odbuduje się ze startu)")
    elif "__error__" in cache:
        _add(
            findings,
            "CRIT",
            "db_unreadable",
            "-",
            f"Baza nieczytelna: {cache['__error__']['error']} — cache do odbudowy",
        )
    elif "__no_table__" in cache:
        _add(
            findings,
            "WARN",
            "cache_table_missing",
            "-",
            "Baza nie ma tabeli schematic_graph (tabele: "
            f"{cache['__no_table__']['tables']}) — init_db + rebuild odtworzy ze źródła",
        )
    else:
        for pid, cpayload in cache.items():
            if pid not in pages:
                _add(
                    findings,
                    "CRIT",
                    "cache_orphan",
                    pid,
                    f"Cache SQLite ma stronę {pid!r} bez pliku gt/{pid}.json "
                    "(rebuild_cache_from_gt jej NIE usunie — zostaje na zawsze)",
                    cache_counts=list(_counts(cpayload)),
                )
                continue
            fs, fl = _counts(pages[pid])
            cs, cl = _counts(cpayload)
            if (fs, fl) != (cs, cl):
                _add(
                    findings,
                    "CRIT",
                    "cache_divergence",
                    pid,
                    f"cache {cs} sym./{cl} linii != plik {fs} sym./{fl} linii",
                    cache_counts=[cs, cl],
                    file_counts=[fs, fl],
                )
        for pid in pages:
            if pid not in cache:
                _add(findings, "INFO", "cache_missing_page", pid, "Strona bez wpisu w cache")

    # val-pages bez GT
    if VAL_PAGES.exists():
        try:
            import yaml

            val = yaml.safe_load(VAL_PAGES.read_text(encoding="utf-8")) or {}
            for pid in val.get("val_pages") or []:
                if pid not in pages:
                    _add(
                        findings,
                        "WARN",
                        "val_page_without_gt",
                        pid,
                        "Strona z val-pages.yaml nie ma pliku gt/*.json",
                    )
        except Exception as exc:  # noqa: BLE001
            _add(findings, "INFO", "val_pages_unreadable", "-", str(exc))

    sev_order = {"CRIT": 0, "WARN": 1, "INFO": 2}
    findings.sort(key=lambda f: (sev_order.get(f["severity"], 9), f["code"], f["page_id"]))
    summary = {
        "gt_files": len(files),
        "crit": sum(1 for f in findings if f["severity"] == "CRIT"),
        "warn": sum(1 for f in findings if f["severity"] == "WARN"),
        "info": sum(1 for f in findings if f["severity"] == "INFO"),
    }
    return {
        "summary": summary,
        "findings": findings,
        "pages": {p: {"symbols": _counts(v)[0], "lines": _counts(v)[1]} for p, v in pages.items()},
    }


def _render_md(report: dict[str, Any]) -> str:
    s = report["summary"]
    out = [
        "# 025 — audyt integralności GT (A1)",
        "",
        f"Plików `gt/*.json`: **{s['gt_files']}** · CRIT: **{s['crit']}** · "
        f"WARN: {s['warn']} · INFO: {s['info']}",
        "",
        "## Strony",
        "",
        "| page_id | symbole | linie |",
        "|---|---:|---:|",
    ]
    for pid, c in sorted(report["pages"].items()):
        out.append(f"| {pid} | {c['symbols']} | {c['lines']} |")
    out += ["", "## Znaleziska", "", "| Sev | Kod | Strona | Opis |", "|---|---|---|---|"]
    for f in report["findings"]:
        out.append(
            f"| {f['severity']} | `{f['code']}` | {f['page_id']} | {f['message']} |"
        )
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Audyt integralności GT (read-only)")
    ap.add_argument("--json", action="store_true", help="wynik jako JSON")
    ap.add_argument("--md", metavar="PLIK", help="zapisz raport markdown")
    args = ap.parse_args()

    report = audit()
    if args.md:
        Path(args.md).write_text(_render_md(report), encoding="utf-8")
        print(f"Raport: {args.md}")
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif not args.md:
        s = report["summary"]
        print(f"gt/*.json: {s['gt_files']} | CRIT {s['crit']} | WARN {s['warn']} | INFO {s['info']}")
        for f in report["findings"]:
            print(f"[{f['severity']:4}] {f['code']:24} {f['page_id']:48} {f['message']}")
    return 1 if report["summary"]["crit"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
