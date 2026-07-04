"""Relabel: zmiana przypisania klasy bboxom (wnetrza + dropdown klas).

Czyta bboxy z SQLite, tnie wycinki, buduje galerie pogrupowana wg AKTUALNEJ klasy.
Przy kazdym wycinku rozwijana lista klas — zmieniasz, klikasz "Eksport zmian".
Potem: python scripts/apply_reassign.py  (zapisuje do bazy).

Uzycie:
    python scripts/relabel_tool.py
    python scripts/relabel_tool.py --class motor   # tylko jedna (blednie oznaczona) klasa
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

import cv2

from backend.class_map import load_group_map, load_palette_map, palette_order, tag_to_class
from backend.models.label import LabelRecord
from backend.paths import DB_PATH, RAW
from labeler.export import find_raw_image

OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "output" / "relabel"
MAX_CROPS = 2000
PAD = 0.25


def _class_options() -> list[str]:
    opts = set(palette_order())
    opts |= set(load_group_map().values())  # nazwy grup (np. zacisk)
    return sorted(opts)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--class", dest="only", default=None, help="tylko bboxy tej aktualnej klasy")
    ap.add_argument("--out", type=Path, default=OUT_DIR)
    args = ap.parse_args()

    if not DB_PATH.exists():
        print(f"[BŁĄD] Brak bazy: {DB_PATH}")
        return 1
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT page_id, payload_json FROM annotations").fetchall()
    conn.close()

    pmap = load_palette_map()
    gmap = load_group_map()
    args.out.mkdir(parents=True, exist_ok=True)
    for old in args.out.glob("crop_*.png"):
        old.unlink()

    items = []
    n = 0
    for page_id, payload in sorted(rows):
        if page_id.startswith("test"):
            continue
        rec = LabelRecord.model_validate(json.loads(payload))
        if not rec.bboxes:
            continue
        src = find_raw_image(rec, RAW)
        img = cv2.imread(str(src)) if src else None
        if img is None:
            continue
        H, W = img.shape[:2]
        for b in rec.bboxes:
            cls = tag_to_class(b.tag, pmap, gmap)
            if cls is None:
                cls = "(bez tagu)"
            if args.only and cls != args.only:
                continue
            if n >= MAX_CROPS:
                break
            mx, my = PAD * b.width, PAD * b.height
            x1 = max(int(b.x - mx), 0); y1 = max(int(b.y - my), 0)
            x2 = min(int(b.x + b.width + mx), W); y2 = min(int(b.y + b.height + my), H)
            if x2 <= x1 or y2 <= y1:
                continue
            crop = img[y1:y2, x1:x2]
            fn = f"crop_{n:04d}.png"
            cv2.imwrite(str(args.out / fn), crop)
            items.append({"id": n, "img": fn, "page_id": page_id, "bbox_id": b.id,
                          "cur": cls, "tag": b.tag})
            n += 1
        if n >= MAX_CROPS:
            break

    if not items:
        print("Brak bboxow do pokazania.")
        return 1

    present = {it['cur'] for it in items if it['cur'] != '(bez tagu)'}
    options = sorted(set(_class_options()) | present)
    data_js = json.dumps(items, ensure_ascii=False)
    opts_js = json.dumps(options, ensure_ascii=False)
    html = """<!DOCTYPE html><html lang="pl"><head><meta charset="UTF-8">
<title>Relabel</title><style>
body{font-family:Segoe UI,Arial,sans-serif;background:#1e1e1e;color:#eee;margin:0;padding:12px}
header{position:sticky;top:0;background:#1e1e1e;padding:8px 0;border-bottom:1px solid #444;z-index:9}
button{font-size:14px;padding:6px 12px;margin-right:8px;cursor:pointer}
section{margin:14px 0;border-top:1px solid #444;padding-top:6px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:8px}
.cell{background:#2a2a2a;border:2px solid #555;border-radius:5px;padding:4px;text-align:center}
.cell.changed{border-color:#f39c12}
.cell img{max-width:100%;height:70px;object-fit:contain;background:#fff;border-radius:3px}
select{width:100%;margin-top:4px;font-size:11px;background:#222;color:#eee;border:1px solid #555}
.counts{font-size:14px}
</style></head><body>
<header>
  <button onclick="exportJSON()">Eksport zmian (JSON)</button>
  <button onclick="bulkClass()">Zmień całą widoczną klasę…</button>
  <span class="counts" id="counts"></span>
  <span style="color:#999;font-size:12px"> — ustaw klasę przy wycinku. Zmiany zapisują się lokalnie.</span>
</header>
<div id="root"></div>
<script>
const ITEMS=__DATA__, OPTS=__OPTS__;
const KEY="relabel:"+ITEMS.length;
let chg=JSON.parse(localStorage.getItem(KEY)||"{}"); // id -> newClass
function optionsHtml(sel){return OPTS.map(o=>`<option ${o===sel?'selected':''}>${o}</option>`).join("");}
function render(){
  const root=document.getElementById("root"); root.innerHTML="";
  const groups={}; ITEMS.forEach(it=>{(groups[it.cur]=groups[it.cur]||[]).push(it);});
  let nchg=Object.keys(chg).length;
  Object.keys(groups).sort((a,b)=>groups[b].length-groups[a].length).forEach(cur=>{
    const sec=document.createElement("section");
    sec.innerHTML=`<h2>${cur} <small style="color:#aaa">${groups[cur].length} szt.</small></h2>`;
    const g=document.createElement("div"); g.className="grid";
    groups[cur].forEach(it=>{
      const newv=chg[it.id]||it.cur;
      const d=document.createElement("div");
      d.className="cell"+(chg[it.id]&&chg[it.id]!==it.cur?" changed":"");
      d.innerHTML=`<img src="${it.img}" title="${it.tag||''}">
        <select onchange="setCls(${it.id},this.value)">${optionsHtml(newv)}</select>`;
      g.appendChild(d);
    });
    sec.appendChild(g); root.appendChild(sec);
  });
  document.getElementById("counts").textContent=`Zmienione: ${nchg} / ${ITEMS.length}`;
}
function setCls(id,v){const it=ITEMS.find(x=>x.id===id);
  if(v===it.cur)delete chg[id];else chg[id]=v;
  localStorage.setItem(KEY,JSON.stringify(chg));render();}
function bulkClass(){const from=prompt("Zmień wszystkie z klasy:");if(!from)return;
  const to=prompt("na klasę:");if(!to)return;
  ITEMS.filter(x=>x.cur===from).forEach(x=>{if(to===x.cur)delete chg[x.id];else chg[x.id]=to;});
  localStorage.setItem(KEY,JSON.stringify(chg));render();}
function exportJSON(){
  const out=ITEMS.filter(x=>chg[x.id]&&chg[x.id]!==x.cur)
    .map(x=>({page_id:x.page_id,bbox_id:x.bbox_id,old:x.cur,new_tag:chg[x.id]}));
  const blob=new Blob([JSON.stringify(out,null,2)],{type:"application/json"});
  const a=document.createElement("a");a.href=URL.createObjectURL(blob);
  a.download="reassignments.json";a.click();
}
render();
</script></body></html>"""
    html = html.replace("__DATA__", data_js).replace("__OPTS__", opts_js)
    (args.out / "index.html").write_text(html, encoding="utf-8")
    print(f"{len(items)} bboxow -> {args.out / 'index.html'}")
    print("Oklikaj klasy, 'Eksport zmian' -> zapisz reassignments.json do data/, potem:")
    print("  python scripts/apply_reassign.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
