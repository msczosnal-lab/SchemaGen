"""Odzyskuje bboxy z adnotacji v1 (tabela annotations, LabelRecord) z surowych
stron uszkodzonych baz i migruje je do grafu v2 (jak label_record_to_graph).

  python tools/recover_from_v1.py            # skan wszystkich data/schemagen*
  python tools/recover_from_v1.py <plik.db>  # jeden plik

Wynik: data/schemagen.v1recovered.db (grafy v2 z bboxami v1). Read-only na zrodlach.
"""
from __future__ import annotations

import datetime
import glob
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import tools.carve_graphs as cg
from backend.class_map import component_type_from_bbox
from backend.models.schematic_graph import GraphSymbol, SchematicGraph, Terminal
from labeler.runtime_draft import image_size_for_page


def _record_to_graph(rec: dict) -> SchematicGraph | None:
    pid = rec.get("page_id")
    bboxes = rec.get("bboxes")
    if not pid or not isinstance(bboxes, list) or not bboxes:
        return None
    w = rec.get("image_width", 0) or 0
    h = rec.get("image_height", 0) or 0
    if w <= 0 or h <= 0:
        try:
            w, h = image_size_for_page(pid)
        except Exception:
            w, h = 5000, 3000
    syms = []
    for b in bboxes:
        try:
            x = float(b["x"]); y = float(b["y"])
            ww = float(b["width"]); hh = float(b["height"])
        except Exception:
            continue
        terms = []
        for t in (b.get("terminals") or []):
            try:
                terms.append(Terminal(id=str(t["id"]), x=float(t["x"]), y=float(t["y"]),
                                       name=t.get("name", "") or ""))
            except Exception:
                continue
        syms.append(GraphSymbol(
            id=str(b.get("id") or ("sym_%d" % len(syms))),
            type=component_type_from_bbox(str(b.get("class_name") or ""), str(b.get("tag") or "")),
            tag=str(b.get("tag") or ""),
            bbox=[x, y, x + ww, y + hh],
            terminals=terms,
        ))
    if not syms:
        return None
    return SchematicGraph(page_id=pid, image_width=int(w) or 5000,
                          image_height=int(h) or 3000, symbols=syms, lines=[])


def main():
    pos = [a for i, a in enumerate(sys.argv[1:], 1)
           if a != "--into" and sys.argv[i - 1] != "--into"]
    if pos:
        files = [pos[0]]
    else:
        files = [f for f in sorted(glob.glob(str(ROOT / "data" / "schemagen*")))
                 if not f.endswith(("-shm", "-wal", ".sql", ".tmp", ".v1recovered.db"))]

    best: dict[str, tuple] = {}  # page_id -> (SchematicGraph, nbbox)
    for f in files:
        try:
            texts = list(cg.iter_json_texts(f))
        except Exception as exc:  # noqa: BLE001
            print("%-46s blad: %s" % (Path(f).name, exc))
            continue
        per = {}
        for obj, _txt in texts:
            if isinstance(obj.get("bboxes"), list) and obj.get("page_id"):
                pid = obj["page_id"]
                nb = len(obj["bboxes"])
                if pid not in per or nb > per[pid][1]:
                    per[pid] = (obj, nb)
        if per:
            summ = ", ".join("%s=%d bbox" % (p.split("_")[-1], v[1]) for p, v in sorted(per.items()))
            print("%-46s %s" % (Path(f).name, summ))
        else:
            print("%-46s (brak adnotacji v1)" % Path(f).name)
        for pid, (obj, nb) in per.items():
            g = _record_to_graph(obj)
            if g and (pid not in best or len(g.symbols) > best[pid][1]):
                best[pid] = (g, len(g.symbols))

    if not best:
        print("\n[WYNIK] Brak adnotacji v1 z bboxami w zadnym pliku.")
        return 1

    print("\n[ODZYSKANE v1 -> v2]")
    for pid, (g, nb) in sorted(best.items()):
        print("  %s : symboli=%d" % (pid, len(g.symbols)))

    # tryb scalania wprost do istniejacej bazy: --into <db>
    if "--into" in sys.argv:
        target = Path(sys.argv[sys.argv.index("--into") + 1])
        tc = sqlite3.connect(target)
        now2 = datetime.datetime.now(datetime.timezone.utc).isoformat()
        replaced = 0
        skipped = 0
        import json as _json
        for pid, (g, _nb) in best.items():
            cur = tc.execute("SELECT payload_json FROM schematic_graph WHERE page_id=?", (pid,)).fetchone()
            existing = 0
            if cur:
                try:
                    existing = len(_json.loads(cur[0]).get("symbols", []))
                except Exception:
                    existing = 0
            if len(g.symbols) > existing:
                tc.execute("INSERT OR REPLACE INTO schematic_graph (page_id, payload_json, updated_at) VALUES (?,?,?)",
                           (pid, g.model_dump_json(by_alias=True), now2))
                replaced += 1
            else:
                skipped += 1
        tc.commit()
        tc.close()
        print("\n[SCALONE do %s] zastapiono %d, pominieto %d (bogatsze zostaly)" % (target.name, replaced, skipped))
        return 0

    import backend.db as dbm
    import backend.paths as pm
    out = ROOT / "data" / "schemagen.v1recovered.db"
    dbm.DB_PATH = out
    pm.DB_PATH = out
    if out.exists():
        out.unlink()
    dbm.init_db()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    c = sqlite3.connect(out)
    for pid, (g, _nb) in best.items():
        c.execute("INSERT OR REPLACE INTO schematic_graph (page_id, payload_json, updated_at) VALUES (?,?,?)",
                  (pid, g.model_dump_json(by_alias=True), now))
    c.commit()
    c.close()
    print("\n[OK] Zapisano do data/schemagen.v1recovered.db")
    print("    Sprawdz: python tools/inspect_graph.py data/schemagen.v1recovered.db")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
