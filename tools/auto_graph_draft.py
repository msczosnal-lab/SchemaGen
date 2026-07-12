"""CLI: auto-draft GT v2 z pełnego pipeline runtime + raport diff.

Uzycie:
    python -m tools.auto_graph_draft p028
    python -m tools.auto_graph_draft p028 --save --force
    python -m tools.auto_graph_draft p028 p029 p030 p033 --json
"""

from __future__ import annotations

import argparse
import json
import sys
import time

from backend.paths import resolve_page_id
from labeler.auto_draft import build_auto_draft, save_auto_draft
from tools.progress_cli import make_progress


def _print_report(report: dict) -> None:
    pid = report.get("page_id", "?")
    draft = report.get("draft", {})
    print(f"=== {pid} ===")
    print(
        f"  draft: {draft.get('symbols', 0)} sym, {draft.get('lines', 0)} linii"
    )
    rt = report.get("runtime", {})
    print(
        f"  runtime: {rt.get('components', 0)} comp, "
        f"{rt.get('connections', 0)} conn, {rt.get('graphic_lines', 0)} gl"
    )
    if "gt" in report:
        gt = report["gt"]
        print(f"  GT: {gt.get('symbols', 0)} sym, {gt.get('lines', 0)} linii")
    if "diff" in report:
        d = report["diff"]
        sym = d.get("symbols", {})
        ln = d.get("lines", {})
        print(
            f"  diff sym: {sym.get('match', '?')}/{sym.get('gt_count', '?')} "
            f"F1={sym.get('f1', 0):.3f}"
        )
        print(
            f"  diff lin: {ln.get('match', '?')}/{ln.get('gt_count', '?')} "
            f"F1={ln.get('f1', 0):.3f}"
        )
        fp = d.get("only_draft_symbols", [])
        fn = d.get("only_gt_symbols", [])
        if fp:
            print(f"  FP sym (draft only): {len(fp)}")
        if fn:
            print(f"  FN sym (GT only): {len(fn)}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pages", nargs="+", help="p028 lub pelny page_id")
    ap.add_argument("--save", action="store_true", help="zapisz draft do gt/")
    ap.add_argument("--force", action="store_true", help="nadpisz istniejacy GT")
    ap.add_argument("--json", action="store_true", help="JSON na stdout")
    ap.add_argument("--quiet", action="store_true", help="bez progresu etapowego")
    args = ap.parse_args()

    total_pages = len(args.pages)
    results: list[dict] = []
    for i, raw in enumerate(args.pages, 1):
        pid = resolve_page_id(raw)
        label = raw if len(raw) <= 8 else pid[-4:]
        prog = None if args.json else make_progress(label, args.quiet)
        if not args.json:
            short = pid.split("_")[-1]
            print(f"[{i}/{total_pages}] {short} — rozpoznawanie...", flush=True)
        t0 = time.monotonic()
        try:
            if args.save:
                out = save_auto_draft(pid, force=args.force, progress=prog)
                report = out.get("report", {})
                results.append(out)
            else:
                _graph, report = build_auto_draft(pid, progress=prog)
                results.append({"status": "preview", "page_id": pid, "report": report})
            if not args.json:
                print(f"  ukonczono w {time.monotonic() - t0:.1f}s", flush=True)
                _print_report(report if args.save else results[-1]["report"])
        except Exception as exc:
            err = {"page_id": pid, "error": str(exc)}
            results.append(err)
            if not args.json:
                print(f"[BLAD] {pid}: {exc}", file=sys.stderr)

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0 if all("error" not in r for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
