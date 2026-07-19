"""Testy sita linii — obramowki bbox -> frame, tekst -> other, przewody zostaja."""

from backend.models.schema import Component, GraphicLine, Terminal
from backend.recognize.line_classifier import LineClassifier
from backend.recognize.line_sieve import (
    apply_sieve,
    apply_terminal_gate,
    merge_collinear_wires,
    recover_terminal_bridges,
    recover_terminal_gated_wires,
)

# Symbol: bbox [100,100,300,200] (x1,y1,x2,y2)
COMP = Component(id="sym_0", type="relay", bbox=[100, 100, 300, 200], source="yolo")


def _wire(pts) -> GraphicLine:
    return GraphicLine(id="gl", points=pts, role="wire")


def test_top_edge_demoted_to_frame() -> None:
    # linia wzdluz gornej krawedzi (y=100, x 100..300) = obramowka
    edge = _wire([[100, 100], [300, 100]])
    [out] = apply_sieve([edge], [COMP], [], edge_tol=6.0)
    assert out.role == "frame"
    assert not LineClassifier.is_connection_candidate(out)


def test_left_edge_demoted_to_frame() -> None:
    edge = _wire([[100, 100], [100, 200]])  # lewy bok (x=100, y 100..200)
    [out] = apply_sieve([edge], [COMP], [], edge_tol=6.0)
    assert out.role == "frame"


def test_perpendicular_wire_touching_edge_stays_wire() -> None:
    # przewod dotyka prawej krawedzi (x=300) punktowo i idzie w prawo (poziom)
    wire = _wire([[300, 150], [400, 150]])
    [out] = apply_sieve([wire], [COMP], [], edge_tol=6.0)
    assert out.role == "wire"
    assert LineClassifier.is_connection_candidate(out)


def test_wire_far_from_box_stays_wire() -> None:
    wire = _wire([[500, 500], [600, 500]])
    [out] = apply_sieve([wire], [COMP], [], edge_tol=6.0)
    assert out.role == "wire"


def test_short_segment_in_text_bbox_demoted_other() -> None:
    # krotki segment wewnatrz bbox tekstu OCR
    seg = _wire([[410, 405], [430, 405]])
    text_bbox = [400, 400, 460, 420]
    [out] = apply_sieve([seg], [COMP], [text_bbox], edge_tol=6.0)
    assert out.role == "other"
    assert not LineClassifier.is_connection_candidate(out)


def test_non_candidate_untouched() -> None:
    stroke = GraphicLine(id="gl", points=[[100, 100], [300, 100]], role="device_stroke")
    [out] = apply_sieve([stroke], [COMP], [], edge_tol=6.0)
    assert out.role == "device_stroke"  # nie ruszamy nie-kandydatow


def test_long_wire_along_edge_demoted() -> None:
    # dluga wire wzdluz dolnego boku bbox = obramowka (ADR: bus wycofane, dluga linia = wire)
    wire = GraphicLine(id="gl", points=[[100, 200], [300, 200]], role="wire")
    [out] = apply_sieve([wire], [COMP], [], edge_tol=6.0)
    assert out.role == "frame"


def test_line_inside_component_demoted_other() -> None:
    # tabelka wewnatrz terminala — cala w bbox [100,100,300,200]
    inner = _wire([[150, 150], [250, 150]])
    [out] = apply_sieve([inner], [COMP], [], edge_tol=6.0)
    assert out.role == "other"
    assert not LineClassifier.is_connection_candidate(out)


def test_wire_crossing_boundary_stays_wire() -> None:
    # przewod z wnetrza na zewnatrz (wychodzi poza prawy bok) -> zostaje wire
    crossing = _wire([[250, 150], [400, 150]])
    [out] = apply_sieve([crossing], [COMP], [], edge_tol=6.0)
    assert out.role == "wire"


# --- mostki w listwie: konce w 2 terminalach tego samego komponentu zostaja wire ---
def _strip() -> Component:
    # listwa bbox [100,100,300,200]; t1 abs(140,150) rel(0.2,0.5), t2 abs(260,150) rel(0.8,0.5)
    return Component(
        id="X1", type="terminal_block", bbox=[100, 100, 300, 200], source="yolo",
        terminals=[Terminal(id="1", x=0.2, y=0.5), Terminal(id="2", x=0.8, y=0.5)],
    )


