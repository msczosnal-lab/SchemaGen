"""Podglad detekcji YOLO na stronie — HTML + PNG (multi-class)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2

from backend.paths import MODELS, RAW, REGISTRY_PATH, raw_image_path
from backend.runtime_config import (
    yolo_conf_threshold,
    yolo_tile_overlap,
    yolo_tile_win,
    yolo_tiled,
)
from labeler.export import load_class_map
from backend.recognize.symbol_detector import OnnxSymbolDetector

OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "output" / "detect_preview"


def active_version() -> str:
    if REGISTRY_PATH.exists():
        try:
            reg = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
            if reg.get("active"):
                return reg["active"]
        except (json.JSONDecodeError, OSError):
            pass
    return "symbols_mc_v1"


def resolve_model(version: str | None, model: Path | None) -> Path:
    if model:
        return model
    ver = version or active_version()
    return MODELS / f"{ver}.onnx"


def find_unlabeled_page() -> Path:
    import sqlite3

    db = Path(__file__).resolve().parents[1] / "data" / "schemagen.db"
    annotated: set[str] = set()
    if db.exists():
        conn = sqlite3.connect(db)
        annotated = {r[0] for r in conn.execute("SELECT page_id FROM annotations")}
        conn.close()
    for png in sorted(RAW.glob("*.png")):
        if png.stem not in annotated:
            return png
    raise FileNotFoundError("Brak nieoznaczonych stron w data/raw/")


def render(page: Path, conf: float | None, out_dir: Path, onnx: Path,
           tiled: bool = False, win: int = 1536, overlap: float = 0.2) -> dict:
    conf = conf if conf is not None else yolo_conf_threshold()
    if not onnx.exists():
        raise FileNotFoundError(
            f"Brak modelu ONNX: {onnx}. Najpierw: python -m train.export_onnx --version {onnx.stem}"
        )
    det = OnnxSymbolDetector(str(onnx), load_class_map())
    if tiled:
        detections = det.detect_tiled(str(page), win=win, overlap=overlap, conf_threshold=conf)
    else:
        detections = det.detect(str(page), conf_threshold=conf)
    img = cv2.imread(str(page))
    if img is None:
        raise FileNotFoundError(f"Nie mozna wczytac: {page}")

    for i, d in enumerate(detections, 1):
        x, y = int(d.x), int(d.y)
        w, h = int(d.width), int(d.height)
        cv2.rectangle(img, (x, y), (x + w, y + h), (46, 204, 113), 3)
        label = f"#{i} {d.class_name} {d.confidence:.0%}"
        cv2.rectangle(img, (x, max(y - 28, 0)), (x + max(len(label) * 11, 60), max(y, 28)), (46, 204, 113), -1)
        cv2.putText(img, label, (x + 4, max(y - 8, 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

    out_dir.mkdir(parents=True, exist_ok=True)
    img_name = "page.png"
    cv2.imwrite(str(out_dir / img_name), img)

    meta = {
        "page": page.name,
        "page_id": page.stem,
        "model": onnx.name,
        "tiled": use_tiled,
        "tile_win": win,
        "tile_overlap": overlap,
        "count": len(detections),
        "detections": [
            {
                "id": i,
                "class": d.class_name,
                "confidence": round(d.confidence, 4),
                "x": round(d.x, 1),
                "y": round(d.y, 1),
                "width": round(d.width, 1),
                "height": round(d.height, 1),
            }
            for i, d in enumerate(detections, 1)
        ],
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    rows = "".join(
        f"<tr><td>#{d['id']}</td><td>{d['class']}</td><td>{d['confidence']:.0%}</td>"
        f"<td>{d['x']:.0f}, {d['y']:.0f}</td><td>{d['width']:.0f}×{d['height']:.0f}</td></tr>"
        for d in meta["detections"]
    ) or "<tr><td colspan='5'>Brak detekcji przy tym progu conf</td></tr>"

    html = f"""<!DOCTYPE html>
<html lang="pl">
<head>
  <meta charset="UTF-8" />
  <title>Detekcja — {page.stem}</title>
  <style>
    body {{ margin: 0; font-family: Segoe UI, Arial, sans-serif; background: #1e1e1e; color: #eee; }}
    header {{ padding: 12px 20px; background: #2d2d2d; border-bottom: 1px solid #444; }}
    main {{ display: grid; grid-template-columns: 1fr 320px; gap: 0; min-height: calc(100vh - 56px); }}
    #img-wrap {{ overflow: auto; padding: 12px; background: #111; }}
    img {{ max-width: 100%; height: auto; border: 1px solid #444; }}
    aside {{ padding: 12px; border-left: 1px solid #444; overflow: auto; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
    th, td {{ border-bottom: 1px solid #333; padding: 6px 4px; text-align: left; }}
    .badge {{ color: #2ecc71; font-weight: bold; }}
    .muted {{ color: #999; font-size: 0.9rem; }}
  </style>
</head>
<body>
  <header>
    <strong>{onnx.stem}</strong> — {page.name}
    <span class="badge"> {meta['count']} detekcji</span>
    <span class="muted"> (conf ≥ {conf})</span>
  </header>
  <main>
    <div id="img-wrap"><img src="{img_name}" alt="schemat z bbox" /></div>
    <aside>
      <h3>Znalezione bboxy</h3>
      <table>
        <thead><tr><th>#</th><th>klasa</th><th>conf</th><th>xy</th><th>rozmiar</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </aside>
  </main>
</body>
</html>"""
    (out_dir / "index.html").write_text(html, encoding="utf-8")
    return meta


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--page",
        default=None,
        help="page_id, skrot p040 lub PNG w data/raw (domyslnie pierwsza nieoznaczona)",
    )
    parser.add_argument("--conf", type=float, default=None)
    parser.add_argument("--version", default=None, help="wersja modelu (domyslnie aktywna z registry)")
    parser.add_argument("--model", type=Path, default=None, help="bezposrednia sciezka do .onnx")
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    parser.add_argument(
        "--tiled",
        action="store_true",
        help="inferencja przesuwnym oknem (domyslnie: yolo_tiled z runtime.yaml)",
    )
    parser.add_argument("--no-tiled", action="store_true", help="wymus detect() bez okien")
    parser.add_argument("--win", type=int, default=None)
    parser.add_argument("--overlap", type=float, default=None)
    args = parser.parse_args()

    if args.page:
        page = raw_image_path(args.page)
        if page is None:
            raise SystemExit(f"[BLAD] Brak obrazu dla: {args.page!r} w {RAW}")
    else:
        page = find_unlabeled_page()

    use_tiled = (args.tiled or yolo_tiled()) and not args.no_tiled
    win = args.win if args.win is not None else yolo_tile_win()
    overlap = args.overlap if args.overlap is not None else yolo_tile_overlap()

    onnx = resolve_model(args.version, args.model)
    meta = render(
        page, args.conf, args.out, onnx,
        tiled=use_tiled, win=win, overlap=overlap,
    )
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
