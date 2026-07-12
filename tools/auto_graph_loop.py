"""Pętla active learning: auto-draft → diff → lista stron do review.

Uzycie:
    python -m tools.auto_graph_loop p028 p029 p030 p033
    python -m tools.auto_graph_loop --from-val --save
    python -m tools.auto_graph_loop p040 --save --force
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

from backend.paths import CONFIG, ROOT, resolve_page_id
from labeler.auto_draft import save_auto_draft
from tools.progress_cli import make_progress

OUT_DIR = ROOT / "data" / "output" / "auto_graph_loop"


def _load_val_pages() -> list[str]:
    path = CONFIG / "val-pages.yaml"
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return [str(p) for p in (data.get("val_pages") or []) if p]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pages", nargs="*", help="strony do draftu")
    ap.add_argument("--from-val", action="store_true", help="wszystkie z val-pages.yaml")
    ap.add_argument("--save", action="store_true", help="zapisz drafty do gt/")
    ap.add_argument("--force", action="store_true", help="nadpisz istniejacy GT")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quiet", action="store_true", help="bez progresu etapowego")
    args = ap.parse_args()

    pages = [resolve_page_id(p) for p in args.pages]
    if args.from_val:
        pages = _load_val_pages()
    if not pages:
        print("[BLAD] Brak stron — podaj page_id lub --from-val", file=sys.stderr)
        return 1

    total_pages = len(pages)
    results: list[dict] = []
    for i, pid in enumerate(pages, 1):
        short = pid.split("_")[-1]
        prog = None if args.json else make_progress(short, args.quiet)
        if not args.json:
            print(f"[{i}/{total_pages}] {short} — rozpoznawanie...", flush=True)
        t0 = time.monotonic()
        try:
            if args.save:
                out = save_auto_draft(pid, force=args.force, progress=prog)
            else:
                from labeler.auto_draft import build_auto_draft

                _g, report = build_auto_draft(pid, progress=prog)
                out = {"status": "preview", "page_id": pid, "report": report}
            results.append(out)
            if not args.json:
                print(f"  ukonczono w {time.monotonic() - t0:.1f}s", flush=True)
        except Exception as exc:
            results.append({"page_id": pid, "status": "error", "error": str(exc)})
            if not args.json:
                print(f"  [BLAD] {short}: {exc}", file=sys.stderr, flush=True)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pages": len(results),
        "saved": sum(1 for r in results if r.get("status") == "draft"),
        "skipped": sum(1 for r in results if r.get("status") == "skipped_existing"),
        "errors": sum(1 for r in results if r.get("status") == "error"),
        "review_queue": [
            {
                "page_id": r["page_id"],
                "symbols_todo": (
                    (r.get("symbols_gt") or 0) - (r.get("symbols_match") or 0)
                    if r.get("symbols_gt") is not None
                    else None
                ),
                "lines_todo": (
                    (r.get("lines_gt") or 0) - (r.get("lines_match") or 0)
                    if r.get("lines_gt") is not None
                    else None
                ),
            }
            for r in results
            if r.get("status") in ("draft", "preview")
        ],
        "results": results,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = OUT_DIR / f"loop_{stamp}.json"
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(f"=== auto_graph_loop ({len(results)} stron) ===")
        for r in results:
            st = r.get("status", "?")
            pid = r.get("page_id", "?")
            if st == "error":
                print(f"  {pid}: BLAD — {r.get('error')}")
            elif st == "skipped_existing":
                print(f"  {pid}: pominiety (GT istnieje)")
            else:
                sm = r.get("symbols_match")
                sg = r.get("symbols_gt")
                lm = r.get("lines_match")
                lg = r.get("lines_gt")
                diff_txt = ""
                if sg is not None:
                    diff_txt = f" | sym {sm}/{sg} lin {lm}/{lg}"
                print(
                    f"  {pid}: {st} — {r.get('symbol_count', '?')} sym, "
                    f"{r.get('line_count', '?')} linii{diff_txt}"
                )
        print(f"Raport: {out_path}")
        print("Nastepny krok: labeler http://localhost:8765 → popraw draft → Zapisz → train/dataset_export.py")

    return 0 if summary["errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
