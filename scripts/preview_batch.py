"""Wsadowy podglad detekcji na wielu stronach -> jedna galeria HTML + metryka.

Ocena WZROKOWA modelu na realnych stronach (lepsza niz mAP z malego val).
Liczy te? agregat: ile detekcji per klasa na calym zestawie (metryka preview).

Uzycie:
    python scripts/preview_batch.py --limit 15
    python scripts/preview_batch.py --pages data/raw/*_p03*.png --conf 0.25
    python scripts/preview_batch.py --version symbols_mc_v2 --conf 0.2
"""

from __future__ import annotations

import argparse
import glob
import json
from collections import Counter
from pathlib import Path

import cv2

from backend.paths import MODELS, RAW, REGISTRY_PATH
from backend.runtime_config import yolo_conf_threshold
from labeler.export import load_class_map
from backend.recognize.symbol_detector import OnnxSymbolDetector

OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "output" / "preview_batch"
PALETTE = [(46, 204, 113), (231, 76, 60), (52, 152, 219), (241, 196, 15),
           (155, 89, 182), (26, 188, 156), (230, 126, 34), (149, 165, 166)]


def active_version() -> str:
    if REGISTRY_PATH.exists():
        try:
            return json.loads(REGISTRY_PATH.read_text(encoding="utf-8")).get("active") or "symbols_mc_v2"
        except (json.JSONDecodeError, OSError):
            pass
    return "symbols_mc_v2"


def _color(class_id: int) -> tuple:
    return PALETTE[class_id % len(PALETTE)]


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pages", nargs="*", help="globy/sciezki PNG (domyslnie z data/raw)")
    ap.add_argument("--limit", type=int, default=15, help="ile stron gdy brak --pages")
    ap.add_argument("--offset", type=int, default=0, help="pomin pierwsze N stron (np. tytulowe)")
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
        pages = sorted(RAW.glob("*.png"))[args.offset : args.offset + args.limit]
    if not pages:
        print("[BŁĄD] Brak stron do podgladu.")
        return 1

    class_map = load_class_map()
    det = OnnxSymbolDetector(str(onnx), class_map)
    args.out.mkdir(parents=True, exist_ok=True)

    per_class: Counter = Counter()
    per_page: list[dict] = []
    for page in pages:
        img = cv2.imread(str(page))
        if img is None:
            continue
        dets = det.detect(str(page), conf_threshold=conf)
        counts: Counter = Counter()
        for d in dets:
            counts[d.class_name] += 1
            per_class[d.class_name] += 1
            c = _color(d.class_id)
            x, y = int(d.x), int(d.y)
            cv2.rectangle(img, (x, y), (int(d.x + d.width), int(d.y + d.height)), c, 3)
            cv2.putText(img, f"{d.class_name} {d.confidence:.0%}", (x + 2, max(y - 5, 14)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, c, 2, cv2.LINE_AA)
        name = f"{page.stem}.png"
        cv2.imwrite(str(args.out / name), img)
        per_page.append({"page": page.stem, "image": name, "count": len(dets),
                         "by_class": dict(counts.most_common())})
        print(f"{page.stem}: {len(dets)} detekcji")

    # galeria
    sections = []
    for p in per_page:
        chips = " ".join(f"<span class='chip'>{_esc(k)}: {v}</span>"
                         for k, v in p["by_class"].items()) or "<span class='muted'>0</span>"
        sections.append(
            f"<section><h2>{_esc(p['page'])} <small>{p['count']} detekcji</small></h2>"
            f"<div class='chips'>{chips}</div>"
            f"<div class='imgwrap'><img src='{p['image']}' loading='lazy'></div></section>"
        )
    summary = "".join(
        f"<tr><td>{_esc(k)}</td><td>{v}</td></tr>" for k, v in per_class.most_common()
    ) or "<tr><td colspan='2'>Brak detekcji</td></tr>"
    total = sum(per_class.values())
    html = f"""<!DOCTYPE html><html lang="pl"><head><meta charset="UTF-8">
<title>Preview batch — {onnx.stem}</title><style>
body{{font-family:Segoe UI,Arial,sans-serif;background:#1e1e1e;color:#eee;margin:0;padding:16px}}
h1{{margin:0 0 8px}} section{{margin:20px 0;border-top:1px solid #444;padding-top:10px}}
small,.muted{{color:#aaa;font-weight:normal}} .chips{{margin:6px 0}}
.chip{{display:inline-block;background:#2d2d2d;border:1px solid #444;border-radius:10px;
padding:2px 8px;margin:2px;font-size:.8rem}}
.imgwrap{{overflow:auto;background:#111;border:1px solid #333;max-height:80vh}}
img{{max-width:100%;height:auto;display:block}}
table{{border-collapse:collapse;font-size:.9rem;margin:8px 0}} td{{border-bottom:1px solid #333;padding:4px 12px}}
</style></head><body>
<h1>{onnx.stem} — {len(per_page)} stron, {total} detekcji <small>(conf ≥ {conf})</small></h1>
<h3>Detekcje per klasa (metryka preview)</h3>
<table><tr><th>klasa</th><th>liczba</th></tr>{summary}</table>
{''.join(sections)}
</body></html>"""
    (args.out / "index.html").write_text(html, encoding="utf-8")
    (args.out / "summary.json").write_text(
        json.dumps({"model": onnx.name, "conf": conf, "pages": len(per_page),
                    "total": total, "per_class": dict(per_class.most_common())},
                   ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nRazem: {len(per_page)} stron, {total} detekcji")
    print(f"Galeria: {args.out / 'index.html'}")
    print("Per klasa:")
    for k, v in per_class.most_common():
        print(f"  {v:5d}  {k}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
