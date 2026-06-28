"""Testy net-buildera (Warstwa 1): scalanie segmentow wire/bus w sieci -> Connection."""

from backend.models.schema import Component, GraphicLine
from backend.recognize.net_builder import build_connections


def _comp(cid: str, bbox) -> Component:
    return Component(id=cid, type="x", bbox=bbox, source="yolo")


def _wire(pts, role="wire", group="") -> GraphicLine:
    return GraphicLine(id="gl", points=pts, role=role, semantic_group=group)


# Symbole: A po lewej, B po prawej, C dalej
A = _comp("A", [0, 40, 40, 80])      # prawa krawedz x=40
B = _comp("B", [200, 40, 240, 80])   # lewa krawedz x=200
C = _comp("C", [400, 40, 440, 80])   # lewa krawedz x=400


def test_two_segments_merge_into_one_connection() -> None:
    # przewod A->B pofragmentowany na 2 kawalki stykajace sie w (120,60)
    s1 = _wire([[40, 60], [120, 60]])
    s2 = _wire([[120, 60], [200, 60]])
    conns, pots = build_connections([s1, s2], [A, B], join_tol=10, terminal_tol=10)
    assert len(conns) == 1
    assert {conns[0].from_ref, conns[0].to} == {"A", "B"}
    assert pots == []


def test_bend_90_degrees_is_one_net() -> None:
    # zalamanie pod katem prostym: A -> w prawo -> w dol/gore, koniec przy B
    s1 = _wire([[40, 60], [120, 60]])
    s2 = _wire([[120, 60], [120, 200]])  # zalamanie w (120,60)
    conns, _ = build_connections([s1, s2], [A, B], join_tol=10, terminal_tol=10)
    # B nie jest dotkniety (drugi segment idzie w dol) -> brak 2 symboli -> brak Connection
    assert conns == []


def test_T_junction_three_symbols_share_potential() -> None:
    # szyna A-B (pozioma) + odczep w polowie do C -> net z 3 symbolami
    bus = _wire([[40, 60], [200, 60]], role="bus")
    tap = _wire([[120, 60], [120, 60], [400, 60]])  # koniec (120,60) na szynie, drugi przy C
    conns, pots = build_connections([bus, tap], [A, B, C], join_tol=10, terminal_tol=10)
    ids = {frozenset((c.from_ref, c.to)) for c in conns}
    assert {"A", "B", "C"} == {x for fs in ids for x in fs}
    assert len(pots) == 1               # wspolny potential dla >2 symboli
    assert all(c.potential == pots[0] for c in conns)


def test_crossing_without_endpoint_not_joined() -> None:
    # dwie linie krzyzujace sie w polowie (zaden koniec w punkcie skrzyzowania) -> 2 nety
    horiz = _wire([[40, 60], [200, 60]])     # A..B
    vert = _wire([[120, 0], [120, 300]])     # przecina w (120,60), ale konce daleko
    conns, _ = build_connections([horiz, vert], [A, B], join_tol=10, terminal_tol=10)
    # tylko net poziomy laczy A-B; pionowy nie dotyka A/B koncami
    assert len(conns) == 1
    assert {conns[0].from_ref, conns[0].to} == {"A", "B"}


def test_dangling_net_no_connection() -> None:
    wire = _wire([[40, 60], [120, 60]])  # tylko A dotkniety, drugi koniec dynda
    conns, _ = build_connections([wire], [A, B], join_tol=10, terminal_tol=10)
    assert conns == []


def test_pe_group_sets_pe_kind() -> None:
    wire = _wire([[40, 60], [200, 60]], group="pe_wire")
    conns, _ = build_connections([wire], [A, B], join_tol=10, terminal_tol=10)
    assert conns[0].kind == "pe"


def test_device_stroke_not_candidate() -> None:
    stroke = _wire([[40, 60], [200, 60]], role="device_stroke")
    conns, _ = build_connections([stroke], [A, B], join_tol=10, terminal_tol=10)
    assert conns == []
