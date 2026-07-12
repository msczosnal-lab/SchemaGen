"""Batch eval GT vs runtime na stronach z config/val-pages.yaml.

Uzycie:
    python scripts/eval_val_pages.py
    python scripts/eval_val_pages.py --page p040
    python scripts/eval_val_pages.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.paths import CONFIG, RAW
from backend.recognize.pipeline import recognize_file
from labeler.gt_loader import gt_source, load_gt_schema
from backend.runtime_config import eval_weights, line_match_tol
from backend.validate.diff_metrics import (
    aggregate_score,
    diff_components,
    diff_connections,
    diff_lines,
    diff_tags,
    page_id as resolve_page_id,
)

OUT_DIR = ROOT / "data" / "output" / "eval_val_pages"


def _load_val_pages() -> list[str]:
    path = CONFIG / "val-pages.yaml"
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return list(data.get("val_pages") or [])


def eval_page(pid: str) -> dict | None:
    img = RAW / f"{pid}.png"
    if not img.exists():
        return None

    gt_schema = load_gt_schema(pid)
    src = gt_source(pid)
    gt_bboxes = len(gt_schema.components) if gt_schema else 0
    gt_lines = len(gt_schema.graphic_lines) if gt_schema else 0

    runtime = recognize_file(str(img))

    report: dict = {
        "page_id": pid,
        "image": str(img),
        "gt": {
            "source": src,
            "bboxes": gt_bboxes,
            "lines": gt_lines,
            "connections": len(gt_schema.connections) if gt_schema else 0,
        },
        "runtime": {
            "components": len(runtime.components),
            "graphic_lines": len(runtime.graphic_lines),
            "connections": len(runtime.connections),
            "context_assignments": len(runtime.context_assignments),
            "potentials": len(runtime.potentials),
            "tags_filled": sum(1 for c in runtime.components if c.tag),
            "conn_potential_filled": sum(1 for c in runtime.connections if c.potential),
        },
    }

    if gt_schema:
        report["connections"] = diff_connections(gt_schema, runtime)
        report["components"] = diff_components(gt_schema, runtime)
        report["tags"] = diff_tags(gt_schema, runtime)
        report["lines"] = diff_lines(gt_schema, runtime, tol=line_match_tol())
        report["score"] = aggregate_score(report, eval_weights())

    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--page", help="Skrot p040 lub pelny page_id")
    ap.add_argument(
        "--pages",
        nargs="+",
        help="Wiele stron (p028 p029) — nadpisuje val-pages.yaml",
    )
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.pages:
        pages = [resolve_page_id(p) for p in args.pages]
    elif args.page:
        pages = [resolve_page_id(args.page)]
    else:
        pages = _load_val_pages()

    if not pages:
        print("[BLAD] Brak val_pages w config/val-pages.yaml")
        return 1

    reports: list[dict] = []
    for pid in pages:
        r = eval_page(pid)
        if r is None:
            print(f"[POMIN] Brak obrazu: {pid}")
            continue
        reports.append(r)

    if not reports:
        print("[BLAD] Zaden raport — brak danych lokalnych")
        return 1

    scored = [r for r in reports if "score" in r]
    summary = {
        "pages": len(reports),
        "total_conn_match": sum(r.get("connections", {}).get("match", 0) for r in reports),
        "total_conn_gt": sum(r.get("connections", {}).get("gt_count", 0) for r in reports),
        "total_bbox_match": sum(r.get("components", {}).get("match", 0) for r in reports),
        "mean_score": round(
            sum(r["score"]["score"] for r in scored) / len(scored), 2
        )
        if scored
        else None,
        "reports": reports,
    }

    if args.json:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        path = OUT_DIR / "report.json"
        path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        print(path)
    else:
        print(f"=== eval_val_pages ({len(reports)} stron) ===")
        for r in reports:
            pid = r["page_id"]
            conn = r.get("connections", {})
            comp = r.get("components", {})
            score = r.get("score", {}).get("score")
            score_txt = f" | score {score:.1f}" if score is not None else ""
            print(
                f"{pid}: bbox {comp.get('match', '?')}/{comp.get('gt_count', '?')} | "
                f"conn {conn.get('match', '?')}/{conn.get('gt_count', '?')} | "
                f"tags {r['runtime'].get('tags_filled', 0)}{score_txt}"
            )
        if summary["mean_score"] is not None:
            print(f"MEAN SCORE: {summary['mean_score']:.2f}/100")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
