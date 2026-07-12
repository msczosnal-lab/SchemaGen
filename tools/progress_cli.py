"""Wspolny progres etapowy dla CLI auto-draft / auto-loop."""

from __future__ import annotations

import time
from typing import Callable, Optional


def make_progress(label: str, quiet: bool = False) -> Optional[Callable[[int, int, str], None]]:
    """Callback etapowy: [p028] [###---] 3/6 trasowanie... (+4.1s) — na zywo, z flush.

    Zwraca None gdy quiet (brak progresu, np. tryb --json).
    """
    if quiet:
        return None
    state = {"last": time.monotonic()}

    def _cb(step: int, total: int, name: str) -> None:
        now = time.monotonic()
        dt = now - state["last"]
        state["last"] = now
        step = max(0, min(step, total))
        bar = "#" * step + "-" * (total - step)
        print(f"  [{label}] [{bar}] {step}/{total} {name} (+{dt:.1f}s)", flush=True)

    return _cb
