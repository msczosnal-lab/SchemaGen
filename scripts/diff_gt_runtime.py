"""Diff GT (labeler) vs runtime (recognize_file) — connections i filary.

Uzycie:
    python scripts/diff_gt_runtime.py --page 22_A_153_PL_Adamed_AGV_SA2_20250706_p040
    python scripts/diff_gt_runtime.py --page p040 --json

Kazdy run dopisuje score do data/output/diff_gt_runtime/{pid}_history.jsonl
i pokazuje delte vs poprzedni run (zadanie 020).
"""

from __future__ import annotations

import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.paths import RAW
from backend.recognize.pipeline import recognize_file
from backend.runtime_config import eval_weights, line_match_tol
from backend.validate.diff_metrics import (
    aggregate_score,
    diff_components,
    diff_connections,
    diff_lines,
    diff_tags,
    page_id,
)
from labeler.gt_loader import gt_source, load_gt_schema

OUT_DIR = _ROOT / "data" / "output" / "diff_gt_runtime"


def _git_head() -> str:
    try:
        return (
            subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                cwd=_ROOT,
                timeout=5,
            ).stdout.strip()
            or ""
        )
    except Exception:
        return ""


def _append_history(pid: str, score: dict) -> dict | None:
    """Dopisuje run do historii JSONL, zwraca poprzedni wpis (do delty)."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    hist = OUT_DIR / f"{pid}_history.jsonl"
    prev = None
    if hist.exists():
        lines = [ln for ln in hist.read_text(encoding="utf-8").splitlines() if ln.strip()]
        if lines:
            try:
                prev = json.loads(lines[-1])
            except json.JSONDecodeError:
                prev = None
    entry = {
        "ts": datetime.datetime.now().isoformat(timespec="seconds"),
        "git": _git_head(),
        "score": score.get("score", 0.0),
        "per_layer": score.get("per_layer", {}),
    }
    with hist.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return prev


def _print_score(score: dict, prev: dict | None) -> None:
    print(f"SCORE: {score['score']:.2f}/100", end="")
    if prev is not None:
        delta = score["score"] - float(prev.get("score", 0.0))
        print(f"  (Δ {delta:+.2f} vs {prev.get('ts', '?')} {prev.get('git', '')})")
    else:
        print("  (pierwszy run — brak delty)")
    prev_layers = (prev or {}).get("per_layer", {})
    for layer, d in score.get("per_layer", {}).items():
        line = f"  {layer:12s} f1={d['f1']:.3f} w={d['weight']:.2f} -> {d['contribution']:.1f}"
        if layer in prev_layers:
            line += f"  (Δf1 {d['f1'] - float(prev_layers[layer].get('f1', 0.0)):+.3f})"
        print(line)


def _print_loss_buckets(report: dict) -> None:
    buckets: list[tuple[int, str]] = []
    conn = report.get("connections", {})
    comp = report.get("components", {})
    tags = report.get("tags", {})
    buckets.append((len(conn.get("only_gt", [])), "connections brakujace w runtime"))
    buckets.append((len(comp.get("only_gt", [])), "komponenty niewykryte (only_gt)"))
    buckets.append((len(comp.get("only_runtime", [])), "komponenty nadmiarowe (only_runtime)"))
    buckets.append((len(tags.get("only_gt", [])), "tagi brakujace"))
    lines_d = report.get("lines", {})
    if lines_d:
        missing_line_pct = int(round((1.0 - lines_d.get("recall", 0.0)) * 100))
        buckets.append((missing_line_pct, "% dlugosci linii GT bez pokrycia runtime"))
    buckets.sort(reverse=True)
    print("Top kubly strat:")
    for n, name in buckets[:3]:
        if n > 0:
            print(f"  {n:4d}  {name}")
    gaps = comp.get("model_gaps", [])
    if gaps:
        print("[MODEL] klasy z GT bez ani jednego trafienia (retrain, nie kod):")
        for typ in gaps:
            print(f"  - {typ or '(bez typu)'}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--page", required=True)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    pid = page_id(args.page)
    img = RAW / f"{pid}.png"
    if not img.exists():
        print(f"[BLAD] Brak {img}")
        return 1

    gt_schema = load_gt_schema(pid)
    src = gt_source(pid)
    gt_bboxes = len(gt_schema.components) if gt_schema else 0
    gt_lines = len(gt_schema.graphic_lines) if gt_schema else 0

    runtime = recognize_file(str(img))

    report = {
        "page_id": pid,
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
            "tags_filled": sum(1 for c in runtime.components if c.tag),
        },
    }

    prev = None
    if gt_schema:
        report["connections"] = diff_connections(gt_schema, runtime)
        report["components"] = diff_components(gt_schema, runtime)
        report["tags"] = diff_tags(gt_schema, runtime)
        report["lines"] = diff_lines(gt_schema, runtime, tol=line_match_tol())
        report["score"] = aggregate_score(report, eval_weights())
        prev = _append_history(pid, report["score"])

    if args.json:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        path = OUT_DIR / f"{pid}.json"
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(path)
        if "score" in report:
            _print_score(report["score"], prev)
    else:
        conn = report.get("connections", {})
        comp = report.get("components", {})
        tags = report.get("tags", {})
        lines_d = report.get("lines", {})
        print(f"=== {pid} ===")
        src = report["gt"].get("source") or "brak"
        print(f"GT [{src}]: {gt_bboxes} bbox, {gt_lines} linii, {conn.get('gt_count', 0)} conn")
        print(
            f"Runtime: {len(runtime.components)} sym, "
            f"{len(runtime.graphic_lines)} linii, {conn.get('runtime_count', 0)} conn"
        )
        print(f"Bbox match (IoU>=0.5): {comp.get('match', 0)}/{comp.get('gt_count', 0)}")
        print(f"Tag match: {tags.get('match', 0)}")
        print(f"Conn match: {conn.get('match', 0)}/{conn.get('gt_count', 0)}")
        if lines_d:
            print(
                f"Linie: P={lines_d.get('precision', 0):.3f} "
                f"R={lines_d.get('recall', 0):.3f} F1={lines_d.get('f1', 0):.3f} "
                f"(tol={lines_d.get('tol')}px)"
            )
        if "score" in report:
            _print_score(report["score"], prev)
            _print_loss_buckets(report)
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
