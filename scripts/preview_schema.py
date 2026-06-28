"""Overlay bbox + linie + connections na stronie schematu (GT lub runtime).

Uzycie:
    python scripts/preview_schema.py --page 22_A_153_PL_Adamed_AGV_SA2_20250706_p040
    python scripts/preview_schema.py --page p040 --source runtime
    python scripts/preview_schema.py --page p040 --source gt
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

from backend.db import load_annotation
from backend.models.label import LabelRecord
from backend.paths import RAW
from backend.recognize.pipeline import recognize_file
from labeler.export import label_to_schema
from labeler.runtime_draft import schema_to_label_record

OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "output" / "preview_schema"


def _find_image(page_id: str) -> Path | None:
    for ext in (".png", ".jpg", ".jpeg"):
        p = RAW / f"{page_id}{ext}"
        if p.exists():
            return p
    return None


def load_gt_schema(page_id: str):
    data = load_annotation(page_id)
    if not data:
        return None
    record = LabelRecord.model_validate(data)
    return label_to_schema(record)


def draw_schema(img: np.ndarray, schema, title: str) -> np.ndarray:
    out = img.copy()
    for c in schema.components:
        if len(c.bbox) < 4:
            continue
        x1, y1, x2, y2 = map(int, c.bbox[:4])
        cv2.rectangle(out, (x1, y1), (x2, y2), (0, 180, 255), 2)
        for t in c.terminals:
            ax = int(x1 + t.x * (x2 - x1))
            ay = int(y1 + t.y * (y2 - y1))
            cv2.circle(out, (ax, ay), 6, (0, 0, 255), -1)
    for ln in schema.graphic_lines:
        if ln.role not in ("wire", "bus"):
            continue
        pts = np.array(ln.points, dtype=np.int32)
        if len(pts) >= 2:
            cv2.polylines(out, [pts], False, (40, 40, 40), 2, cv2.LINE_AA)
    for conn in schema.connections:
        cv2.putText(
            out,
            f"{conn.from_ref}->{conn.to}",
            (10, 30 + 18 * hash(conn.id) % 200),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 128, 0),
            1,
            cv2.LINE_AA,
        )
    cv2.putText(out, title, (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--page", required=True, help="page_id (stem w data/raw)")
    ap.add_argument("--source", choices=("gt", "runtime", "both"), default="both")
    args = ap.parse_args()

    page_id = args.page
    if not page_id.startswith("22_") and "p0" in page_id:
        page_id = f"22_A_153_PL_Adamed_AGV_SA2_20250706_{page_id}"

    img_path = _find_image(page_id)
    if img_path is None:
        print(f"[BLAD] Brak obrazu dla {page_id}")
        return 1
    img = cv2.imread(str(img_path))
    if img is None:
        print("[BLAD] Nie wczytano obrazu")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    written = []

    if args.source in ("gt", "both"):
        gt = load_gt_schema(page_id)
        if gt:
            p = OUT_DIR / f"{page_id}_gt.png"
            cv2.imwrite(str(p), draw_schema(img, gt, "GT"))
            written.append(str(p))
        else:
            print("GT: brak adnotacji w bazie")

    if args.source in ("runtime", "both"):
        schema = recognize_file(str(img_path))
        p = OUT_DIR / f"{page_id}_runtime.png"
        cv2.imwrite(str(p), draw_schema(img, schema, "runtime"))
        written.append(str(p))
        meta = OUT_DIR / f"{page_id}_runtime.json"
        meta.write_text(
            json.dumps(
                {
                    "components": len(schema.components),
                    "graphic_lines": len(schema.graphic_lines),
                    "connections": len(schema.connections),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    print("Zapisano:", *written, sep="\n  ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
