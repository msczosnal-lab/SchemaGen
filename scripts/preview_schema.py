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
from backend.recognize.line_classifier import LineClassifier
from backend.recognize.graph_builder import _terminal_tol
from backend.recognize.net_builder import _group_into_nets, _nodes_on_net
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


# Kolory BGR
_C_WIRE = (40, 200, 40)      # zielony — wykryty przewod
_C_BUS = (220, 120, 0)       # niebieski — szyna (deprecated, gdyby byl)
_C_BBOX = (0, 150, 255)      # pomaranczowy — bbox symbolu
_C_TERM = (0, 215, 255)      # zolty — terminal
_C_CONN = (40, 40, 230)      # czerwony — logiczne polaczenie (Connection)


def _anchor(ref: str, comps_by_id: dict) -> tuple[int, int] | None:
    """Punkt kotwicy dla 'comp' lub 'comp:terminal' (srodek bbox / pozycja terminala)."""
    cid = str(ref).split(":", 1)[0]
    c = comps_by_id.get(cid)
    if c is None or len(c.bbox) < 4:
        return None
    x1, y1, x2, y2 = c.bbox[:4]
    if ":" in str(ref):
        tid = str(ref).split(":", 1)[1]
        for t in c.terminals:
            if str(t.id) == tid:
                return int(x1 + t.x * (x2 - x1)), int(y1 + t.y * (y2 - y1))
    return int((x1 + x2) / 2), int((y1 + y2) / 2)


def draw_schema(img: np.ndarray, schema, title: str) -> np.ndarray:
    # Przygas tlo (oryginalny schemat -> blady), zeby overlay byl czytelny
    white = np.full_like(img, 255)
    out = cv2.addWeighted(img, 0.30, white, 0.70, 0)

    # 1) Wykryte przewody (kandydaci Connection) — wyrazny kolor wg roli
    for ln in schema.graphic_lines:
        if ln.role not in ("wire", "bus"):
            continue
        pts = np.array(ln.points, dtype=np.int32)
        if len(pts) >= 2:
            color = _C_BUS if ln.role == "bus" else _C_WIRE
            cv2.polylines(out, [pts], False, color, 3, cv2.LINE_AA)

    # 2) Bboxy symboli + terminale (z etykieta id)
    for c in schema.components:
        if len(c.bbox) < 4:
            continue
        x1, y1, x2, y2 = map(int, c.bbox[:4])
        cv2.rectangle(out, (x1, y1), (x2, y2), _C_BBOX, 2)
        for t in c.terminals:
            ax = int(x1 + t.x * (x2 - x1))
            ay = int(y1 + t.y * (y2 - y1))
            cv2.circle(out, (ax, ay), 7, (255, 255, 255), -1)
            cv2.circle(out, (ax, ay), 7, _C_TERM, 2)
            cv2.circle(out, (ax, ay), 2, (0, 0, 0), -1)
            cv2.putText(out, str(t.id), (ax + 8, ay - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2, cv2.LINE_AA)

    # 3) Logiczne polaczenia — czerwona linia miedzy kotwicami from/to
    comps_by_id = {c.id: c for c in schema.components}
    for conn in schema.connections:
        a = _anchor(conn.from_ref, comps_by_id)
        b = _anchor(conn.to, comps_by_id)
        if a is None or b is None:
            continue
        dashed = conn.kind == "link"  # mostek listwy — odroznij
        if dashed:
            cv2.line(out, a, b, _C_CONN, 2, cv2.LINE_AA)
            cv2.circle(out, a, 4, _C_CONN, -1)
            cv2.circle(out, b, 4, _C_CONN, -1)
        else:
            cv2.line(out, a, b, _C_CONN, 2, cv2.LINE_AA)

    # 4) Naglowek + legenda + licznik
    cv2.putText(out, title, (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 0, 0), 2)
    legend = [
        (f"connections: {len(schema.connections)}", _C_CONN),
        (f"wire/bus linie: {sum(1 for l in schema.graphic_lines if l.role in ('wire','bus'))}", _C_WIRE),
        (f"symbole: {len(schema.components)}", _C_BBOX),
        ("terminale (zolte)", _C_TERM),
    ]
    for i, (txt, col) in enumerate(legend):
        y = 54 + 22 * i
        cv2.putText(out, txt, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 3, cv2.LINE_AA)
        cv2.putText(out, txt, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, col, 1, cv2.LINE_AA)
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
