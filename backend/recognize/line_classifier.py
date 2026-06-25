# COWORK_TASK: sync/prompts/003-line-tracer-classifier.md

"""Klasyfikacja linii: rola (wire/bus/device_stroke/...) + grupa semantyczna z koloru.

Wejscie: segmenty geometryczne z LineTracer (z `detected_color`).
Wyjscie: list[GraphicLine] (role, semantic_group, color_ref, detected_color).
NIE tworzy Connection — to robi GraphBuilder (prompt 004). Linia != polaczenie.
"""

from __future__ import annotations

import math

from backend.colors.palette import ColorPalette, load_palette
from backend.models.schema import GraphicLine
from backend.recognize.line_tracer import LineSegment


CONNECTION_ROLES = frozenset({"wire", "bus"})

# Geometria: linia uznana za "dluga" (kandydat na szyne) gdy >= tego progu (px),
# o ile jest blisko osi (pozioma/pionowa). Mozna nadpisac przez image_size.
BUS_MIN_LENGTH = 400.0
AXIS_TOL_DEG = 8.0


class LineClassifier:
    def __init__(self, palette: ColorPalette | None = None) -> None:
        self._palette = palette or load_palette()

    def classify(
        self,
        segments: list[LineSegment],
        *,
        image_size: tuple[int, int] | None = None,
        bus_min_length: float | None = None,
    ) -> list[GraphicLine]:
        bus_len = bus_min_length if bus_min_length is not None else self._bus_threshold(image_size)
        out: list[GraphicLine] = []
        for i, seg in enumerate(segments):
            group = self._palette.match_color(seg.detected_color) if seg.detected_color else None
            role = self._role_for(seg, group, bus_len)
            color_ref = ""
            if group:
                color_ref = str(self._palette.groups.get(group, {}).get("stroke", "")) or ""
            if not color_ref:
                color_ref = seg.detected_color
            style = "dashed" if role == "dash" else "solid"
            out.append(
                GraphicLine(
                    id=f"gl_{i}",
                    points=[[seg.x1, seg.y1], [seg.x2, seg.y2]],
                    role=role,
                    style=style,
                    semantic_group=group or "",
                    color_ref=color_ref,
                    detected_color=seg.detected_color,
                )
            )
        return out

    @staticmethod
    def _bus_threshold(image_size: tuple[int, int] | None) -> float:
        if not image_size:
            return BUS_MIN_LENGTH
        w, h = image_size
        # Szyna zwykle obejmuje sporo szerokosci/wysokosci strony.
        return 0.45 * max(w, h)

    def _role_for(self, seg: LineSegment, group: str | None, bus_len: float) -> str:
        # 1) Wskazowka z grupy koloru — jesli grupa definiuje jednoznaczna role.
        if group:
            roles = self._palette.groups.get(group, {}).get("roles", [])
            if len(roles) == 1:
                return str(roles[0])
            # grupa typu falownik (fill, applies_to_types) -> obrys urzadzenia
            grp = self._palette.groups.get(group, {})
            if grp.get("applies_to_types") and not roles:
                return "device_stroke"

        # 2) Geometria: dluga linia w osi -> szyna (bus).
        angle = seg.angle_deg
        axis_aligned = (
            angle <= AXIS_TOL_DEG
            or angle >= 180.0 - AXIS_TOL_DEG
            or abs(angle - 90.0) <= AXIS_TOL_DEG
        )
        if axis_aligned and seg.length >= bus_len:
            return "bus"

        # 3) Domyslnie kabel.
        return "wire"

    @staticmethod
    def is_connection_candidate(line: GraphicLine) -> bool:
        return line.role in CONNECTION_ROLES
