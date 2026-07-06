"""Testy kompilacji SchematicGraph → SchemaModel."""

from __future__ import annotations

from backend.models.schema import Terminal
from backend.models.schematic_graph import GraphLine, GraphSymbol, SchematicGraph
from labeler.graph_compile import graph_to_schema


def _relay_fuse_graph(*, vertices: list | None = None) -> SchematicGraph:
    line_data: dict = {
        "id": "L1",
        "from": "k1:1",
        "to": "f1:2",
        "kind": "power",
    }
    if vertices is not None:
        line_data["vertices"] = vertices
    return SchematicGraph(
        page_id="t",
        image_width=1000,
        image_height=800,
        symbols=[
            GraphSymbol(
                id="k1",
                type="cewka_przekaznika",
                tag="-K1",
                bbox=[100, 100, 200, 200],
                terminals=[Terminal(id="1", x=1.0, y=0.5)],
            ),
            GraphSymbol(
                id="f1",
                type="bezpiecznik",
                tag="-F1",
                bbox=[400, 100, 500, 200],
                terminals=[Terminal(id="2", x=0.0, y=0.5)],
            ),
        ],
        lines=[GraphLine.model_validate(line_data)],
    )


def test_graph_compile_components_and_connection() -> None:
    schema = graph_to_schema(_relay_fuse_graph(vertices=[[200, 150], [400, 150]]))
    assert len(schema.components) == 2
    assert schema.components[0].id == "k1"
    assert schema.components[0].terminals[0].x == 1.0
    assert len(schema.connections) == 1
    assert schema.connections[0].from_ref == "k1:1"
    assert schema.connections[0].to == "f1:2"
    assert schema.connections[0].kind == "power"
    assert schema.connections[0].potential == ""


def test_graph_compile_auto_route_L_shape() -> None:
    schema = graph_to_schema(_relay_fuse_graph())
    assert len(schema.graphic_lines) == 1
    pts = schema.graphic_lines[0].points
    assert pts[0] == [200.0, 150.0]
    assert pts[-1] == [400.0, 150.0]
    assert len(pts) == 3  # L: poziomo-pionowo lub odwrotnie
    assert schema.graphic_lines[0].role == "wire"


def test_graph_compile_link_bus_potential() -> None:
    """Trzy złączki połączone link → wspólny potential na torze szyny."""
    g = SchematicGraph(
        page_id="bus",
        image_width=2000,
        image_height=1500,
        symbols=[
            GraphSymbol(
                id="z1",
                type="zlaczka",
                tag="-X1",
                bbox=[100, 100, 150, 180],
                terminals=[
                    Terminal(id="L", x=0.0, y=0.5),
                    Terminal(id="R", x=1.0, y=0.5),
                ],
            ),
            GraphSymbol(
                id="z2",
                type="zlaczka",
                bbox=[200, 100, 250, 180],
                terminals=[
                    Terminal(id="L", x=0.0, y=0.5),
                    Terminal(id="R", x=1.0, y=0.5),
                ],
            ),
            GraphSymbol(
                id="z3",
                type="zlaczka",
                bbox=[300, 100, 350, 180],
                terminals=[
                    Terminal(id="L", x=0.0, y=0.5),
                    Terminal(id="R", x=1.0, y=0.5),
                ],
            ),
        ],
        lines=[
            GraphLine.model_validate(
                {"id": "L1", "from": "z1:R", "to": "z2:L", "kind": "link"}
            ),
            GraphLine.model_validate(
                {"id": "L2", "from": "z2:R", "to": "z3:L", "kind": "link"}
            ),
            GraphLine.model_validate(
                {
                    "id": "L3",
                    "from": "k1:1",
                    "to": "z1:T",
                    "kind": "power",
                    "vertices": [[50, 140], [125, 140]],
                }
            ),
        ],
    )
    # dodaj symbol k1 z terminalem T na z1 (power od urządzenia)
    g.symbols.append(
        GraphSymbol(
            id="k1",
            type="cewka",
            bbox=[0, 100, 50, 180],
            terminals=[Terminal(id="1", x=1.0, y=0.5)],
        )
    )
    g.symbols[0].terminals.append(Terminal(id="T", x=0.5, y=0.0))

    schema = graph_to_schema(g)
    link_conns = [c for c in schema.connections if c.kind == "link"]
    assert len(link_conns) == 2
    assert len(schema.potentials) == 1
    assert schema.potentials[0] == "-X1"  # tag skrajnej złączki
    assert all(c.potential == "-X1" for c in link_conns)


def test_graph_compile_internal_mostek_no_potential() -> None:
    """Mostek left↔right w jednej złączce — link, bez potential (1 symbol)."""
    g = SchematicGraph(
        page_id="t",
        image_width=500,
        image_height=500,
        symbols=[
            GraphSymbol(
                id="z1",
                type="zlaczka",
                bbox=[100, 100, 150, 180],
                terminals=[
                    Terminal(id="L", x=0.0, y=0.5),
                    Terminal(id="R", x=1.0, y=0.5),
                ],
            ),
        ],
        lines=[
            GraphLine.model_validate(
                {"id": "L1", "from": "z1:L", "to": "z1:R", "kind": "link"}
            ),
        ],
    )
    schema = graph_to_schema(g)
    assert schema.connections[0].kind == "link"
    assert schema.potentials == []
    assert schema.connections[0].potential == ""


def test_graph_compile_meta_source() -> None:
    schema = graph_to_schema(_relay_fuse_graph())
    assert schema.meta.source == "t"