def test_bridge_between_two_terminals_stays_wire() -> None:
    # mostek w calosci w bbox, konce w t1 i t2 -> NIE demotowany (zostaje kandydatem)
    bridge = _wire([[140, 150], [260, 150]])
    [out] = apply_sieve([bridge], [_strip()], [], edge_tol=6.0, bridge_tol=8.0)
    assert out.role == "wire"
    assert LineClassifier.is_connection_candidate(out)


def test_inside_line_not_hitting_two_terminals_demoted() -> None:
    # linia wewnatrz, ale konce nie trafiaja w 2 rozne terminale -> other
    inner = _wire([[150, 130], [180, 130]])
    [out] = apply_sieve([inner], [_strip()], [], edge_tol=6.0, bridge_tol=8.0)
    assert out.role == "other"


def test_recover_terminal_bridges_promotes_other_back_to_wire() -> None:
    # runtime: sito zdemotowalo mostek do 'other' zanim terminale powstaly; odzysk -> wire
    demoted = GraphicLine(id="gl", points=[[140, 150], [260, 150]], role="other")
    [out] = recover_terminal_bridges([demoted], [_strip()], bridge_tol=8.0)
    assert out.role == "wire"
    assert LineClassifier.is_connection_candidate(out)


def test_recover_leaves_genuine_other_untouched() -> None:
    # 'other' niebędący mostkiem (brak trafienia w 2 terminale) zostaje other
    demoted = GraphicLine(id="gl", points=[[150, 130], [180, 130]], role="other")
    [out] = recover_terminal_bridges([demoted], [_strip()], bridge_tol=8.0)
    assert out.role == "other"


def test_recover_terminal_gated_wires_promotes_other_with_two_ends() -> None:
    a = Component(
        id="A", type="zlaczka", bbox=[100, 100, 150, 180], source="yolo",
        terminals=[Terminal(id="1", x=1.0, y=0.5)],
    )
    b = Component(
        id="B", type="zlaczka", bbox=[300, 100, 350, 180], source="yolo",
        terminals=[Terminal(id="1", x=0.0, y=0.5)],
    )
    demoted = GraphicLine(id="gl", points=[[150, 140], [300, 140]], role="other")
    [out] = recover_terminal_gated_wires([demoted], [a, b], tol=10)
    assert out.role == "wire"


def test_sieve_keeps_wire_crossing_multiple_boxes() -> None:
    boxes = [
        Component(id=f"z{i}", type="zlaczka", bbox=[100 + i * 94, 100, 150 + i * 94, 180], source="yolo")
        for i in range(4)
    ]
    inner = _wire([[80, 140], [500, 140]])
    [out] = apply_sieve([inner], boxes, [], edge_tol=6.0)
    assert out.role == "wire"


def test_merge_collinear_wires_joins_gap() -> None:
    a = _wire([[0, 10], [50, 10]])
    b = _wire([[55, 10], [100, 10]])
    out = merge_collinear_wires([a, b], gap_tol=10)
    wires = [ln for ln in out if ln.role == "wire"]
    assert len(wires) == 1
    assert wires[0].points[0][0] <= 1
    assert wires[0].points[-1][0] >= 99


def test_long_bus_along_row_of_small_boxes_stays_wire() -> None:
    # Szyna listwy p027: pozioma linia przez wiele waskich zlaczek (nie obramowka jednego).
    boxes = [
        Component(id=f"z{i}", type="zlaczka", bbox=[100 + i * 94, 100, 150 + i * 94, 180], source="yolo")
        for i in range(8)
    ]
    bus = _wire([[80, 140], [900, 140]])
    [out] = apply_sieve([bus], boxes, [], edge_tol=6.0)
    assert out.role == "wire"
    assert LineClassifier.is_connection_candidate(out)


def test_long_wire_in_wide_ocr_bbox_stays_wire() -> None:
    # OCR na p027: szeroki plytki pasek tytulowy (~1475x70) nie demotuje szyny ~800px.
    bus = _wire([[100, 50], [900, 50]])
    title_bar = [80, 40, 1600, 110]
    [out] = apply_sieve([bus], [COMP], [title_bar], edge_tol=6.0)
    assert out.role == "wire"


