"""Testy RelationResolver — mock tekstow/linii (bez GPU/OCR)."""

from __future__ import annotations

import json
from pathlib import Path

from backend.models.schema import Component, Connection, GraphicLine
from backend.recognize.ocr_engine import TextDetection
from backend.recognize.relation_resolver import RelationResolver

_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "relations_minimal.json"


def _load_fixture() -> dict:
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


def _components_from_fixture(data: dict) -> list[Component]:
    return [Component.model_validate(c) for c in data["components"]]


def _texts_from_fixture(data: dict) -> list[TextDetection]:
    return [TextDetection(**t) for t in data["texts"]]


def test_proximity_tag_assigned_without_overlap() -> None:
    relay = Component(
        id="sym_r", type="relay", bbox=[300, 40, 360, 100], source="yolo"
    )
    texts = [TextDetection(text="-K1", bbox=[365, 45, 395, 60], confidence=0.95)]
    resolver = RelationResolver()
    _, _, _, _, annotations = resolver.resolve(
        [relay], texts, [], [], [], image_size=(1000, 1000)
    )
    assert relay.tag == "-K1"
    assert "-K1" not in annotations


def test_table_text_goes_to_annotations_only() -> None:
    relay = Component(
        id="sym_r", type="relay", bbox=[300, 40, 360, 100], source="yolo"
    )
    texts = [
        TextDetection(text="TABELKA", bbox=[10, 900, 80, 920], confidence=0.85)
    ]
    resolver = RelationResolver()
    resolver.resolve([relay], texts, [], [], [], image_size=(1000, 1000))
    assert relay.tag == ""
    assert "TABELKA" in annotations if False else True  # placeholder
    _, _, _, _, annotations = resolver.resolve(
        [relay], texts, [], [], [], image_size=(1000, 1000)
    )
    assert relay.tag == ""
    assert "TABELKA" in annotations


def test_merge_potential_arrows_same_tag() -> None:
    a_in = Component(
        id="sym_in",
        type="strzalka_potencjalu_wejsciowa",
        bbox=[100, 50, 130, 80],
        tag="24V",
        source="yolo",
    )
    a_out = Component(
        id="sym_out",
        type="strzalka_potencjalu_wyjsciowa",
        bbox=[200, 50, 230, 80],
        tag="24V",
        source="yolo",
    )
    relay = Component(
        id="sym_relay", type="relay", bbox=[300, 40, 360, 100], source="yolo"
    )
    conns = [
        Connection.model_validate({"from": "sym_in", "to": "sym_out", "kind": "power"}),
        Connection.model_validate(
            {"from": "sym_out", "to": "sym_relay", "kind": "power"}
        ),
    ]
    resolver = RelationResolver()
    _, out_conns, potentials, _, _ = resolver.resolve(
        [a_in, a_out, relay], [], conns, [], [], image_size=(1000, 1000)
    )
    pairs = {(c.from_ref.split(":")[0], c.to.split(":")[0]) for c in out_conns}
    assert ("sym_in", "sym_out") not in pairs
    assert "pot_24V" in potentials
    relay_conn = next(c for c in out_conns if "sym_relay" in (c.from_ref, c.to))
    assert relay_conn.potential == "pot_24V"


def test_wire_label_sets_connection_potential() -> None:
    sym_a = Component(id="sym_a", type="fuse", bbox=[20, 40, 80, 100], source="yolo")
    sym_b = Component(
        id="sym_b", type="inverter", bbox=[120, 30, 220, 130], source="yolo"
    )
    wire = GraphicLine(id="gl_0", points=[[80, 70], [120, 70]], role="wire")
    texts = [TextDetection(text="W1", bbox=[95, 55, 115, 70], confidence=0.9)]
    conns = [
        Connection.model_validate({"from": "sym_a", "to": "sym_b", "kind": "power"})
    ]
    resolver = RelationResolver()
    _, out_conns, _, _, _ = resolver.resolve(
        [sym_a, sym_b], texts, conns, [wire], [], image_size=(1000, 1000)
    )
    assert out_conns[0].potential == "W1"


def test_runtime_context_zlaczka_in_row() -> None:
    z1 = Component(
        id="z1", type="zlaczka", bbox=[50, 200, 70, 220], source="yolo"
    )
    z2 = Component(
        id="z2", type="zlaczka", bbox=[90, 202, 110, 222], source="yolo"
    )
    lst = Component(
        id="lst",
        type="listwa_zlaczek",
        bbox=[40, 195, 120, 205],
        source="yolo",
    )
    resolver = RelationResolver()
    _, _, _, ctx, _ = resolver.resolve([z1, z2, lst], [], [], [], [])
    roles = {a.bbox_id: a.role for a in ctx}
    assert roles.get("z1") == "zlaczka"
    assert roles.get("z2") == "zlaczka"


def test_fixture_minimal_loads_and_resolves() -> None:
    data = _load_fixture()
    comps = _components_from_fixture(data)
    texts = _texts_from_fixture(data)
    lines = [GraphicLine.model_validate(ln) for ln in data["graphic_lines"]]
    conns = [Connection.model_validate(c) for c in data["connections"]]
    size = tuple(data["image_size"])

    resolver = RelationResolver()
    comps, out_conns, potentials, ctx, annotations = resolver.resolve(
        comps, texts, conns, lines, list(data["potentials"]), image_size=size
    )

    relay = next(c for c in comps if c.id == "sym_relay")
    assert relay.tag == "-K1"
    assert "TABELKA" in annotations
    assert "pot_24V" in potentials
    assert not any(
        c.from_ref.split(":")[0] == "sym_arrow_in"
        and c.to.split(":")[0] == "sym_arrow_out"
        for c in out_conns
    )
    assert len(ctx) >= 2
