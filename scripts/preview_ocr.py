"""Podglad OCR (PaddleOCR) na stronach schematu — HTML + PNG.

Smoke test filaru tekst po commicie Claude (002-ocr).

Uzycie:
    python scripts/preview_ocr.py --page data/raw/22_A_153_PL_Adamed_AGV_SA2_20250706_p035.png
    python scripts/preview_ocr.py --offset 20 --limit 5
    python scripts/preview_ocr.py --lang latin --use-gpu
"""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import cv2

from backend.paths import RAW
from backend.recognize.ocr_engine import PaddleOcrEngine, TextDetection

OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "output" / "preview_ocr"


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _draw(img, dets: list[TextDetection]) -> None:
    for d in dets:
        x1, y1, x2, y2 = (int(v) for v in d.bbox)
        cv2.rectangle(img, (x1, y1), (x2, y2), (52, 152, 219), 2)
        label = f"{d.text} {d.confidence:.0%}"
        cv2.putText(
            img, label, (x1 + 2, max(y1 - 4, 14)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (52, 152, 219), 1, cv2.LINE_AA,
        )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--page", type=Path, help="pojedynczy PNG")
    ap.add_argument("--pages", nargs="*", help="globy PNG")
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--lang", default="en", help="en | latin (PL diakrytyki)")
    ap.add_argument("--use-gpu", action="store_true", help="GPU w workerze OCR")
    ap.add_argument("--cpu", action="store_true", help="wymus CPU (domyslnie gdy brak --use-gpu)")
    ap.add_argument("--out", type=Path, default=OUT_DIR)
    args = ap.parse_args()

    if args.page:
        pages = [args.page]
    elif args.pages:
        pages = sorted({Path(p) for pat in args.pages for p in glob.glob(pat)})
    else:
        pages = sorted(RAW.glob("*.png"))[args.offset : args.offset + args.limit]
    if not pages:
        print("[BLAD] Brak stron.")
        return 1

    use_gpu = args.use_gpu and not args.cpu
    try:
        engine = PaddleOcrEngine(use_gpu=use_gpu, lang=args.lang)
    except ImportError as exc:
        print(f"[BLAD] {exc}")
        return 1

    args.out.mkdir(parents=True, exist_ok=True)
    per_page: list[dict] = []
    total = 0

    for page in pages:
        img = cv2.imread(str(page))
        if img is None:
            print(f"{page.stem}: nie wczytano")
            continue
        try:
            dets = engine.extract_text(page)
        except Exception as exc:
            print(f"{page.stem}: OCR blad — {exc}")
            continue
        _draw(img, dets)
        name = f"{page.stem}.png"
        cv2.imwrite(str(args.out / name), img)
        texts = [d.text for d in dets]
        per_page.append({
            "page": page.stem,
            "image": name,
            "count": len(dets),
            "texts": texts[:30],
        })
        total += len(dets)
        print(f"{page.stem}: {len(dets)} linii tekstu")

    sections = []
    for p in per_page:
        chips = " ".join(
            f"<span class='chip'>{_esc(t)}</span>" for t in p["texts"]
        ) or "<span class='muted'>0</span>"
        sections.append(
            f"<section><h2>{_esc(p['page'])} <small>{p['count']} detekcji</small></h2>"
            f"<div class='chips'>{chips}</div>"
            f"<div class='imgwrap'><img src='{p['image']}' loading='lazy'></div></section>"
        )
    html = f"""<!DOCTYPE html><html lang="pl"><head><meta charset="UTF-8">
<title>OCR preview — {args.lang}</title><style>
body{{font-family:Segoe UI,Arial,sans-serif;background:#1e1e1e;color:#eee;margin:0;padding:16px}}
section{{margin:20px 0;border-top:1px solid #444;padding-top:10px}}
.chip{{display:inline-block;background:#2d2d2d;border:1px solid #444;border-radius:10px;
padding:2px 8px;margin:2px;font-size:.8rem}}
.imgwrap{{overflow:auto;background:#111;border:1px solid #333;max-height:80vh}}
img{{max-width:100%;height:auto;display:block}}
small,.muted{{color:#aaa}}
</style></head><body>
<h1>OCR preview — {len(per_page)} stron, {total} detekcji <small>(lang={args.lang})</small></h1>
{''.join(sections)}
</body></html>"""
    (args.out / "index.html").write_text(html, encoding="utf-8")
    (args.out / "summary.json").write_text(
        json.dumps({"lang": args.lang, "pages": len(per_page), "total": total,
                    "per_page": per_page}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nGaleria: {args.out / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
