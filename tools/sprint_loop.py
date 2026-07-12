"""Sprint /loop: draft → failure_analysis → eval → export → train → ONNX.

Uzycie:
    python -m tools.sprint_loop --pages p028 p029 p030 p033
    python -m tools.sprint_loop --from-val --train --export-onnx
    python -m tools.sprint_loop --skip-draft --train-only
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from backend.paths import ROOT, resolve_page_id
from tools.line_failure_analysis import SPRINT_PAGES, _load_val_sprint_pages

OUT_DIR = ROOT / "data" / "output" / "sprint_loop"
DEFAULT_TRAIN_NAME = "symbols_sprint_v1"
DEFAULT_ONNX_VERSION = "symbols_sprint_v1"


def _run(cmd: list[str], step: str) -> int:
    print(f"\n--- {step} ---", flush=True)
    print(" ".join(cmd), flush=True)
    t0 = time.monotonic()
    rc = subprocess.call(cmd, cwd=str(ROOT))
    print(f"  ({step} zakonczony w {time.monotonic() - t0:.1f}s, rc={rc})", flush=True)
    return rc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pages", nargs="*", help="strony sprintu (domyslnie p028-p033)")
    ap.add_argument("--from-val", action="store_true")
    ap.add_argument("--skip-draft", action="store_true", help="pomin auto-draft + failure")
    ap.add_argument("--draft-only", action="store_true", help="tylko draft + failure")
    ap.add_argument("--train", action="store_true", help="fine-tune YOLO")
    ap.add_argument("--export-onnx", action="store_true", help="eksport ONNX po treningu")
    ap.add_argument("--train-only", action="store_true", help="export dataset + train + onnx")
    ap.add_argument("--epochs", type=int, default=80)
    ap.add_argument("--name", default=DEFAULT_TRAIN_NAME)
    ap.add_argument("--onnx-version", default=DEFAULT_ONNX_VERSION)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    py = sys.executable
    if args.pages:
        pages = [resolve_page_id(p) for p in args.pages]
    elif args.from_val:
        pages = _load_val_sprint_pages()
    else:
        pages = [resolve_page_id(p) for p in SPRINT_PAGES]

    log: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pages": pages,
        "steps": [],
    }
    rc_total = 0

    if not args.skip_draft and not args.train_only:
        page_args = [p.split("_")[-1] for p in pages]
        cmd = [py, "-m", "tools.line_failure_analysis", *page_args]
        if args.quiet:
            cmd.append("--quiet")
        rc = _run(cmd, "failure_analysis")
        log["steps"].append({"name": "failure_analysis", "rc": rc})
        rc_total |= rc

        cmd = [py, "tools/baseline_eval_gt.py"]
        rc = _run(cmd, "baseline_eval")
        log["steps"].append({"name": "baseline_eval", "rc": rc})
        rc_total |= rc

    if args.draft_only:
        _write_log(log)
        return rc_total

    do_train = args.train or args.train_only or args.export_onnx
    if do_train:
        rc = _run([py, "-m", "train.dataset_export", "--min-count", "1"], "dataset_export")
        log["steps"].append({"name": "dataset_export", "rc": rc})
        rc_total |= rc

        train_cmd = [
            py,
            "-m",
            "train.train_symbols",
            "--name",
            args.name,
            "--epochs",
            str(args.epochs),
            "--fliplr",
            "0.5",
            "--flipud",
            "0.5",
        ]
        rc = _run(train_cmd, "yolo_train")
        log["steps"].append({"name": "yolo_train", "rc": rc, "version": args.name})
        rc_total |= rc

        if args.export_onnx or args.train_only:
            onnx_cmd = [
                py,
                "-m",
                "train.export_onnx",
                "--version",
                args.onnx_version,
            ]
            weights = ROOT / "data" / "runs" / args.name / "weights" / "best.pt"
            if weights.exists():
                onnx_cmd.extend(["--weights", str(weights)])
            rc = _run(onnx_cmd, "export_onnx")
            log["steps"].append({"name": "export_onnx", "rc": rc, "version": args.onnx_version})
            rc_total |= rc

            rc = _run([py, "tools/baseline_eval_gt.py"], "post_train_eval")
            log["steps"].append({"name": "post_train_eval", "rc": rc})
            rc_total |= rc

    _write_log(log)
    print(f"\nRaport sprint_loop: {OUT_DIR / 'last.json'}")
    return rc_total


def _write_log(log: dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / "last.json"
    path.write_text(json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
