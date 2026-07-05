"""Testy remapu ID symboli/terminali w diff_connections (prompt 022, krok 0)."""

from __future__ import annotations

from backend.models.schema import Component, Connection, SchemaModel, Terminal
from backend.validate.diff_metrics import diff_connections, pair_components


def test_pair_components_greedy_iou() -> None:
    gt = SchemaModel(
        components=[
            Component(id="g1", type="relay", bbox=[10, 10, 50, 50]),
            Component(id="g2", type="fuse", bbox=[100, 100, 140, 140]),
        ]
    )
    rt = SchemaModel(
        components=[
            Component(id="r1", type="relay", bbox=[12, 12, 52, 52]),
            Component(id="r2", type="fuse", bbox=[102, 102, 142, 142]),
            Component(id="r3", type="relay", bbox=[200, 200, 240, 240]),
        ]
    )
    p = pair_components(gt, rt)
    assert p["rt_to_gt"] == {"r1": "g1", "r2": "g2"}
    assert set(p["only_runtime"]) == {"r3"}


def test_diff_connections_id_remap_f1_perfect() -> None:
    """Te same polaczenia przy roznych id symboli i terminali -> F1=1.0."""
    gt = SchemaModel(
        components=[
            Component(
                id="sym_k1",
                type="relay",
                bbox=[100, 100, 200, 200],
                terminals=[Terminal(id="1", x=0.0, y=0.5)],
            ),
            Component(
                id="sym_k2",
                type="fuse",
                bbox=[300, 100, 400, 200],
                terminals=[Terminal(id="3", x=1.0, y=0.5)],
            ),
        ],
        connections=[
            Connection.model_validate(
                {"from": "sym_k1:1", "to": "sym_k2:3", "kind": "power"}
            ),
        ],
    )
    rt = SchemaModel(
        components=[
            Component(
                id="sym_0",
                type="relay",
                bbox=[102, 102, 202, 202],
                terminals=[Terminal(id="T1", x=0.0, y=0.5)],
            ),
            Component(
                id="sym_1",
                type="fuse",
                bbox=[302, 102, 402, 202],
                terminals=[Terminal(id="T3", x=1.0, y=0.5)],
            ),
        ],
        connections=[
            Connection.model_validate(
                {"from": "sym_0:T1", "to": "sym_1:T3", "kind": "power"}
            ),
        ],
    )
    d = diff_connections(gt, rt, terminal_tol=20.0)
    assert d["match"] == 1
    assert d["f1"] == 1.0
    assert d["only_gt"] == []
    assert d["only_runtime"] == []


def test_diff_connections_unpaired_component_only_runtime() -> None:
    gt = SchemaModel(
        connections=[
            Connection.model_validate({"from": "g1:1", "to": "g2:2", "kind": "power"}),
        ]
    )
    rt = SchemaModel(
        components=[
            Component(id="sym_0", type="relay", bbox=[10, 10, 50, 50]),
        ],
        connections=[
            Connection.model_validate(
                {"from": "sym_0:1", "to": "sym_99:2", "kind": "power"}
            ),
        ],
    )
    d = diff_connections(gt, rt)
    assert d["match"] == 0
    assert len(d["only_runtime"]) == 1
