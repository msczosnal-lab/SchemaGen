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
from scripts.diff_metrics import (
    _page_id,
    diff_components,
    diff_connections,
    diff_tags,
)

OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "output" / "diff_gt_runtime"


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
    gt_lines = 0
    gt_bboxes = 0
    gt_schema = None
    if gt_data:
        rec = LabelRecord.model_validate(gt_data)
        gt_schema = label_to_schema(rec)
        gt_lines = len(rec.lines)
        gt_bboxes = len(rec.bboxes)

    runtime = recognize_file(str(img))

    report = {
        "page_id": page_id,
        "gt": {
            "bboxes": gt_bboxes,
            "lines": gt_lines,
            "connections": len(gt_schema.connections) if gt_schema else 0,
        },
        "runtime": {
            "components": len(runtime.components),
            "graphic_lines": len(runtime.graphic_lines),
            "connections": len(runtime.connections),
            "context_assignments": len(runtime.context_assignments),
            "tags_filled": sum(1 for c in runtime.components if c.tag),
        },
    }

    if gt_schema:
        report["connections"] = diff_connections(gt_schema, runtime)
        report["components"] = diff_components(gt_schema, runtime)
        report["tags"] = diff_tags(gt_schema, runtime)

    if args.json:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        path = OUT_DIR / f"{page_id}.json"
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(path)
    else:
        conn = report.get("connections", {})
        comp = report.get("components", {})
        tags = report.get("tags", {})
        print(f"=== {page_id} ===")
        print(f"GT: {gt_bboxes} bbox, {gt_lines} linii, {conn.get('gt_count', 0)} conn")
        print(
            f"Runtime: {len(runtime.components)} sym, "
            f"{len(runtime.graphic_lines)} linii, {conn.get('runtime_count', 0)} conn"
        )
        print(f"Bbox match (IoU>=0.5): {comp.get('match', 0)}/{comp.get('gt_count', 0)}")
        print(f"Tag match: {tags.get('match', 0)}")
        print(f"Conn match: {conn.get('match', 0)}/{conn.get('gt_count', 0)}")
        only_gt = conn.get("only_gt", [])
        only_rt = conn.get("only_runtime", [])
        print(f"Tylko GT conn ({len(only_gt)}):")
        for a, b, k in only_gt[:10]:
            print(f"  {a} -> {b} ({k})")
        print(f"Tylko runtime conn ({len(only_rt)}):")
        for a, b, k in only_rt[:10]:
            print(f"  {a} -> {b} ({k})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
