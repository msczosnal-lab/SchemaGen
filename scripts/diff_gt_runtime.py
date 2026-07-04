"""Diff GT (labeler) vs runtime (recognize_file) — connections i filary.

Uzycie:
    python scripts/diff_gt_runtime.py --page 22_A_153_PL_Adamed_AGV_SA2_20250706_p040
    python scripts/diff_gt_runtime.py --page p040 --json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.db import load_annotation
from backend.models.label import LabelRecord
from backend.paths import RAW
from backend.recognize.pipeline import recognize_file
from labeler.export import label_to_schema

OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "output" / "diff_gt_runtime"


def _norm_conn(c) -> tuple[str, str, str]:
    return (str(c.from_ref), str(c.to), str(getattr(c, "kind", "power")))


def _page_id(raw: str) -> str:
    if raw.startswith("22_"):
        return raw
    return f"22_A_153_PL_Adamed_AGV_SA2_20250706_{raw}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--page", required=True)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    page_id = _page_id(args.page)
    img = RAW / f"{page_id}.png"
    if not img.exists():
        print(f"[BLAD] Brak {img}")
        return 1

    gt_data = load_annotation(page_id)
    gt_conns: set[tuple[str, str, str]] = set()
    gt_lines = 0
    gt_bboxes = 0
    if gt_data:
        rec = LabelRecord.model_validate(gt_data)
        gt_schema = label_to_schema(rec)
        gt_conns = {_norm_conn(c) for c in gt_schema.connections}
        gt_lines = len(rec.lines)
        gt_bboxes = len(rec.bboxes)

    runtime = recognize_file(str(img))
    rt_conns = {_norm_conn(c) for c in runtime.connections}

    only_gt = sorted(gt_conns - rt_conns)
    only_rt = sorted(rt_conns - gt_conns)
    both = sorted(gt_conns & rt_conns)

    report = {
        "page_id": page_id,
        "gt": {"bboxes": gt_bboxes, "lines": gt_lines, "connections": len(gt_conns)},
        "runtime": {
            "components": len(runtime.components),
            "graphic_lines": len(runtime.graphic_lines),
            "connections": len(rt_conns),
        },
        "connections": {
            "match": len(both),
            "only_gt": only_gt,
            "only_runtime": only_rt,
        },
    }

    if args.json:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        path = OUT_DIR / f"{page_id}.json"
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(path)
    else:
        print(f"=== {page_id} ===")
        print(f"GT: {gt_bboxes} bbox, {gt_lines} linii, {len(gt_conns)} conn")
        print(
            f"Runtime: {len(runtime.components)} sym, "
            f"{len(runtime.graphic_lines)} linii, {len(rt_conns)} conn"
        )
        print(f"Match connections: {len(both)}")
        print(f"Tylko GT ({len(only_gt)}):")
        for a, b, k in only_gt[:20]:
            print(f"  {a} -> {b} ({k})")
        if len(only_gt) > 20:
            print(f"  ... +{len(only_gt) - 20}")
        print(f"Tylko runtime ({len(only_rt)}):")
        for a, b, k in only_rt[:20]:
            print(f"  {a} -> {b} ({k})")
        if len(only_rt) > 20:
            print(f"  ... +{len(only_rt) - 20}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
