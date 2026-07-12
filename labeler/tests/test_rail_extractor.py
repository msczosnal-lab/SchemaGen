"""Testy RailExtractor v0."""

from __future__ import annotations

from backend.models.schema import Component, Connection, SchemaMeta, SchemaModel, Terminal
from labeler.rail_extractor import expand_rail_connections


def _star_net() -> SchemaModel:
    z1 = Component(
        id="z1",
        type="zlaczka",
        bbox=[0, 100, 20, 120],
        terminals=[Terminal(id="L", x=0, y=0.5), Terminal(id="R", x=1, y=0.5)],
    )
    z2 = Component(
        id="z2",
        type="zlaczka",
        bbox=[40, 100, 60, 120],
        terminals=[Terminal(id="L", x=0, y=0.5), Terminal(id="R", x=1, y=0.5)],
    )
    z3 = Component(
        id="z3",
        type="zlaczka",
        bbox=[80, 100, 100, 120],
        terminals=[Terminal(id="L", x=0, y=0.5), Terminal(id="R", x=1, y=0.5)],
    )
    pot = "net_0"
    return SchemaModel(
        meta=SchemaMeta(source="t"),
        components=[z1, z2, z3],
        connections=[
            Connection.model_validate({"from": "z2:R", "to": "z1:L", "kind": "link", "potential": pot}),
            Connection.model_validate({"from": "z2:R", "to": "z3:L", "kind": "link", "potential": pot}),
            Connection.model_validate({"from": "z1:R", "to": "z2:L", "kind": "link", "potential": pot}),
        ],
    )


def test_expand_rail_chain_replaces_star() -> None:
    schema = _star_net()
    out = expand_rail_connections(schema)
    link_pairs = {
        tuple(sorted([str(c.from_ref), str(c.to)]))
        for c in out
        if c.kind == "link"
    }
    assert ("z1:R", "z2:L") in link_pairs or ("z2:L", "z1:R") in link_pairs
    assert ("z2:R", "z3:L") in link_pairs or ("z3:L", "z2:R") in link_pairs
    assert len(link_pairs) >= 2
