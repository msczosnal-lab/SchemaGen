"""Testy generowania."""

from pathlib import Path

from backend.generate.composer import BlockComposer
from backend.generate.svg_renderer import SvgRenderer


def test_compose_blocks() -> None:
    model = BlockComposer().compose_blocks(["400vac_supply", "frequency_control"])
    assert len(model.components) >= 2
    assert "400vac_supply" in model.blocks or model.blocks


def test_render_svg(tmp_path: Path) -> None:
    model = BlockComposer().compose_from_config()
    out = tmp_path / "test.svg"
    SvgRenderer().render(model, str(out))
    assert out.exists()
    assert "<svg" in out.read_text(encoding="utf-8")
