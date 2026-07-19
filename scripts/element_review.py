"""Przegladarka WSZYSTKICH oznaczonych elementow: retag / usun / symetria klasy.

Prompt 028:
  Czesc A — klasyfikacja przez `bbox_class` (jak eksport treningowy i
    class_report), a nie przez sam `tag`. Wczesniej narzedzie klasyfikowalo
    `tag_to_class(tag)`, wiec np. 3 bboxy `type=styki` z tagiem "SAF1/2/3"
    ladowaly w osobnych pseudoklasach — stad 163 (raport) vs 160 (przegladarka).
    Narzedzie raportuje TERAZ jawnie kazdy element, ktorego nie udalo sie
    wyrenderowac, z powodem. Cicha rozbieznosc miedzy raportem a przegladarka
    jest gorsza niz brak przegladarki.
  Czesc B — panel symetrii przy KAZDEJ KLASIE (symetria jest wlasnoscia klasy
    symbolu, nie egzemplarza) + podglad transformacji na cropie wzorcowym.

Interakcja:
  - KLIK w crop  -> ramka CZERWONA = do usuniecia (klik ponownie cofa),
  - zmiana klasy w <select> -> ramka NIEBIESKA = retag (kasuje ew. usuniecie),
  - checkbox przy nazwie klasy (filtr) -> "przejrzana" (zapis w localStorage),
  - panel symetrii przy klasie -> podglad + zapis do symmetry.json.

Pobierz:
  `reassignments.json` (format apply_reassign.py):
      [{"page_id","bbox_id","old","new_tag"}]   new_tag="__DELETE__" = usun
  `symmetry.json` (format apply_symmetry.py):
      {"<klasa>": {"mirror_h":bool,"mirror_v":bool,"rotations":[90,...]}}

    python scripts/element_review.py --thumb 120 --thicken 2
    python scripts/element_review.py --class styki
Wynik: data/output/element_review.html
  -> scripts/apply_reassign.py  /  scripts/apply_symmetry.py
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

# Uruchomienie: python scripts/element_review.py (bez wymogu pip install -e .)
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.paths import RAW, ROOT
from backend.class_map import bbox_class, load_palette_map, palette_order
from backend.symmetry import TRANSFORM_KEYS, load_symmetry_file
from train.mostek_orient import CLASS_NAMES as MOSTEK_CLASSES
from train.dataset_export import load_all_training_records, load_graph_v2_records
from train.mostek_tiles import crop_bbox

try:
    from scripts._thumb import thumb_b64
except ModuleNotFoundError:
    from _thumb import thumb_b64


# Powody, dla ktorych bbox policzony przez class_report nie trafia do siatki.
SKIP_NO_PAGE_IMAGE = "brak PNG strony w data/raw"
SKIP_EMPTY_CROP = "bbox poza kadrem / zerowa powierzchnia"
SKIP_CROP_ERROR = "wyjatek przy wycinaniu cropa"
SKIP_NO_CLASS = "bbox bez type i bez tagu"


def collect_items(recs, imgs, only_class: str = ""):
    """(items, dist_all, skipped) — items renderowalne, dist_all = pelny rozklad
    klas (jak class_report), skipped = [(klasa, page_id, bbox_id, powod)].

    dist_all liczy KAZDY bbox z klasa, niezaleznie od tego, czy da sie go
    narysowac — dzieki temu naglowek przegladarki jest porownywalny 1:1
    z class_report, a roznica jest jawnie wyliczona, nie ukryta.
    """
    pmap = load_palette_map()
    items: list[tuple[str, str, str, object]] = []
    skipped: list[tuple[str, str, str, str]] = []
    dist_all: Counter = Counter()

    for rec in recs:
        for b in rec.bboxes:
            cls = bbox_class(b.class_name, b.tag, pmap)
            if not cls:
                # bez type i bez tagu — class_report tez tego nie liczy,
                # ale raportujemy, zeby nie zniknal po cichu
                skipped.append(("(bez klasy)", rec.page_id, b.id, SKIP_NO_CLASS))
                continue
            dist_all[cls] += 1
            if only_class and only_class.lower() not in (
                cls.lower(),
                (b.tag or "").strip().lower(),
            ):
                continue
            # Obraz strony dopiero TU — przy `--class styki` strony bez tej klasy
            # nie sa w ogole otwierane. `dist_all` liczy sie niezaleznie od obrazow,
            # wiec porownanie z class_report zostaje pelne.
            page = imgs.get(rec.page_id)
            if page is None:
                skipped.append((cls, rec.page_id, b.id, SKIP_NO_PAGE_IMAGE))
                continue
            try:
                crop = crop_bbox(page, b.x, b.y, b.width, b.height)
            except Exception as exc:  # noqa: BLE001 — kazdy blad ma byc widoczny, nie fatalny
                skipped.append((cls, rec.page_id, b.id, f"{SKIP_CROP_ERROR}: {exc}"))
                continue
            if crop.size == 0:
                skipped.append((cls, rec.page_id, b.id, SKIP_EMPTY_CROP))
                continue
            items.append((cls, rec.page_id, b.id, crop))

    return items, dist_all, skipped


def _transform_css(name: str) -> str:
    """Transformacja -> CSS transform dla podgladu miniatury."""
    return {
        "mirror_h": "scaleX(-1)",
        "mirror_v": "scaleY(-1)",
        "rot90": "rotate(90deg)",
        "rot180": "rotate(180deg)",
        "rot270": "rotate(270deg)",
    }[name]


_TRANSFORM_LABEL = {
    "mirror_h": "&#8596; lustro poziome",
    "mirror_v": "&#8597; lustro pionowe",
    "rot90": "&#10227; 90&deg;",
    "rot180": "&#10227; 180&deg;",
    "rot270": "&#10227; 270&deg;",
}


class LazyPageImages:
    """Wczytuje PNG strony na zadanie i trzyma tylko JEDEN w pamieci.

    `_load_page_images` laduje wszystkie strony naraz. Przy 199 stronach
    6617x4678 to ~6 GB w grayscale — maszyna sie dlawi albo proces ginie.
    Crops sa robione strona po stronie, wiec wystarczy biezacy obraz.

    Interfejs `.get(page_id)` zgodny ze slownikiem, zeby `collect_items`
    dzialalo tak samo w testach (zwykly dict) i w produkcji.
    """

    def __init__(self, raw_dir, records) -> None:
        from labeler.export import find_raw_image

        self._find = find_raw_image
        self._raw = raw_dir
        self._by_id = {r.page_id: r for r in records}
        self._cur_id: str | None = None
        self._cur = None
        self.missing: set[str] = set()

    def get(self, page_id: str):
        if page_id == self._cur_id:
            return self._cur
        rec = self._by_id.get(page_id)
        src = self._find(rec, self._raw) if rec is not None else None
        if src is None:
            self.missing.add(page_id)
            self._cur_id, self._cur = page_id, None
            return None
        from PIL import Image
        import numpy as np

        try:
            img = np.asarray(Image.open(src).convert("L"))
        except Exception:  # noqa: BLE001 — nieczytelny plik = strona bez podgladu
            self.missing.add(page_id)
            img = None
        self._cur_id, self._cur = page_id, img
        return img

    def __len__(self) -> int:  # tylko do naglowka
        return len(self._by_id) - len(self.missing)


def _warn_v1_only_pages(v2_recs) -> None:
    """Ostrzez o stronach, gdzie SQLite v1 ma wiecej bboxow niz gt/*.json.

    Te bboxy NIE sa pokazywane (bo nie da sie ich zapisac przez apply_reassign),
    ale uzytkownik musi wiedziec, ze istnieja — inaczej mamy znowu cicha
    rozbieznosc, tyle ze w druga strone.
    """
    try:
        from train.dataset_export import load_labeled_records

        v1 = {r.page_id: len(r.bboxes) for r in load_labeled_records()}
    except Exception as exc:  # noqa: BLE001 — brak/uszkodzona baza nie blokuje przegladu
        print(f"[UWAGA] nie udalo sie porownac z SQLite v1 ({exc}) — pomijam kontrole")
        return
    v2 = {r.page_id: len(r.bboxes) for r in v2_recs}
    worse = [(p, n, v2.get(p, 0)) for p, n in v1.items() if n > v2.get(p, 0)]
    if not worse:
        return
    lost = sum(n - m for _p, n, m in worse)
    print(f"[UWAGA] {len(worse)} stron ma w SQLite v1 wiecej bboxow niz gt/*.json "
          f"({lost} bbox nie jest pokazywanych — nie da sie ich zapisac do GT v2):")
    for p, n, m in sorted(worse, key=lambda t: t[2] - t[1])[:10]:
        print(f"   {p[-5:]}: v1={n} gt={m}")
    print("   Migracja: labeler/migrate_label_v1.py. Podglad v1: --legacy-v1 "
          "(UWAGA: wtedy eksport zmian NIE zapisze sie przez apply_reassign).")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--class", dest="cls", default="", help="filtr: tylko ta klasa/tag")
    ap.add_argument("--legacy-v1", action="store_true",
                    help="czytaj stary merge v1+v2 (id moga nie istniec w gt/ — "
                         "apply_reassign ich nie zapisze)")
    ap.add_argument("--sort", choices=("page", "shape", "size"), default="shape",
                    help="kolejnosc w siatce: shape=wg proporcji bboxa (odstajace "
                         "laduja razem na koncu), size=wg powierzchni, page=wg strony")
    ap.add_argument("--limit", type=int, default=0, help="max cropow (0=wszystko)")
    ap.add_argument("--thumb", type=int, default=96, help="wysokosc miniatury px")
    ap.add_argument("--thicken", type=int, default=1, help="ile razy pogrubic linie")
    args = ap.parse_args()

    # [BŁĄD] 2026-07-19: narzedzie czytalo `load_all_training_records()` — merge
    # SQLite v1 + gt/*.json, gdzie v1 wygrywa, gdy ma wiecej bboxow na stronie.
    # Wtedy przegladarka pokazywala bboxy z id `element_*` (v1), a `apply_reassign`
    # pisze do `gt/*.json` (v2) i tych id tam nie ma — 183 z 241 zmian przepadalo
    # jako "bbox_id nieznalezionych". Przegladarka MUSI czytac to samo zrodlo,
    # do ktorego zapisuje narzedzie stosujace zmiany.
    recs = load_graph_v2_records() if not args.legacy_v1 else load_all_training_records()

    imgs = LazyPageImages(RAW, recs)

    if not args.legacy_v1:
        _warn_v1_only_pages(recs)

    items, dist_all, skipped = collect_items(recs, imgs, args.cls)

    items.sort(key=lambda t: (t[0], t[1]))
    truncated = 0
    if args.limit and len(items) > args.limit:
        truncated = len(items) - args.limit
        items = items[: args.limit]

    rendered = Counter(it[0] for it in items)
    skip_by_class = Counter(s[0] for s in skipped)
    skip_by_reason = Counter(s[3].split(":")[0] for s in skipped)

    # --- konsola: rozbieznosc jawnie, per klasa ---
    n_missing = len(imgs.missing) if hasattr(imgs, "missing") else 0
    print(f"Stron: {len(recs)} | stron bez PNG: {n_missing} "
          f"| bbox z klasa: {sum(dist_all.values())}")
    if args.cls:
        print(f"Filtr klasy: {args.cls!r}")
    mismatched = [
        (c, dist_all[c], rendered.get(c, 0))
        for c in sorted(dist_all)
        if (not args.cls or c in rendered or c in skip_by_class)
        and dist_all[c] != rendered.get(c, 0)
        and (not args.cls or args.cls.lower() == c.lower())
    ]
    if skipped:
        print(f"\n[BŁĄD] {len(skipped)} elementow NIE wyrenderowano. Powody:")
        for reason, n in skip_by_reason.most_common():
            print(f"  {n:>5}  {reason}")
        print("  Rozbicie na klasy (top 15):")
        for c, n in skip_by_class.most_common(15):
            print(f"  {n:>5}  {c}")
    if truncated:
        print(f"[UWAGA] --limit obcial {truncated} elementow (nie sa bledem)")
    if mismatched:
        print("\n[BŁĄD] class_report != przegladarka dla klas:")
        for c, total, shown in mismatched:
            print(f"  {c:<34} raport={total:>5}  narysowano={shown:>5}  brak={total - shown:>4}")

    # --- HTML ---
    seen_classes = set(dist_all)
    dropdown = sorted(set(palette_order()) | set(MOSTEK_CLASSES) | seen_classes)
    filt_classes = sorted({it[0] for it in items})

    sym_cfg = load_symmetry_file(known_classes=seen_classes)
    for w in sym_cfg.warnings:
        print(f"[UWAGA] symbol-symmetry.yaml: {w}")
    sym_init = {
        c: {
            "mirror_h": sym_cfg.get(c).mirror_h,
            "mirror_v": sym_cfg.get(c).mirror_v,
            "rotations": list(sym_cfg.get(c).rotations),
            "note": sym_cfg.get(c).note,
        }
        for c in filt_classes
    }
    # crop wzorcowy klasy = pierwszy wyrenderowany (items posortowane po klasie)
    exemplar: dict[str, str] = {}
    for cls, _pid, _bid, crop in items:
        if cls not in exemplar:
            exemplar[cls] = thumb_b64(crop, args.thumb, args.thicken)

    filter_btns = "".join(
        f'<span class="fbtn" data-c="{c}"><button onclick="flt(\'{c}\')">{c}'
        f' <i>{rendered.get(c, 0)}</i></button>'
        f'<input type="checkbox" class="fchk" data-c="{c}" onchange="rev(this)" '
        f'title="przejrzana"></span> '
        for c in filt_classes
    )

    # panele symetrii — jeden na klase.
    # Podglady WSZYSTKICH transformacji sa zawsze widoczne. Wczesniejsza wersja
    # pokazywala podglad dopiero po zaznaczeniu checkboxa — czyli zeby zobaczyc,
    # jak wyglada lustro, trzeba bylo najpierw wyrazic na nie zgode. W konfiguracji
    # fail-safe to jest odwrotnie niz trzeba: zgoda ma byc SKUTKIEM obejrzenia.
    # Sterowanie symetria = KLIK W PODGLAD, nie checkbox obok. Ogladasz obrocony
    # rysunek i klikasz go, jesli to nadal ten sam symbol — decyzja zapada na tym
    # samym obiekcie, ktory ocenia oko.
    sym_panels = []
    for c in filt_classes:
        denied_in_repo = c in sym_cfg and not sym_cfg.get(c).any_allowed
        previews = "".join(
            f'<span class="pv" data-c="{c}" data-t="{t}" onclick="onsym(this)" '
            f'title="klik = przelacz zgode na {_TRANSFORM_LABEL[t]}">'
            f'<img src="data:image/png;base64,{exemplar.get(c, "")}" '
            f'style="height:{args.thumb}px;transform:{_transform_css(t)};'
            f'image-rendering:pixelated;background:#fff"><br><i>{_TRANSFORM_LABEL[t]}</i>'
            f'<br><b class="pvst">niedozwolone</b></span>'
            for t in TRANSFORM_KEYS
        )
        note = sym_init[c]["note"]
        sym_panels.append(
            f'<div class="sympanel{" denied" if denied_in_repo else ""}" data-c="{c}" '
            f'data-denied="{"1" if denied_in_repo else "0"}" style="display:none">'
            f'<b>Symetria klasy <code>{c}</code></b> '
            f'<span class="hint">klikaj podglady, ktore sa nadal tym samym symbolem '
            f'(wlasnosc klasy, nie egzemplarza — brak zaznaczenia = brak zgody)'
            f'</span>'
            f'<div class="pvrow"><span class="pv0"><img '
            f'src="data:image/png;base64,{exemplar.get(c, "")}" '
            f'style="height:{args.thumb}px;image-rendering:pixelated;background:#fff">'
            f'<br><i>oryginal</i></span>{previews}</div>'
            + (f'<div class="note">{note}</div>' if note else "")
            + "</div>"
        )

    cells = []
    for cls, pid, bid, crop in items:
        cells.append(
            f'<div class="cell" data-cls="{cls}" data-del="0">'
            f'<img onclick="toggleDel(this,event)" src="data:image/png;base64,'
            f'{thumb_b64(crop, args.thumb, args.thicken)}" '
            f'style="height:{args.thumb}px;image-rendering:pixelated;background:#fff"><br>'
            f'<span style="color:#888">{pid[-4:]}</span><br>'
            f'<select class="cs" data-pid="{pid}" data-bid="{bid}" '
            f'data-orig="{cls}" onchange="onsel(this)"></select></div>'
        )

    # tabela rozbieznosci w naglowku
    if mismatched or skipped:
        rows = "".join(
            f"<tr><td>{c}</td><td>{t}</td><td>{s}</td><td>{t - s}</td></tr>"
            for c, t, s in mismatched
        )
        reasons = "".join(f"<li>{n} &times; {r}</li>" for r, n in skip_by_reason.most_common())
        diag_html = (
            '<details id="diag" open><summary><b style="color:#c0392b">'
            f"[BŁĄD] {len(skipped)} elementow nie wyrenderowano</b> — rozwin</summary>"
            f"<ul>{reasons}</ul>"
            + (
                "<table><tr><th>klasa</th><th>class_report</th><th>narysowano</th>"
                f"<th>brak</th></tr>{rows}</table>"
                if rows
                else ""
            )
            + "</details>"
        )
    else:
        diag_html = (
            '<span style="color:#159c4a">&#10003; liczniki zgodne z class_report</span>'
        )

    html = f"""<html><head><meta charset="utf-8"><style>
button{{margin:1px;cursor:pointer}} #bar{{position:sticky;top:0;background:#fff;
padding:8px;border-bottom:2px solid #333;z-index:9;max-height:60vh;overflow:auto}}
.cell{{display:inline-block;margin:3px;text-align:center;font:10px monospace;
border:3px solid #ddd;padding:2px;vertical-align:top;border-radius:4px}}
.cell img{{cursor:pointer}} select{{font:10px monospace;max-width:110px}}
.cell.chg{{border-color:#2563eb;background:#e8f0fe}}
.cell.del{{border-color:#c0392b;background:#fde8e8}}
.fbtn.done button{{background:#c8f7c5;text-decoration:line-through}}
.fbtn i{{color:#888;font-style:normal}}
#diag{{font:11px monospace;background:#fff6f6;border:1px solid #e0b4b4;padding:6px;
margin:4px 0;border-radius:4px}}
#diag table{{border-collapse:collapse;font:11px monospace}}
#diag td,#diag th{{border:1px solid #ddd;padding:1px 6px;text-align:right}}
#diag td:first-child,#diag th:first-child{{text-align:left}}
.sympanel{{font:12px sans-serif;background:#f4f7ff;border:1px solid #b9c8ee;
padding:6px;margin:4px 0;border-radius:4px}}
.sympanel label{{margin-right:10px;cursor:pointer;white-space:nowrap}}
.hint{{color:#666;font-size:11px}}
.sympanel .hint{{color:#666;font-size:11px}}
.sympanel .note{{color:#555;font-size:11px;font-style:italic;margin-top:4px}}
.pvrow{{margin-top:6px;white-space:nowrap;overflow-x:auto}}
.pvrow span{{display:inline-block;text-align:center;margin:2px 8px;font:10px monospace;
color:#555;vertical-align:top}}
.pvrow .pv0 img{{border:2px solid #159c4a}}
.pvrow .pv{{cursor:pointer;border-radius:4px;padding:2px}}
.pvrow .pv:hover{{background:#e8f0fe}}
.pvrow .pv img{{border:2px dashed #bbb;opacity:.55}}
.pvrow .pv.on img{{border:2px solid #2563eb;opacity:1}}
.pvrow .pvst{{color:#999;font-weight:normal}}
.pvrow .pv.on .pvst{{color:#2563eb;font-weight:bold}}
.sympanel.denied{{background:#fff6f6;border-color:#e0b4b4}}
</style></head><body>
<div id="bar">
  <b>Elementy: {len(items)}</b> / {sum(dist_all.values())} w GT &nbsp;
  zmian: <span id="cnt">0</span>
  &nbsp; przejrzano klas: <span id="revcnt">0</span>/{len(filt_classes)}
  &nbsp;<button onclick="dl()">Pobierz reassignments.json</button>
  &nbsp;<button onclick="dlsym()">Pobierz symmetry.json</button>
  &nbsp;<button onclick="dlrev()">Pobierz reviewed.json</button>
  &nbsp;<button onclick="revAll()">Zaznacz wszystkie przejrzane</button>
  &nbsp;<button onclick="revNone()">Odznacz wszystkie</button>
  &nbsp;<button onclick="rst()">Cofnij zmiany</button><br>
  {diag_html}
  <span class="hint">klik = usun / shift+klik = zakres</span><br>
  Filtr: <button onclick="flt('')">[wszystkie]</button> {filter_btns}
  {''.join(sym_panels)}
</div>
<div id="grid">{''.join(cells)}</div>
<script>
const CLASSES={json.dumps(dropdown, ensure_ascii=False)};
const SYM={json.dumps(sym_init, ensure_ascii=False)};
const TKEYS={json.dumps(list(TRANSFORM_KEYS))};
const DEL="__DELETE__";
const RKEY="schemagen_reviewed:"+location.pathname;
const SKEY="schemagen_symmetry:"+location.pathname;
// Zbior klas widocznych TERAZ. Stan "przejrzana" przezywal regeneracje pliku,
// wiec po zmianie przestrzeni nazw klas (migracja tag -> bbox_class) w localStorage
// zostawaly klasy widmo typu `1q4`, `ks2_10` i wyciekaly do reviewed.json.
const LIVE=new Set([...document.querySelectorAll('.fchk')].map(c=>c.dataset.c));
let REV=new Set(JSON.parse(localStorage.getItem(RKEY)||"[]"));
const STALE=[...REV].filter(c=>!LIVE.has(c));
if(STALE.length){{
  REV=new Set([...REV].filter(c=>LIVE.has(c)));
  localStorage.setItem(RKEY,JSON.stringify([...REV]));
  console.warn("usunieto "+STALE.length+" nieaktualnych klas z 'przejrzane': "+STALE.join(", "));
}}
// stan symetrii: yaml jako baza, localStorage nadpisuje (praca w toku)
let SYMST=JSON.parse(JSON.stringify(SYM));
Object.assign(SYMST, JSON.parse(localStorage.getItem(SKEY)||"{{}}"));
function tkeyOn(c,t){{
  const s=SYMST[c]; if(!s) return false;
  if(t==='mirror_h') return !!s.mirror_h;
  if(t==='mirror_v') return !!s.mirror_v;
  return (s.rotations||[]).includes(parseInt(t.slice(3)));
}}
// wypelnij dropdowny
document.querySelectorAll('.cs').forEach(s=>{{
  const orig=s.dataset.orig; let h='';
  if(!CLASSES.includes(orig)) h+=`<option value="${{orig}}">${{orig}}</option>`;
  for(const c of CLASSES) h+=`<option value="${{c}}">${{c}}</option>`;
  s.innerHTML=h; s.value=orig;
}});
// przywroc "przejrzane"
document.querySelectorAll('.fchk').forEach(cb=>{{
  if(REV.has(cb.dataset.c)){{cb.checked=true; cb.closest('.fbtn').classList.add('done');}}
}});
// przywroc stan podgladow symetrii
// Podglady sa ZAWSZE widoczne — zaznaczenie zmienia tylko wyroznienie.
function updPv(c){{document.querySelectorAll(`.pv[data-c="${{CSS.escape(c)}}"]`).forEach(p=>{{
  const on=tkeyOn(c,p.dataset.t);
  p.classList.toggle('on',on);
  const st=p.querySelector('.pvst'); if(st) st.innerText=on?'DOZWOLONE':'niedozwolone';}});}}
Object.keys(SYMST).forEach(updPv);
updRev();
function state(cell){{
  if(cell.dataset.del==='1') return 'del';
  const s=cell.querySelector('.cs');
  if(s.value!==s.dataset.orig) return 'chg';
  return '';
}}
function upd(){{
  let n=0;
  document.querySelectorAll('.cell').forEach(cell=>{{
    const st=state(cell);
    cell.classList.toggle('del',st==='del');
    cell.classList.toggle('chg',st==='chg');
    if(st) n++;
  }});
  document.getElementById('cnt').innerText=n;
}}
// Shift+klik = zakres od ostatnio klikanego do biezacego (jak w menedzerze plikow).
// Zakres liczony po WIDOCZNYCH komorkach, wiec przy aktywnym filtrze klasy
// nie zaznaczy niczego spoza niej.
let LAST=null;
function visibleCells(){{
  return [...document.querySelectorAll('.cell')].filter(c=>c.style.display!=='none');
}}
function toggleDel(img,ev){{
  const cell=img.closest('.cell');
  const vis=visibleCells();
  const i=vis.indexOf(cell);
  if(ev&&ev.shiftKey&&LAST!==null){{
    const j=vis.indexOf(LAST);
    if(j!==-1){{
      const val=LAST.dataset.del;                 // rozciagnij stan zrodla zakresu
      const [a,b]=i<j?[i,j]:[j,i];
      for(let k=a;k<=b;k++) vis[k].dataset.del=val;
      upd(); return;
    }}
  }}
  cell.dataset.del=cell.dataset.del==='1'?'0':'1';
  LAST=cell; upd();
}}
function onsel(s){{s.closest('.cell').dataset.del='0'; upd();}}  // zmiana klasy kasuje usuniecie
function rst(){{document.querySelectorAll('.cell').forEach(c=>{{
  c.dataset.del='0'; const s=c.querySelector('.cs'); s.value=s.dataset.orig;}}); upd();}}
function rev(cb){{const c=cb.dataset.c;
  if(cb.checked)REV.add(c); else REV.delete(c);
  localStorage.setItem(RKEY,JSON.stringify([...REV]));
  cb.closest('.fbtn').classList.toggle('done',cb.checked); updRev();}}
function updRev(){{document.getElementById('revcnt').innerText=REV.size;}}
function setAllRev(on){{
  document.querySelectorAll('.fchk').forEach(cb=>{{
    cb.checked=on;
    if(on) REV.add(cb.dataset.c); else REV.delete(cb.dataset.c);
    cb.closest('.fbtn').classList.toggle('done',on);
  }});
  localStorage.setItem(RKEY,JSON.stringify([...REV])); updRev();
}}
function revAll(){{setAllRev(true);}}
function revNone(){{setAllRev(false);}}
// Klik w podglad przelacza zgode na ta transformacje.
function onsym(el){{
  const c=el.dataset.c, t=el.dataset.t;
  if(!SYMST[c]) SYMST[c]={{mirror_h:false,mirror_v:false,rotations:[],note:""}};
  const s=SYMST[c], on=!tkeyOn(c,t);
  if(t==='mirror_h'||t==='mirror_v') s[t]=on;
  else {{
    const deg=parseInt(t.slice(3)); s.rotations=(s.rotations||[]).filter(r=>r!==deg);
    if(on) s.rotations.push(deg);
    s.rotations.sort((a,b)=>a-b);
  }}
  localStorage.setItem(SKEY,JSON.stringify(SYMST)); updPv(c);
}}
function flt(c){{
  document.querySelectorAll('.cell').forEach(e=>{{
    e.style.display=(!c||e.dataset.cls===c)?'inline-block':'none';}});
  document.querySelectorAll('.sympanel').forEach(p=>{{
    p.style.display=(c&&p.dataset.c===c)?'block':'none';}});
}}
function dl(){{
  const out=[];
  document.querySelectorAll('.cell').forEach(cell=>{{
    const s=cell.querySelector('.cs'); let nt=null;
    if(cell.dataset.del==='1') nt=DEL;
    else if(s.value!==s.dataset.orig) nt=s.value;
    if(nt!==null) out.push({{page_id:s.dataset.pid,bbox_id:s.dataset.bid,
      old:s.dataset.orig,new_tag:nt}});
  }});
  save(JSON.stringify(out),'reassignments.json');
}}
// Klasy oznaczone "przejrzana" = zatwierdzone do treningu. Bez tego eksportu
// informacja zostawala w localStorage i nie widzial jej ani eksport, ani trening.
function dlrev(){{
  const out={{reviewed:[...REV].sort(),
    all_classes:[...document.querySelectorAll('.fchk')].map(c=>c.dataset.c).sort()}};
  save(JSON.stringify(out,null,2),'reviewed.json');
}}
function dlsym(){{
  const out={{}};
  Object.keys(SYMST).sort().forEach(c=>{{
    const s=SYMST[c];
    out[c]={{mirror_h:!!s.mirror_h,mirror_v:!!s.mirror_v,
      rotations:(s.rotations||[]).slice().sort((a,b)=>a-b),note:s.note||""}};
  }});
  save(JSON.stringify(out,null,2),'symmetry.json');
}}
function save(txt,name){{
  const blob=new Blob([txt],{{type:'application/json'}});
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);
  a.download=name;a.click();
}}
</script></body></html>"""

    out = ROOT / "data" / "output" / "element_review.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(
        f"\nOK -> {out}  ({len(items)} cropow, {len(filt_classes)} klas w siatce, "
        f"{len(dropdown)} klas w dropdown)"
    )


if __name__ == "__main__":
    main()
