"""Baseline eval GT v2 (p028–p033) — runtime vs skompilowane GT."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ["p028", "p029", "p030", "p033"]


def main() -> int:
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "eval_val_pages.py"),
        "--pages",
        *PAGES,
        "--json",
    ]
    return subprocess.call(cmd, cwd=str(ROOT))


if __name__ == "__main__":
    raise SystemExit(main())
