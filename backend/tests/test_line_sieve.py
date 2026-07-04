"""Testy sita linii — obramowki bbox -> frame, tekst -> other, przewody zostaja."""

from backend.models.schema import Component, GraphicLine, Terminal
from backend.recognize.line_classifier import LineClassifier
from backend.recognize.line_sieve import apply_sieve, recover_terminal_bridges

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
