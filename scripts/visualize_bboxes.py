"""Wizualizacja bboxow ground-truth z SQLite na stronach PNG.

Cel: zobaczyc bboxy w AKTUALNYCH koordynatach (po skalowaniu) i wykryc bledy
skalowania (bboxy poza obrazem = czerwone). Dziala na danych Filipa (data/schemagen.db
+ data/raw/*.png) — na PC ZW bez bazy wypisze ostrzezenie.

Uzycie:
    python scripts/visualize_bboxes.py                 # wszystkie oznaczone strony
    python scripts/visualize_bboxes.py --page SchematWRT01_p013
    python scripts/visualize_bboxes.py --out data/output/bbox_overlay

Wynik (data/output/bbox_overlay/):
    <page_id>.png   — strona z nalozonymi bboxami (zielone OK, czerwone = overflow)
    index.html      — galeria + tabele tagow per strona
    report.json     — statystyki: bboxy/strone, overflow, rozklad tagow (pod klasy SSN)
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from pathlib import Path

import cv2

from backend.models.label import LabelRecord
from backend.paths import DB_PATH, RAW, ROOT
from labeler.export import find_raw_image

OUT_DIR = ROOT / "data" / "output" / "bbox_overlay"

GREEN = (46, 204, 113)
RED = (60, 60, 231)
TOL = 2.0  # tolerancja px na granicy obrazu


def _load_records(page_filter: str | None) -> list[LabelRecord]:
    if not DB_PATH.exists():
        print(f"[BŁĄD] Brak bazy: {DB_PATH}. Uruchom na PC z danymi (Filip).")
        return []
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT page_id, payload_json FROM annotations").fetchall()
    conn.close()
    records: list[LabelRecord] = []
    for page_id, payload_json in rows:
        if page_filter and page_id != page_filter:
            continue
        rec = LabelRecord.model_validate(json.loads(payload_json))
        if rec.bboxes:
            records.append(rec)
    return sorted(records, key=lambda r: r.page_id)


def _overflow(b, w: int, h: int) -> bool:
    return b.x < -TOL or b.y < -TOL or (b.x + b.width) > w + TOL or (b.y + b.height) > h + TOL


def render_page(record: LabelRecord, out_dir: Path) -> dict | None:
    src = find_raw_image(record, RAW)
    if src is None:
        print(f"[RYZYKO] {record.page_id}: brak PNG w data/raw — pomijam")
        return None
    img = cv2.imread(str(src))
    if img is None:
        print(f"[RYZYKO] {record.page_id}: nie wczytano {src.name}")
        return None
    h, w = img.shape[:2]

    overflow = 0
    items = []
    for i, b in enumerate(record.bboxes, 1):
        bad = _overflow(b, w, h)
        overflow += int(bad)
        color = RED if bad else GREEN
        x, y = int(b.x), int(b.y)
        cv2.rectangle(img, (x, y), (int(b.x + b.width), int(b.y + b.height)), color, 2)
        cv2.putText(img, str(i), (x + 2, max(y - 4, 12)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
        items.append({
            "n": i, "tag": b.tag or "", "class": b.class_name,
            "x": round(b.x, 1), "y": round(b.y, 1),
            "w": round(b.width, 1), "h": round(b.height, 1),
            "overflow": bad,
        })

    out_dir.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_dir / f"{record.page_id}.png"), img)
    return {
        "page_id": record.page_id, "image": f"{record.page_id}.png",
        "img_w": w, "img_h": h, "n_bbox": len(record.bboxes),
        "overflow": overflow, "items": items,
    }


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_html(pages: list[dict], out_dir: Path) -> None:
    blocks = []
    for p in pages:
        warn = (f"<span style='color:#e74c3c'>⚠ {p['overflow']} poza obrazem</span>"
                if p["overflow"] else "<span style='color:#2ecc71'>OK</span>")
        rows = "".join(
            f"<tr class='{'bad' if it['overflow'] else ''}'><td>{it['n']}</td>"
            f"<td>{_esc(it['class'])}</td><td>{_esc(it['tag'][:80])}</td>"
            f"<td>{it['x']:.0f},{it['y']:.0f}</td><td>{it['w']:.0f}×{it['h']:.0f}</td></tr>"
            for it in p["items"]
        )
        blocks.append(f"""
<section>
  <h2>{p['page_id']} <small>{p['img_w']}×{p['img_h']} px · {p['n_bbox']} bbox · {warn}</small></h2>
  <div class="row">
    <div class="imgwrap"><img src="{p['image']}" loading="lazy"></div>
    <table><thead><tr><th>#</th><th>klasa</th><th>tag</th><th>xy</th><th>rozmiar</th></tr></thead>
    <tbody>{rows}</tbody></table>
  </div>
</section>""")
    total_bbox = sum(p["n_bbox"] for p in pages)
    total_over = sum(p["overflow"] for p in pages)
    html = f"""<!DOCTYPE html><html lang="pl"><head><meta charset="UTF-8">
<title>BBox overlay — ground truth</title><style>
body{{font-family:Segoe UI,Arial,sans-serif;background:#1e1e1e;color:#eee;margin:0;padding:16px}}
h1{{margin:0 0 12px}} section{{margin:24px 0;border-top:1px solid #444;padding-top:12px}}
small{{color:#aaa;font-weight:normal}} .row{{display:grid;grid-template-columns:1fr 360px;gap:12px}}
.imgwrap{{overflow:auto;background:#111;border:1px solid #333}} img{{max-width:100%;height:auto;display:block}}
table{{width:100%;border-collapse:collapse;font-size:.8rem;align-self:start}}
th,td{{border-bottom:1px solid #333;padding:4px 6px;text-align:left}} tr.bad{{background:#3a1414}}
</style></head><body>
<h1>BBox overlay — {len(pages)} stron · {total_bbox} bbox · <span style="color:{'#e74c3c' if total_over else '#2ecc71'}">{total_over} overflow</span></h1>
{''.join(blocks)}
</body></html>"""
    (out_dir / "index.html").write_text(html, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--page", default=None, help="filtr po page_id")
    ap.add_argument("--out", type=Path, default=OUT_DIR)
    args = ap.parse_args()

    records = _load_records(args.page)
    if not records:
        print("Brak oznaczonych stron z bboxami.")
        return 1

    pages, tags = [], Counter()
    for rec in records:
        meta = render_page(rec, args.out)
        if meta is None:
            continue
        pages.append(meta)
        for it in meta["items"]:
            tags[it["tag"] or "(pusty)"] += 1
        flag = f"⚠ {meta['overflow']} overflow" if meta["overflow"] else "OK"
        print(f"{meta['page_id']}: {meta['n_bbox']} bbox, {flag} -> {meta['image']}")

    build_html(pages, args.out)
    report = {
        "pages": len(pages),
        "total_bbox": sum(p["n_bbox"] for p in pages),
        "total_overflow": sum(p["overflow"] for p in pages),
        "tag_distribution": dict(tags.most_common()),
    }
    (args.out / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nRazem: {report['pages']} stron, {report['total_bbox']} bbox, "
          f"{report['total_overflow']} overflow")
    print(f"Galeria: {args.out / 'index.html'}")
    print(f"Rozklad tagow (pod klasy SSN): {args.out / 'report.json'}")
    print("\nTop 15 tagow:")
    for tag, n in tags.most_common(15):
        print(f"  {n:5d}  {tag[:70]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
