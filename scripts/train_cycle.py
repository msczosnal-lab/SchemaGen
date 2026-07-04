"""Powtarzalna petla treningowa: raport -> eksport -> trening -> ONNX -> preview.

Uruchomienie (GPU u Filipa):
    python scripts/train_cycle.py
    python scripts/train_cycle.py --name symbols_atomic_v3 --min-count 5
    python scripts/train_cycle.py --skip-train --name symbols_atomic_v1
    python scripts/train_cycle.py --epochs 30   # szybki test

Log: data/models/train_cycle_log.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.paths import DATA, LABELED, MODELS, REGISTRY_PATH
from train.dataset_export import export_dataset

LOG_PATH = MODELS / "train_cycle_log.jsonl"
PREVIEW_OUT = DATA / "output" / "preview_batch"
VERSION_RE = re.compile(r"^symbols_atomic_v(\d+)$")


def _next_version(prefix: str = "symbols_atomic") -> str:
    """symbols_atomic_vN — najwyzsze N z registry, summary i runs + 1."""
    max_n = 0
    if REGISTRY_PATH.exists():
        try:
            reg = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
            for v in reg.get("versions") or {}:
                m = VERSION_RE.match(v) if prefix == "symbols_atomic" else None
                if m:
                    max_n = max(max_n, int(m.group(1)))
        except (json.JSONDecodeError, OSError):
            pass
    for p in MODELS.glob(f"{prefix}_v*_train_summary.json"):
        m = VERSION_RE.match(p.name.replace("_train_summary.json", ""))
        if m:
            max_n = max(max_n, int(m.group(1)))
    runs = DATA / "runs"
    if runs.exists():
        for d in runs.iterdir():
            if d.is_dir():
                m = VERSION_RE.match(d.name)
                if m:
                    max_n = max(max_n, int(m.group(1)))
    return f"{prefix}_v{max_n + 1}"


def _read_summary(version: str) -> dict | None:
    path = MODELS / f"{version}_train_summary.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _read_manifest() -> dict | None:
    path = LABELED / "export-manifest.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _parse_results_csv(run_dir: Path) -> dict[str, float]:
    """Per-klasa mAP50 z results.csv (best-effort)."""
    csv_path = run_dir / "results.csv"
    if not csv_path.exists():
        return {}
    try:
        import csv

        rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
        if not rows:
            return {}
        last = rows[-1]
        out: dict[str, float] = {}
        for k, v in last.items():
            if k.startswith("metrics/mAP50(") and k.endswith(")"):
                cls = k[len("metrics/mAP50(") : -1]
                try:
                    out[cls] = float(v)
                except (TypeError, ValueError):
                    pass
        if "metrics/mAP50(B)" in last:
            try:
                out["__global__"] = float(last["metrics/mAP50(B)"])
            except (TypeError, ValueError):
                pass
        return out
    except OSError:
        return {}


def _run_class_report(min_count: int) -> str:
    proc = subprocess.run(
        [sys.executable, str(_ROOT / "scripts" / "class_report.py"), "--min-count", str(min_count)],
        capture_output=True,
        text=True,
        cwd=str(_ROOT),
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        print(out)
        raise RuntimeError(f"class_report zakonczyl sie kodem {proc.returncode}")
    print(out)
    return out


def _run_preview(version: str, conf: float, offset: int, limit: int, gt_context: bool) -> dict:
    out_dir = PREVIEW_OUT / version
    cmd = [
        sys.executable,
        str(_ROOT / "scripts" / "preview_batch.py"),
        "--version",
        version,
        "--conf",
        str(conf),
        "--offset",
        str(offset),
        "--limit",
        str(limit),
        "--out",
        str(out_dir),
    ]
    if gt_context:
        cmd.append("--gt-context")
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(_ROOT))
    print(proc.stdout or "")
    if proc.stderr:
        print(proc.stderr, file=sys.stderr)
    summary_path = out_dir / "summary.json"
    if summary_path.exists():
        return json.loads(summary_path.read_text(encoding="utf-8"))
    return {"error": proc.stderr or "brak summary.json", "returncode": proc.returncode}


def _append_log(entry: dict) -> None:
    MODELS.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _compare_previous(version: str, map50: float | None) -> dict:
    m = VERSION_RE.match(version)
    if not m or map50 is None:
        return {}
    prev = f"symbols_atomic_v{int(m.group(1)) - 1}"
    prev_summary = _read_summary(prev)
    if not prev_summary:
        return {"previous_version": prev, "previous_map50": None}
    prev_map = (prev_summary.get("metrics") or {}).get("map50")
    delta = None if prev_map is None else map50 - float(prev_map)
    return {
        "previous_version": prev,
        "previous_map50": prev_map,
        "map50_delta": delta,
        "improved": delta is not None and delta > 0,
    }


def run_cycle(
    name: str | None = None,
    min_count: int = 5,
    val_ratio: float = 0.2,
    batch: int | None = None,
    imgsz: int | None = None,
    epochs: int = 150,
    conf: float = 0.25,
    preview_offset: int = 20,
    preview_limit: int = 16,
    gt_context: bool = True,
    skip_train: bool = False,
) -> dict:
    started = datetime.now(timezone.utc)
    version = name or _next_version()
    print(f"=== train_cycle: {version} ===\n")

    class_report_text = _run_class_report(min_count)

    export_summary = export_dataset(val_ratio=val_ratio, min_count=min_count)
    manifest = _read_manifest() or {}
    print(
        f"Eksport: train={export_summary['train']} val={export_summary['val']} "
        f"klasy={export_summary['classes']}"
    )

    train_summary: dict | None = None
    if not skip_train:
        from train.train_symbols import train

        kw: dict = {"name": version, "epochs": epochs}
        if batch is not None:
            kw["batch"] = batch
        if imgsz is not None:
            kw["imgsz"] = imgsz
        train_summary = train(**kw)
        print(json.dumps(train_summary, ensure_ascii=False, indent=2))

        from train.export_onnx import export_onnx

        metrics = train_summary.get("metrics") if train_summary else None
        onnx_path = export_onnx(version=version, metrics=metrics, imgsz=imgsz)
        print(f"ONNX: {onnx_path}")
    else:
        print("[SKIP] trening i export_onnx pominiety (--skip-train)")

    preview = _run_preview(version, conf, preview_offset, preview_limit, gt_context)

    summary = _read_summary(version) if not skip_train else _read_summary(version)
    map50 = None
    if summary:
        map50 = (summary.get("metrics") or {}).get("map50")
    run_dir = Path((summary or {}).get("save_dir", DATA / "runs" / version))
    per_class_map = _parse_results_csv(run_dir) if run_dir.exists() else {}

    finished = datetime.now(timezone.utc)
    entry = {
        "timestamp": finished.isoformat(),
        "duration_sec": (finished - started).total_seconds(),
        "version": version,
        "min_count": min_count,
        "val_ratio": val_ratio,
        "fixed_val_pages": manifest.get("fixed_val_pages", []),
        "train_pages": manifest.get("train_pages", []),
        "val_pages": manifest.get("val_pages", []),
        "num_classes": export_summary.get("classes"),
        "map50": map50,
        "per_class_map50": per_class_map,
        "preview": preview,
        "skip_train": skip_train,
        "comparison": _compare_previous(version, map50) if map50 is not None else {},
        "class_report_excerpt": class_report_text[:2000],
    }
    _append_log(entry)

    print(f"\nLog: {LOG_PATH}")
    if entry.get("comparison"):
        c = entry["comparison"]
        if c.get("map50_delta") is not None:
            sign = "+" if c["map50_delta"] >= 0 else ""
            print(
                f"mAP50 vs {c['previous_version']}: {map50:.4f} "
                f"({sign}{c['map50_delta']:.4f})"
            )
    return entry


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--name", default=None, help="np. symbols_atomic_v2 (domyslnie auto N+1)")
    ap.add_argument("--min-count", type=int, default=5)
    ap.add_argument("--val-ratio", type=float, default=0.2)
    ap.add_argument("--batch", type=int, default=None)
    ap.add_argument("--imgsz", type=int, default=None)
    ap.add_argument("--epochs", type=int, default=150)
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--preview-offset", type=int, default=20)
    ap.add_argument("--preview-limit", type=int, default=16)
    ap.add_argument("--no-gt-context", action="store_true")
    ap.add_argument("--skip-train", action="store_true")
    args = ap.parse_args()

    try:
        run_cycle(
            name=args.name,
            min_count=args.min_count,
            val_ratio=args.val_ratio,
            batch=args.batch,
            imgsz=args.imgsz,
            epochs=args.epochs,
            conf=args.conf,
            preview_offset=args.preview_offset,
            preview_limit=args.preview_limit,
            gt_context=not args.no_gt_context,
            skip_train=args.skip_train,
        )
    except Exception as exc:
        print(f"[BLAD] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
