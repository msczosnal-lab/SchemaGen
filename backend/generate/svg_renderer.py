"""Auto-layout i renderer SVG."""

from __future__ import annotations

from pathlib import Path

import svgwrite

from backend.models.schema import SchemaModel
from backend.paths import BLOCKS


class SvgRenderer:
    """Renderuje SchemaModel do SVG z symbolami IEC."""

    def __init__(self, width: int = 800, height: int = 600) -> None:
        self._width = width
        self._height = height

    def _symbol_path(self, comp_type: str) -> str | None:
        sym = BLOCKS / "symbols" / f"{comp_type}.svg"
        if sym.exists():
            return str(sym)
        return None

    def render(self, model: SchemaModel, output_path: str) -> str:
        dwg = svgwrite.Drawing(output_path, size=(self._width, self._height))
        dwg.add(dwg.rect(insert=(0, 0), size=(self._width, self._height), fill="white"))

        for comp in model.components:
            if len(comp.bbox) >= 4:
                x, y, x2, y2 = comp.bbox[:4]
                w, h = max(x2 - x, 40), max(y2 - y, 40)
            else:
                x, y, w, h = 20.0, 20.0, 80.0, 60.0

            dwg.add(
                dwg.rect(
                    insert=(x, y),
                    size=(w, h),
                    fill="#f5f5f5",
                    stroke="#333",
                    rx=4,
                )
            )
            label = comp.tag or comp.id
            dwg.add(
                dwg.text(
                    label,
                    insert=(x + 4, y + h / 2),
                    fill="#111",
                    font_size="12px",
                    font_family="Arial",
                )
            )

        for i, conn in enumerate(model.connections):
            y_line = 30 + i * 8
            dwg.add(
                dwg.line(
                    start=(10, self._height - y_line),
                    end=(self._width - 10, self._height - y_line),
                    stroke="#0066cc",
                    stroke_width=1,
                )
            )
            dwg.add(
                dwg.text(
                    f"{conn.from_ref} -> {conn.to} ({conn.potential})",
                    insert=(12, self._height - y_line - 2),
                    fill="#0066cc",
                    font_size="9px",
                )
            )

        dwg.save()
        return output_path


def generate_schematic(
    config_path: str | None,
    output_svg: str,
) -> SchemaModel:
    from backend.generate.composer import BlockComposer

    model = BlockComposer().compose_from_config(config_path)
    SvgRenderer().render(model, output_svg)
    return model
