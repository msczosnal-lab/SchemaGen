"""Diagnostyka wspolrzednych bboxow (READ-ONLY, nic nie zapisuje).

Per strona pokazuje zwiazek: zapisane image_width/height vs faktyczny PNG vs
zasieg bboxow. Wykrywa typ bledu skalowania i sugeruje wspolczynnik.

Uzycie:
    python scripts/diag_coords.py
    python scripts/diag_coords.py --page SchematWRT01_p013
"""

from __future__ import annotations

import argparse
import json
import sqlite3

from backend.models.label import LabelRecord
from backend.paths import DB_PATH, RAW
from labeler.export import find_raw_image
from backend.geometry.coord_scale import image_size


def diag(page_filter: str | None) -> int:
    if not DB_PATH.exists():
        print(f"[BŁĄD] Brak bazy: {DB_PATH}")
        return 1
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT page_id, payload_json FROM annotations").fetchall()
    conn.close()

    hdr = f"{'page_id':<26} {'stored WxH':>13} {'png WxH':>13} {'bbox L,T..R,B':>22} {'ext%':>6} {'diag'}"
    print(hdr)
    print("-" * len(hdr))
    for page_id, payload_json in sorted(rows):
        if page_filter and page_id != page_filter:
            continue
        rec = LabelRecord.model_validate(json.loads(payload_json))
        if not rec.bboxes:
            continue
        sw, sh = rec.image_width or 0, rec.image_height or 0
        src = find_raw_image(rec, RAW)
        png = image_size(src) if src else None
        pw, ph = (png if png else (0, 0))

        left = min(b.x for b in rec.bboxes)
        top = min(b.y for b in rec.bboxes)
        right = max(b.x + b.width for b in rec.bboxes)
        bottom = max(b.y + b.height for b in rec.bboxes)
        ext = (right / pw if pw else 0, bottom / ph if ph else 0)

        # diagnoza
        diag = []
        if not png:
            diag.append("BRAK PNG")
        else:
            if sw and abs(pw / sw - 1) > 0.02:
                diag.append(f"PNG/stored x{pw/sw:.2f}")
            if right > pw + 2 or bottom > ph + 2:
                diag.append("OVERFLOW(za duze)")
            elif max(ext) < 0.55:
                diag.append(f"CIASNO ext{max(ext):.0%} (niedoskalowane?)")
            else:
                diag.append("ok-zasieg")
        sug = ""
        if png and sw and abs(pw / sw - 1) > 0.02:
            sug = f" -> --factor {pw/sw:.3f}"
        print(f"{page_id:<26} {sw}x{sh:<7} {pw}x{ph:<7} "
              f"{left:.0f},{top:.0f}..{right:.0f},{bottom:.0f}".ljust(22)
              + f" {max(ext):.0%}".rjust(7) + f"  {', '.join(diag)}{sug}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--page", default=None)
    args = ap.parse_args()
    return diag(args.page)


if __name__ == "__main__":
    raise SystemExit(main())
