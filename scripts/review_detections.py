"""Przeglad pojedynczych detekcji do recznej oceny (precyzja).

Kazda detekcja = wycinek z kontekstem + narysowana ramka. W przegladarce klikasz
kafelek: szary -> OK (zielony) -> ZLE (czerwony). Przycisk "Eksport ocen" pobiera JSON.

Uzycie:
    python scripts/review_detections.py --limit 30 --offset 15 --conf 0.05
    python scripts/review_detections.py --version symbols_mc_v2 --pages "data/raw/*p03*.png"
"""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import cv2

from backend.paths import MODELS, RAW, REGISTRY_PATH
from backend.runtime_config import yolo_conf_threshold
from labeler.export import load_class_map
from backend.recognize.symbol_detector import OnnxSymbolDetector

OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "output" / "review"
MAX_CROPS = 400
CONTEXT = 0.6  # margines kontekstu = 60% wiekszego boku bboxa


def active_version() -> str:
    if REGISTRY_PATH.exists():
        try:
            return json.loads(REGISTRY_PATH.read_text(encoding="utf-8")).get("active") or "symbols_mc_v2"
        except (json.JSONDecodeError, OSError):
            pass
    return "symbols_mc_v2"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pages", nargs="*")
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--conf", type=float, default=None)
    ap.add_argument("--version", default=None)
    ap.add_argument("--model", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=OUT_DIR)
    args = ap.parse_args()

    conf = args.conf if args.conf is not None else yolo_conf_threshold()
    onnx = args.model or (MODELS / f"{args.version or active_version()}.onnx")
    if not onnx.exists():
        print(f"[BŁĄD] Brak modelu: {onnx}")
        return 1

    if args.pages:
        files: list[Path] = []
        for pat in args.pages:
            files.extend(Path(p) for p in glob.glob(pat))
        pages = sorted(set(files))
    else:
        pages = sorted(RAW.glob("*.png"))[args.offset: args.offset + args.limit]
    if not pages:
        print("[BŁĄD] Brak stron.")
        return 1

    det = OnnxSymbolDetector(str(onnx), load_class_map())
    args.out.mkdir(parents=True, exist_ok=True)
    for old in args.out.glob("crop_*.png"):
        old.unlink()

    items = []
    n = 0
    for page in pages:
        img = cv2.imread(str(page))
        if img is None:
            continue
        H, W = img.shape[:2]
        for d in det.detect(str(page), conf_threshold=conf):
            if n >= MAX_CROPS:
                break
            m = int(CONTEXT * max(d.width, d.height))
            x1, y1 = max(int(d.x) - m, 0), max(int(d.y) - m, 0)
            x2, y2 = min(int(d.x + d.width) + m, W), min(int(d.y + d.height) + m, H)
            crop = img[y1:y2, x1:x2].copy()
            if crop.size == 0:
                continue
            # narysuj wykryta ramke w wycinku
            cv2.rectangle(crop, (int(d.x) - x1, int(d.y) - y1),
                          (int(d.x + d.width) - x1, int(d.y + d.height) - y1), (46, 204, 113), 2)
            fname = f"crop_{n:04d}.png"
            cv2.imwrite(str(args.out / fname), crop)
            items.append({"id": n, "img": fname, "page": page.stem, "cls": d.class_name,
                          "conf": round(d.confidence, 3),
                          "bbox": [round(d.x, 1), round(d.y, 1), round(d.width, 1), round(d.height, 1)]})
            n += 1
        if n >= MAX_CROPS:
            break

    if not items:
        print(f"Brak detekcji przy conf={conf}. Obniz prog.")
        return 1

    data_js = json.dumps(items, ensure_ascii=False)
    html = """<!DOCTYPE html><html lang="pl"><head><meta charset="UTF-8">
<title>Przeglad detekcji</title><style>
body{font-family:Segoe UI,Arial,sans-serif;background:#1e1e1e;color:#eee;margin:0;padding:12px}
header{position:sticky;top:0;background:#1e1e1e;padding:8px 0;border-bottom:1px solid #444;z-index:9}
button{font-size:14px;padding:6px 12px;margin-right:8px;cursor:pointer}
#grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px;margin-top:10px}
.cell{border:3px solid #555;border-radius:6px;padding:4px;background:#2a2a2a;cursor:pointer;text-align:center}
.cell.ok{border-color:#2ecc71} .cell.bad{border-color:#e74c3c}
.cell img{max-width:100%;height:auto;display:block;margin:0 auto;background:#fff}
.cap{font-size:11px;margin-top:3px;color:#ccc;word-break:break-all}
.counts{font-size:14px}
</style></head><body>
<header>
  <button onclick="exportJSON()">Eksport ocen (JSON)</button>
  <span class="counts" id="counts"></span>
  <span style="color:#999;font-size:12px"> — klik: szary→OK→ZLE. Oceny zapisuja sie lokalnie.</span>
</header>
<div id="grid"></div>
<script>
const ITEMS = __DATA__;
const KEY = "review:" + ITEMS.length + ":" + (ITEMS[0]&&ITEMS[0].page);
let marks = JSON.parse(localStorage.getItem(KEY) || "{}");
const grid = document.getElementById("grid");
function cls(v){return v===1?"cell ok":v===2?"cell bad":"cell";}
function render(){
  grid.innerHTML="";
  let ok=0,bad=0,un=0;
  ITEMS.forEach(it=>{
    const v=marks[it.id]||0; if(v===1)ok++;else if(v===2)bad++;else un++;
    const d=document.createElement("div");
    d.className=cls(v);
    d.innerHTML=`<img src="${it.img}" loading="lazy"><div class="cap">${it.cls} ${(it.conf*100).toFixed(0)}%<br>${it.page}</div>`;
    d.onclick=()=>{marks[it.id]=((marks[it.id]||0)+1)%3;localStorage.setItem(KEY,JSON.stringify(marks));render();};
    grid.appendChild(d);
  });
  document.getElementById("counts").textContent=`OK ${ok} | ZLE ${bad} | nieocenione ${un} | razem ${ITEMS.length}`;
}
function exportJSON(){
  const out=ITEMS.map(it=>({...it,verdict:({0:"",1:"ok",2:"bad"})[marks[it.id]||0]}));
  const blob=new Blob([JSON.stringify(out,null,2)],{type:"application/json"});
  const a=document.createElement("a");a.href=URL.createObjectURL(blob);
  a.download="review_verdicts.json";a.click();
}
render();
</script></body></html>"""
    html = html.replace("__DATA__", data_js)
    (args.out / "index.html").write_text(html, encoding="utf-8")
    (args.out / "items.json").write_text(data_js, encoding="utf-8")
    print(f"{len(items)} detekcji do oceny -> {args.out / 'index.html'}")
    print("Otworz w przegladarce, oklikaj, kliknij 'Eksport ocen'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
