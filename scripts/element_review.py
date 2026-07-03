"""Przegladarka WSZYSTKICH oznaczonych elementow: retag lub usun (nie marnuj bboxow).

Crop + strona + <select> klasy (aktualna wybrana) + opcja "usun". Filtr po klasie,
licznik zmian, przycisk pobrania `reassignments.json` (format apply_reassign.py):
    [{"page_id","bbox_id","old","new_tag"}, ...]   (new_tag="__DELETE__" = usun)

    python scripts/element_review.py
    python scripts/element_review.py --class mostek
    python scripts/element_review.py --thumb 120 --thicken 2
Wynik: data/output/element_review.html -> potem scripts/apply_reassign.py
"""
from __future__ import annotations

import argparse
import json

from backend.paths import RAW, ROOT
from backend.class_map import palette_order, tag_to_class
from train.mostek_orient import CLASS_NAMES as MOSTEK_CLASSES
from train.dataset_export import load_labeled_records, _load_page_images
from train.mostek_tiles import crop_bbox

try:
    from scripts._thumb import thumb_b64
except ModuleNotFoundError:
    from _thumb import thumb_b64


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--class", dest="cls", default="", help="filtr: tylko ten tag/klasa")
    ap.add_argument("--limit", type=int, default=0, help="max cropow (0=wszystko)")
    ap.add_argument("--thumb", type=int, default=96, help="wysokosc miniatury px")
    ap.add_argument("--thicken", type=int, default=1, help="ile razy pogrubic linie")
    args = ap.parse_args()

    recs = load_labeled_records()
    imgs = _load_page_images(recs, RAW)

    items = []  # (klasa, page_id, bbox_id, crop)
    seen_classes = set()
    for rec in recs:
        page = imgs.get(rec.page_id)
        if page is None:
            continue
        for b in rec.bboxes:
            tag = (b.tag or "").strip()
            cls = tag_to_class(tag) or tag or "(bez tagu)"
            seen_classes.add(cls)
            if args.cls and args.cls.lower() not in (cls.lower(), tag.lower()):
                continue
            crop = crop_bbox(page, b.x, b.y, b.width, b.height)
            if crop.size == 0:
                continue
            items.append((cls, rec.page_id, b.id, crop))

    items.sort(key=lambda t: (t[0], t[1]))
    if args.limit:
        items = items[: args.limit]

    dropdown = sorted(set(palette_order()) | set(MOSTEK_CLASSES) | seen_classes)
    filt_classes = sorted({it[0] for it in items})
    filter_btns = "".join(
        f'<button onclick="flt(\'{c}\')">{c}</button> ' for c in filt_classes
    )

    cells = []
    for cls, pid, bid, crop in items:
        cells.append(
            f'<div class="cell" data-cls="{cls}" '
            f'style="display:inline-block;margin:3px;text-align:center;'
            f'font:10px monospace;border:1px solid #ddd;padding:2px;vertical-align:top">'
            f'<img src="data:image/png;base64,{thumb_b64(crop, args.thumb, args.thicken)}" '
            f'style="height:{args.thumb}px;image-rendering:pixelated;background:#fff"><br>'
            f'<span style="color:#888">{pid[-4:]}</span><br>'
            f'<select class="cs" data-pid="{pid}" data-bid="{bid}" '
            f'data-orig="{cls}" onchange="upd()"></select></div>'
        )

    html = f"""<html><head><meta charset="utf-8"><style>
button{{margin:2px;cursor:pointer}} #bar{{position:sticky;top:0;background:#fff;
padding:8px;border-bottom:2px solid #333;z-index:9}} select{{font:10px monospace;max-width:110px}}
.chg select{{background:#fff3cd}} .del select{{background:#f8d7da}}</style></head><body>
<div id="bar">
  <b>Elementy: {len(items)}</b> &nbsp; zmian: <span id="cnt">0</span>
  &nbsp;<button onclick="dl()">Pobierz reassignments.json</button>
  &nbsp;<button onclick="rst()">Cofnij wszystkie</button><br>
  Filtr: <button onclick="flt('')">[wszystkie]</button> {filter_btns}
</div>
<div id="grid">{''.join(cells)}</div>
<script>
const CLASSES={json.dumps(dropdown, ensure_ascii=False)};
const DEL="__DELETE__";
document.querySelectorAll('.cs').forEach(s=>{{
  const orig=s.dataset.orig; let h='';
  if(!CLASSES.includes(orig)) h+=`<option value="${{orig}}">${{orig}}</option>`;
  for(const c of CLASSES) h+=`<option value="${{c}}">${{c}}</option>`;
  h+=`<option value="${{DEL}}">🗑 usun</option>`;
  s.innerHTML=h; s.value=orig;
}});
function upd(){{
  let n=0;
  document.querySelectorAll('.cs').forEach(s=>{{
    const cell=s.closest('.cell'); const chg=s.value!==s.dataset.orig;
    cell.classList.toggle('chg',chg && s.value!==DEL);
    cell.classList.toggle('del',s.value===DEL);
    if(chg) n++;
  }});
  document.getElementById('cnt').innerText=n;
}}
function rst(){{document.querySelectorAll('.cs').forEach(s=>s.value=s.dataset.orig);upd();}}
function flt(c){{document.querySelectorAll('.cell').forEach(e=>{{
  e.style.display=(!c||e.dataset.cls===c)?'inline-block':'none';}});}}
function dl(){{
  const out=[];
  document.querySelectorAll('.cs').forEach(s=>{{
    if(s.value!==s.dataset.orig) out.push({{page_id:s.dataset.pid,
      bbox_id:s.dataset.bid, old:s.dataset.orig, new_tag:s.value}});
  }});
  const blob=new Blob([JSON.stringify(out)],{{type:'application/json'}});
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);
  a.download='reassignments.json';a.click();
}}
</script></body></html>"""

    out = ROOT / "data" / "output" / "element_review.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"OK -> {out}  ({len(items)} elementow, {len(dropdown)} klas w dropdown)")


if __name__ == "__main__":
    main()
