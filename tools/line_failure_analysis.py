"""CLI: analiza powodu pudła per linia GT vs auto-draft.

Uzycie:
    python -m tools.line_failure_analysis p028 p029 p030 p033
    python -m tools.line_failure_analysis --from-val --json
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from backend.db import load_schematic_graph
from backend.models.schematic_graph import SchematicGraph
from backend.paths import CONFIG, ROOT, resolve_page_id
from backend.validate.line_failure_analysis import analyze_line_failures
from labeler.auto_draft import build_auto_draft
from tools.progress_cli import make_progress

OUT_DIR = ROOT / "data" / "output" / "line_failure_analysis"
SPRINT_PAGES = ["p028", "p029", "p030", "p033"]


def _load_val_sprint_pages() -> list[str]:
    path = CONFIG / "val-pages.yaml"
    if not path.exists():
        return [resolve_page_id(p) for p in SPRINT_PAGES]
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    pages = [str(p) for p in (data.get("val_pages") or []) if p]
    sprint = {resolve_page_id(p) for p in SPRINT_PAGES}
    picked = [p for p in pages if p in sprint]
    return picked or [resolve_page_id(p) for p in SPRINT_PAGES]


def analyze_page(page_id: str, *, quiet: bool = False) -> dict:
    pid = resolve_page_id(page_id)
    gt_raw = load_schematic_graph(pid)
    if not gt_raw:
        raise FileNotFoundError(f"Brak GT v2: {pid}")
    gt_graph = SchematicGraph.model_validate(gt_raw)
    short = pid.split("_")[-1]
    prog = make_progress(short, quiet)
    draft, _report = build_auto_draft(pid, progress=prog)
    analysis = analyze_line_failures(gt_graph, draft)
    return {
        "page_id": pid,
        "gt_lines": len(gt_graph.lines),
        "draft_lines": len(draft.lines),
        "analysis": analysis,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pages", nargs="*", help="p028 ...")
    ap.add_argument("--from-val", action="store_true", help="p028-p033 z val-pages")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if args.pages:
        pages = [resolve_page_id(p) for p in args.pages]
    elif args.from_val:
        pages = _load_val_sprint_pages()
    else:
        pages = [resolve_page_id(p) for p in SPRINT_PAGES]

    results: list[dict] = []
    for i, pid in enumerate(pages, 1):
        if not args.json:
            print(f"[{i}/{len(pages)}] {pid.split('_')[-1]}...", flush=True)
        try:
            results.append(analyze_page(pid, quiet=args.quiet or args.json))
        except Exception as exc:
            results.append({"page_id": pid, "error": str(exc)})
            if not args.json:
                print(f"  BLAD: {exc}", file=sys.stderr)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pages": len(results),
        "results": results,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    json_path = OUT_DIR / f"report_{stamp}.json"
    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    csv_path = OUT_DIR / f"lines_{stamp}.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["page_id", "line_id", "from", "to", "kind", "status", "reason"])
        for r in results:
            if "error" in r:
                continue
            for ln in r["analysis"]["lines"]:
                w.writerow(
                    [
                        r["page_id"],
                        ln.get("line_id"),
                        ln.get("from"),
                        ln.get("to"),
                        ln.get("kind"),
                        ln.get("status"),
                        ln.get("reason"),
                    ]
                )

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(f"=== line_failure_analysis ({len(results)} stron) ===")
        for r in results:
            if "error" in r:
                print(f"  {r['page_id']}: BLAD — {r['error']}")
                continue
            a = r["analysis"]
            rc = a.get("reason_counts", {})
            top = ", ".join(f"{k}={v}" for k, v in list(rc.items())[:4])
            print(
                f"  {r['page_id'][-4:]}: matched {a['matched']}/{a['gt_count']} | {top}"
            )
        print(f"JSON: {json_path}")
        print(f"CSV:  {csv_path}")

    return 0 if all("error" not in r for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