def test_wire_spanning_most_of_large_symbol_stays_wire() -> None:
    # Przewod wzdłuż terminal_plc (676x474) — nie grafika wewnetrzna tabelki.
    plc = Component(id="plc", type="terminal_plc", bbox=[100, 100, 776, 574], source="yolo")
    bus = _wire([[120, 300], [740, 300]])
    [out] = apply_sieve([bus], [plc], [], edge_tol=6.0)
    assert out.role == "wire"


# --- terminal gate (po wyprowadzeniu terminali) ---
def test_terminal_gate_demotes_wire_without_terminal_contact() -> None:
    comp = Component(id="A", type="relay", bbox=[0, 0, 40, 40], source="yolo")
    wire = _wire([[100, 20], [200, 20]])  # daleko od symbolu bez terminali
    [out] = apply_terminal_gate([wire], [comp], tol=10)
    assert out.role == "other"


def test_terminal_gate_demotes_single_ended_stub() -> None:
    comp = Component(
        id="X1", type="zlaczka", bbox=[100, 100, 150, 180], source="yolo",
        terminals=[Terminal(id="1", x=0.0, y=0.5), Terminal(id="2", x=1.0, y=0.5)],
    )
    wire = _wire([[100, 140], [300, 140]])  # tylko lewy koniec przy terminalu
    [out] = apply_terminal_gate([wire], [comp], tol=10)
    assert out.role == "other"


def test_terminal_gate_keeps_wire_between_two_terminals() -> None:
    a = Component(
        id="A", type="zlaczka", bbox=[100, 100, 150, 180], source="yolo",
        terminals=[Terminal(id="1", x=1.0, y=0.5)],
    )
    b = Component(
        id="B", type="zlaczka", bbox=[300, 100, 350, 180], source="yolo",
        terminals=[Terminal(id="1", x=0.0, y=0.5)],
    )
    wire = _wire([[150, 140], [300, 140]])
    [out] = apply_terminal_gate([wire], [a, b], tol=10)
    assert out.role == "wire"


def test_terminal_gate_probe_finds_bbox_without_terminals() -> None:
    """Drugi bbox bez terminali — probe widzi kontakt wire z krawedzia."""
    a = Component(
        id="A", type="zlaczka", bbox=[100, 100, 150, 180], source="yolo",
        terminals=[Terminal(id="1", x=1.0, y=0.5)],
    )
    b = Component(id="B", type="zlaczka", bbox=[298, 100, 348, 180], source="yolo")
    wire = _wire([[150, 140], [300, 140]])
    [out] = apply_terminal_gate([wire], [a, b], tol=10, probe_tol=25)
    assert out.role == "wire"


def test_terminal_gate_keeps_bus_crossing_boxes_without_terminals() -> None:
    """p027: szyna przez rzad zlaczek bez terminali — przecina >=2 bboxy."""
    boxes = [
        Component(id=f"z{i}", type="zlaczka", bbox=[100 + i * 94, 100, 150 + i * 94, 180], source="yolo")
        for i in range(4)
    ]
    bus = _wire([[80, 140], [500, 140]])
    [out] = apply_terminal_gate([bus], boxes, tol=10)
    assert out.role == "wire"


def test_terminal_gate_keeps_bus_with_terminals_on_path() -> None:
    boxes = [
        Component(
            id=f"z{i}",
            type="zlaczka",
            bbox=[100 + i * 94, 100, 150 + i * 94, 180],
            source="yolo",
            terminals=[Terminal(id="1", x=0.5, y=0.5)],
        )
        for i in range(4)
    ]
    bus = _wire([[80, 140], [500, 140]])
    [out] = apply_terminal_gate([bus], boxes, tol=10)
    assert out.role == "wire"


def test_terminal_gate_keeps_internal_bridge() -> None:
    strip = _strip()
    bridge = _wire([[140, 150], [260, 150]])
    [out] = apply_terminal_gate([bridge], [strip], tol=10)
    assert out.role == "wire"
