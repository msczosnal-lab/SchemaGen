"""Podglad LineTracer + LineClassifier na stronach schematu — HTML + PNG.

Smoke test filaru linii po commicie Claude (002/003).

Uzycie:
    python scripts/preview_lines.py --page data/raw/22_A_153_PL_Adamed_AGV_SA2_20250706_p035.png
    python scripts/preview_lines.py --offset 24 --limit 6
"""

from __future__ import annotations

import argparse
import glob
import json
from collections import Counter
from pathlib import Path

import cv2

from backend.paths import RAW
from backend.recognize.line_classifier import LineClassifier
from backend.recognize.line_sieve import apply_sieve
from backend.recognize.line_tracer import LineTracer

OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "output" / "preview_lines"

# Kolory rol w overlayu (BGR). wire vs frame musza byc wyraznie rozne — wczesniej
# dwie prawie identyczne zielenie ukrywaly demot ramki. frame -> pomarancz.
# Martwy klucz "bus" usuniety (rola wycofana w ADR connection-model).
ROLE_COLORS_BGR = {
    "wire": (60, 220, 60),        # jaskrawa zielen
    "device_stroke": (255, 51, 153),  # rozowy
    "dash": (160, 160, 160),      # szary
    "frame": (0, 140, 255),       # pomarancz
    "crossing": (241, 196, 15),   # turkus
}


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _draw_lines(img, lines, segments) -> None:
    for seg in segments:
        color = (200, 200, 200)
        cv2.line(
            img,
            (int(seg.x1), int(seg.y1)),
            (int(seg.x2), int(seg.y2)),
            color,
            1,
            cv2.LINE_AA,
        )
    for line in lines:
        if len(line.points) < 2:
            continue
        p1, p2 = line.points[0], line.points[-1]
        color = ROLE_COLORS_BGR.get(line.role, (149, 165, 166))
        cv2.line(
            img,
            (int(p1[0]), int(p1[1])),
            (int(p2[0]), int(p2[1])),
            color,
            2,
            cv2.LINE_AA,
        )
        mx = int((p1[0] + p2[0]) / 2)
        my = int((p1[1] + p2[1]) / 2)
        label = line.role
        if line.semantic_group:
            label += f"/{line.semantic_group}"
        cv2.putText(
            img,
            label,
            (mx + 4, my - 4),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            color,
            1,
            cv2.LINE_AA,
        )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--page", type=Path)
    ap.add_argument("--pages", nargs="*", help="globy PNG")
    ap.add_argument("--limit", type=int, default=6)
    ap.add_argument("--offset", type=int, default=24, help="domyslnie p025+ Adamed")
    ap.add_argument(
        "--min-line-length",
        type=int,
        default=None,
        help="Jawny prog Hough (px); domyslnie None = auto z config/runtime.yaml",
    )
    ap.add_argument("--max-line-gap", type=int, default=None)
    ap.add_argument("--hough-threshold", type=int, default=None)
    ap.add_argument(
        "--legacy-hough",
        action="store_true",
        help="Stare progi 30/8/50 (tylko kalibracja historyczna — na 6600px daje ~800+ seg)",
    )
    ap.add_argument(
        "--with-sieve",
        action="store_true",
        help="Po klasyfikacji: sito jak w GraphBuilder (wymaga detekcji YOLO)",
    )
    ap.add_argument("--out", type=Path, default=OUT_DIR)
    args = ap.parse_args()

    if args.page:
        pages = [args.page]
    elif args.pages:
        pages = sorted({Path(p) for pat in args.pages for p in glob.glob(pat)})
        if args.limit:
            pages = pages[: args.limit]
    else:
        pages = sorted(RAW.glob("*.png"))[args.offset : args.offset + args.limit]
    if not pages:
        print("[BLAD] Brak stron.")
        return 1

    min_len = 30 if args.legacy_hough else args.min_line_length
    max_gap = 8 if args.legacy_hough else args.max_line_gap
    hough_thr = 50 if args.legacy_hough else args.hough_threshold

    tracer = LineTracer(
        min_line_length=min_len,
        max_line_gap=max_gap,
        hough_threshold=hough_thr,
    )
    classifier = LineClassifier()
    args.out.mkdir(parents=True, exist_ok=True)

    per_page: list[dict] = []
    total_segs = 0
    role_totals: Counter = Counter()

    for page in pages:
        img = cv2.imread(str(page))
        if img is None:
            print(f"{page.stem}: nie wczytano")
            continue
        h, w = img.shape[:2]
        segments = tracer.trace(str(page))
        lines = classifier.classify(segments, image_size=(w, h))
        roles_pre = Counter(l.role for l in lines)
        if args.with_sieve:
            from backend.models.schema import Component
            from backend.recognize.graph_builder import GraphBuilder

            dets = GraphBuilder()._detect(str(page))
            components = [
                Component(
                    id=f"sym_{i}",
                    type=d.class_name,
                    bbox=[d.x, d.y, d.x + d.width, d.y + d.height],
                    source="yolo",
                )
                for i, d in enumerate(dets)
            ]
            edge_tol = max(6.0, 0.004 * max(w, h))
            lines = apply_sieve(lines, components, [], edge_tol=edge_tol)
        roles = Counter(l.role for l in lines)
        groups = Counter(l.semantic_group for l in lines if l.semantic_group)
        total_segs += len(segments)
        role_totals.update(roles)

        overlay = img.copy()
        _draw_lines(overlay, lines, segments)
        name = f"{page.stem}.png"
        cv2.imwrite(str(args.out / name), overlay)

        per_page.append({
            "page": page.stem,
            "image": name,
            "segments": len(segments),
            "lines": len(lines),
            "roles": dict(roles),
            "roles_pre_sieve": dict(roles_pre) if args.with_sieve else None,
            "groups": dict(groups),
            "longest": max((s.length for s in segments), default=0),
        })
        extra = f" pre_sieve={dict(roles_pre)}" if args.with_sieve else ""
        print(
            f"{page.stem}: seg={len(segments)} lines={len(lines)} "
            f"roles={dict(roles)}{extra}"
        )

    legend = " ".join(
        f"<span class='chip' style='border-color:#{c[2]:02x}{c[1]:02x}{c[0]:02x}'>"
        f"{_esc(role)}</span>"
        for role, c in ROLE_COLORS_BGR.items()
    )
    sections = []
    for p in per_page:
        chips = " ".join(
            f"<span class='chip'>{_esc(k)}={v}</span>" for k, v in p["roles"].items()
        ) or "<span class='muted'>0</span>"
        sections.append(
            f"<section><h2>{_esc(p['page'])} "
            f"<small>{p['segments']} seg / {p['lines']} lines</small></h2>"
            f"<div class='chips'>{chips}</div>"
            f"<div class='imgwrap'><img src='{p['image']}' loading='lazy'></div></section>"
        )

    html = f"""<!DOCTYPE html><html lang="pl"><head><meta charset="UTF-8">
<title>Line preview</title><style>
body{{font-family:Segoe UI,Arial,sans-serif;background:#1e1e1e;color:#eee;margin:0;padding:16px}}
section{{margin:20px 0;border-top:1px solid #444;padding-top:10px}}
.chip{{display:inline-block;background:#2d2d2d;border:1px solid #444;border-radius:10px;
padding:2px 8px;margin:2px;font-size:.8rem}}
.imgwrap{{overflow:auto;background:#111;border:1px solid #333;max-height:80vh}}
img{{max-width:100%;height:auto;display:block}}
small,.muted{{color:#aaa}}
</style></head><body>
<h1>Line preview — {len(per_page)} stron, {total_segs} segmentow</h1>
<p>{legend}</p>
{''.join(sections)}
</body></html>"""
    summary = {
        "pages": len(per_page),
        "total_segments": total_segs,
        "role_totals": dict(role_totals),
        "per_page": per_page,
        "params": {
            "min_line_length": min_len,
            "max_line_gap": max_gap,
            "hough_threshold": hough_thr,
            "legacy_hough": args.legacy_hough,
            "with_sieve": args.with_sieve,
        },
    }
    (args.out / "index.html").write_text(html, encoding="utf-8")
    (args.out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nGaleria: {args.out / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
