"""IO wzorcow terminali per klasa (config/terminal-patterns.yaml)."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

from backend.paths import CONFIG

TERMINAL_PATTERNS_PATH = CONFIG / "terminal-patterns.yaml"
_FRAC_CLUSTER_TOL = 0.12


def load_patterns(path: Path | None = None) -> dict[str, dict]:
    p = path or TERMINAL_PATTERNS_PATH
    defaults: dict = {"version": 1, "classes": {}}
    if not p.exists():
        return defaults
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or defaults
    classes = data.get("classes") or {}
    if not isinstance(classes, dict):
        classes = {}
    return {"version": int(data.get("version", 1)), "classes": dict(classes)}


def save_class_pattern(
    class_name: str,
    pattern: dict[str, Any],
    path: Path | None = None,
) -> dict[str, Any]:
    """Zapisz/ nadpisz wzorzec klasy w YAML."""
    p = path or TERMINAL_PATTERNS_PATH
    data = load_patterns(p)
    classes = data.setdefault("classes", {})
    classes[class_name] = pattern
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    try:
        from backend.runtime_config import terminal_patterns

        terminal_patterns.cache_clear()
    except Exception:
        pass
    return pattern


def rel_to_edge_frac(x: float, y: float) -> tuple[str, float]:
    """Pozycja wzgledna terminala -> (krawedz, frac wzdluz krawedzi)."""
    x = max(0.0, min(1.0, x))
    y = max(0.0, min(1.0, y))
    dist = {"left": x, "right": 1.0 - x, "top": y, "bottom": 1.0 - y}
    edge = min(dist, key=dist.get)
    frac = y if edge in ("left", "right") else x
    return edge, round(frac, 4)


def build_pattern_from_bboxes(
    bboxes: list[dict],
    *,
    method: str = "line-contact",
    frac_tol: float = 0.15,
    required_ratio: float = 0.5,
) -> dict[str, Any]:
    """Uśrednij terminale z wielu bboxow tej samej klasy -> pattern YAML."""
    by_edge: dict[str, list[float]] = defaultdict(list)
    n_samples = 0
    for b in bboxes:
        terms = b.get("terminals") or []
        if not terms:
            continue
        n_samples += 1
        for t in terms:
            edge, frac = rel_to_edge_frac(float(t["x"]), float(t["y"]))
            by_edge[edge].append(frac)

    expected: list[dict[str, Any]] = []
    for edge in ("left", "right", "top", "bottom"):
        fracs = sorted(by_edge.get(edge, []))
        if not fracs:
            continue
        for cluster in _cluster_1d(fracs, _FRAC_CLUSTER_TOL):
            avg = round(sum(cluster) / len(cluster), 4)
            expected.append(
                {
                    "edge": edge,
                    "frac": avg,
                    "required": len(cluster) >= max(1, n_samples * required_ratio),
                }
            )

    return {
        "method": method,
        "expected": expected,
        "frac_tol": frac_tol,
    }


def _cluster_1d(values: list[float], tol: float) -> list[list[float]]:
    if not values:
        return []
    clusters: list[list[float]] = [[values[0]]]
    for v in values[1:]:
        if v - clusters[-1][-1] <= tol:
            clusters[-1].append(v)
        else:
            clusters.append([v])
    return clusters
