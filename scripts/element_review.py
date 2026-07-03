"""Przegladarka WSZYSTKICH oznaczonych elementow (cropy) z zaznaczaniem do usuniecia.

Renderuje siatke HTML (styl jak mostek_orient_preview): crop + tag/klasa + strona +
checkbox. Filtr po klasie, licznik zaznaczonych, przycisk pobrania listy do usuniecia
(JSON: ["<page_id>|<bbox_id>", ...]). Usuniecie wykonuje osobno scripts/apply_delete.py.

    python scripts/element_review.py                  # wszystkie klasy
    python scripts/element_review.py --class mostek    # tylko jedna klasa (tag)
    python scripts/element_review.py --min-score 0.55  # tylko mostek: dodaj score NCC
Wynik: data/output/element_review.html
"""
from __future__ import annotations

import argparse
import io

from backend.paths import RAW, ROOT
from backend.class_map import tag_to_class
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

    items = []  # (klasa, tag, page_id, bbox_id, crop)
    for rec in recs:
        page = imgs.get(rec.page_id)
        if page is None:
            continue
        for b in rec.bboxes:
            tag = (b.tag or "").strip()
            cls = tag_to_class(tag) or tag or "(bez tagu)"
            if args.cls and args.cls.lower() not in (cls.lower(), tag.lower()):
                continue
            crop = crop_bbox(page, b.x, b.y, b.width, b.height)
            if crop.size == 0:
                continue
            items.append((cls, tag, rec.page_id, b.id, crop))

    items.sort(key=lambda t: (t[0], t[2]))
    if args.limit:
        items = items[: args.limit]

    classes = sorted({it[0] for it in items})
    filter_btns = "".join(
        f'<button onclick="flt(\'{c}\')">{c}</button> ' for c in classes
    )
    cells = []
    for cls, tag, pid, bid, crop in items:
        val = f"{pid}|{bid}"
        cells.append(
            f'<label class="cell" data-cls="{cls}" '
            f'style="display:inline-block;margin:3px;text-align:center;'
            f'font:10px monospace;border:1px solid #ddd;padding:2px;vertical-align:top">'
            f'<input type="checkbox" class="del" value="{val}" onchange="upd()"><br>'
            f'<img src="data:image/png;base64,{thumb_b64(crop, args.thumb, args.thicken)}" '
            f'style="height:{args.thumb}px;image-rendering:pixelated;background:#fff"><br>'
            f'<b>{cls}</b><br><span style="color:#888">{pid[-4:]}</span></label>'
        )

    html = f"""<html><head><meta charset="utf-8"><style>
button{{margin:2px;cursor:pointer}} #bar{{position:sticky;top:0;background:#fff;
padding:8px;border-bottom:2px solid #333;z-index:9}}</style></head><body>
<div id="bar">
  <b>Elementy: {len(items)}</b> &nbsp; zaznaczono: <span id="cnt">0</span>
  &nbsp;<button onclick="dl()">Pobierz liste do usuniecia (JSON)</button>
  &nbsp;<button onclick="clr()">Odznacz</button><br>
  Filtr: <button onclick="flt('')">[wszystkie]</button> {filter_btns}
</div>
<div id="grid">{''.join(cells)}</div>
<script>
function upd(){{document.getElementById('cnt').innerText=
  document.querySelectorAll('.del:checked').length;}}
function clr(){{document.querySelectorAll('.del:checked').forEach(c=>c.checked=false);upd();}}
function flt(c){{document.querySelectorAll('.cell').forEach(e=>{{
  e.style.display=(!c||e.dataset.cls===c)?'inline-block':'none';}});}}
function dl(){{
  const ids=[...document.querySelectorAll('.del:checked')].map(c=>c.value);
  const blob=new Blob([JSON.stringify(ids,null,0)],{{type:'application/json'}});
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);
  a.download='delete_list.json';a.click();
}}
</script></body></html>"""

    out = ROOT / "data" / "output" / "element_review.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"OK -> {out}  ({len(items)} elementow, {len(classes)} klas)")


if __name__ == "__main__":
    main()
