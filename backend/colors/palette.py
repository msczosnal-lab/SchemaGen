"""Dopasowanie kolorow semantycznych z config/semantic-colors.yaml."""

from __future__ import annotations

import colorsys
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from backend.paths import CONFIG

DEFAULT_PALETTE = CONFIG / "semantic-colors.yaml"


@dataclass(frozen=True)
class ResolvedStyle:
    stroke: str
    fill: str | None
    style: str


@dataclass
class ColorPalette:
    version: int
    groups: dict[str, dict[str, Any]]
    text_inherit: str
    tolerance: dict[str, float]

    @classmethod
    def load(cls, path: Path | None = None) -> ColorPalette:
        palette_path = path or DEFAULT_PALETTE
        raw = yaml.safe_load(palette_path.read_text(encoding="utf-8"))
        return cls(
            version=int(raw.get("version", 1)),
            groups=raw.get("groups", {}),
            text_inherit=str(raw.get("text", {}).get("inherit_from", "component")),
            tolerance=raw.get("tolerance", {}),
        )

    def resolve_stroke(self, semantic_group: str, role: str = "wire") -> ResolvedStyle:
        group = self.groups.get(semantic_group, {})
        stroke = str(group.get("stroke", "#333333"))
        fill = group.get("fill")
        style = str(group.get("style", "solid"))
        roles = group.get("roles", [])
        if roles and role not in roles:
            style = "solid"
        return ResolvedStyle(stroke=stroke, fill=str(fill) if fill else None, style=style)

    def group_for_component_type(self, component_type: str) -> str | None:
        for name, group in self.groups.items():
            types = group.get("applies_to_types", [])
            if component_type in types:
                return name
        return None

    def match_color(self, hex_color: str) -> str | None:
        target = _parse_hex(hex_color)
        if target is None:
            return None
        hue_deg = float(self.tolerance.get("hue_deg", 12))
        sat_min = float(self.tolerance.get("sat_min", 0.15))
        val_delta = float(self.tolerance.get("value_delta", 0.12))
        # Tie-break deterministyczny: (dystans, specyficznosc, nazwa) — nie kolejnosc dict.
        # specyficznosc = liczba rol (mniej = bardziej specyficzna); przy remisie odcienia
        # grupa 1-rolowa (np. pe_wire) wygrywa z wielorolowa (enclosure). Findings 019 H4.
        best: tuple[float, int, str] | None = None
        for name, group in self.groups.items():
            roles = group.get("roles") or []
            rank = len(roles) if roles else 1
            for key in ("stroke", "fill"):
                ref = group.get(key)
                if not ref:
                    continue
                parsed = _parse_hex(str(ref))
                if parsed is None:
                    continue
                dist = _color_distance(target, parsed, hue_deg, sat_min, val_delta)
                cand = (dist, rank, name)
                if best is None or cand < best:
                    best = cand
        if best is None:
            return None
        threshold = hue_deg / 180.0 + val_delta + 0.05
        return best[2] if best[0] <= threshold else None


def load_palette(path: Path | None = None) -> ColorPalette:
    return ColorPalette.load(path)


def _parse_hex(value: str) -> tuple[float, float, float] | None:
    text = value.strip().lstrip("#")
    if len(text) == 3:
        text = "".join(ch * 2 for ch in text)
    if len(text) != 6:
        return None
    try:
        r = int(text[0:2], 16) / 255.0
        g = int(text[2:4], 16) / 255.0
        b = int(text[4:6], 16) / 255.0
    except ValueError:
        return None
    return colorsys.rgb_to_hsv(r, g, b)


def _color_distance(
    a: tuple[float, float, float],
    b: tuple[float, float, float],
    hue_deg: float,
    sat_min: float,
    val_delta: float,
) -> float:
    ah, as_, av = a
    bh, bs, bv = b
    if as_ < sat_min and bs < sat_min:
        return abs(av - bv)
    hue_diff = abs(ah - bh)
    hue_diff = min(hue_diff, 1.0 - hue_diff)
    hue_norm = hue_diff / max(hue_deg / 360.0, 1e-6)
    sat_norm = abs(as_ - bs)
    val_norm = abs(av - bv) / max(val_delta, 1e-6)
    return math.sqrt(hue_norm**2 + sat_norm**2 + val_norm**2)
