"""Testy GraphBuilder.build — mock detector/ocr/tracer/classifier (bez GPU/paddle/CV).

Sprawdza:
- SchemaModel ma components (source=yolo) + graphic_lines + connections,
- tag z OCR dopasowany do bbox symbolu, reszta tekstu -> annotations,
- linia wire tworzy Connection miedzy dwoma symbolami,
- linia device_stroke NIE tworzy Connection (regula krytyczna),
- meta.source ustawiony.
"""

from __future__ import annotations

from backend.models.detection import SymbolDetection
from backend.models.schema import GraphicLine
from backend.recognize.graph_builder import GraphBuilder, _apply_roi
from backend.recognize.ocr_engine import TextDetection


class _FakeDetector:
    def __init__(self, detections: list[SymbolDetection]) -> None:
        self._d = detections

    def detect(self, image_path: str):  # noqa: ARG002
        return self._d


class _FakeOcr:
    def __init__(self, texts: list[TextDetection]) -> None:
        self._t = texts

    def extract_text(self, image_path):  # noqa: ARG002
        return self._t


class _FakeTracer:
    def trace(self, image):  # noqa: ARG002
        return []  # segmenty nieistotne — classifier zwraca gotowe linie


class _FakeClassifier:
    def __init__(self, lines: list[GraphicLine]) -> None:
        self._lines = lines

    def classify(self, segments, *, image_size=None, **_kw):  # noqa: ARG002
        return self._lines


def _two_symbols() -> list[SymbolDetection]:
    # F (x 20..80, y 40..100) i U (x 120..220, y 30..130)
    return [
        SymbolDetection(class_id=0, class_name="fuse", confidence=0.9,
                        x=20, y=40, width=60, height=60),
        SymbolDetection(class_id=0, class_name="inverter", confidence=0.8,
                        x=120, y=30, width=100, height=100),
    ]


def _builder(*, detections, texts, lines) -> GraphBuilder:
    return GraphBuilder(
        detector=_FakeDetector(detections),
        ocr=_FakeOcr(texts),
        tracer=_FakeTracer(),
        classifier=_FakeClassifier(lines),
    )


def test_build_assembles_components_lines_connections() -> None:
    wire = GraphicLine(id="gl_0", points=[[80, 70], [120, 70]], role="wire")
    gb = _builder(detections=_two_symbols(), texts=[], lines=[wire])

    model = gb.build("page.png", source="data/raw/page.png")

    assert model.meta.source == "data/raw/page.png"
    assert len(model.components) == 2
    assert all(c.source == "yolo" for c in model.components)
    assert model.components[0].bbox == [20.0, 40.0, 80.0, 100.0]
    assert len(model.graphic_lines) == 1

    # wire laczy oba symbole (konce na krawedziach bbox). Auto-zaciski -> adres comp:terminal,
    # wiec porownujemy po komponencie (prefiks przed ":").
    assert len(model.connections) == 1
    conn = model.connections[0]
    ends = {conn.from_ref.split(":")[0], conn.to.split(":")[0]}
    assert ends == {"sym_0", "sym_1"}
    assert conn.kind == "power"


def test_device_stroke_line_makes_no_connection() -> None:
    stroke = GraphicLine(id="gl_0", points=[[80, 70], [120, 70]], role="device_stroke")
    gb = _builder(detections=_two_symbols(), texts=[], lines=[stroke])

    model = gb.build("page.png", source="x")

    assert len(model.graphic_lines) == 1
    assert model.connections == []  # device_stroke != Connection


def test_frame_and_dash_lines_make_no_connection() -> None:
    lines = [
        GraphicLine(id="gl_0", points=[[80, 70], [120, 70]], role="frame"),
        GraphicLine(id="gl_1", points=[[80, 70], [120, 70]], role="dash"),
        GraphicLine(id="gl_2", points=[[80, 70], [120, 70]], role="crossing"),
    ]
    gb = _builder(detections=_two_symbols(), texts=[], lines=lines)

    model = gb.build("page.png")
    assert model.connections == []


def test_ocr_tag_matched_to_symbol_and_rest_to_annotations() -> None:
    texts = [
        TextDetection(text="-F1", bbox=[30, 45, 60, 60], confidence=0.95),  # w F
        TextDetection(text="OPIS", bbox=[400, 400, 460, 420], confidence=0.9),  # poza
    ]
    gb = _builder(detections=_two_symbols(), texts=texts, lines=[])

    model = gb.build("page.png")

    fuse = next(c for c in model.components if c.type == "fuse")
    assert fuse.tag == "-F1"
    assert "OPIS" in model.annotations
    assert "-F1" not in model.annotations


def test_bus_role_deprecated_no_connection() -> None:
    # ADR connection-model: rola "bus" wycofana -> nie jest kandydatem -> brak Connection
    bus = GraphicLine(id="gl_0", points=[[80, 70], [120, 70]], role="bus")
    gb = _builder(detections=_two_symbols(), texts=[], lines=[bus])
    model = gb.build("page.png")
    assert model.connections == []


def test_wire_not_touching_symbols_no_connection() -> None:
    # konce daleko od jakiegokolwiek bbox -> brak Connection
    wire = GraphicLine(id="gl_0", points=[[1000, 1000], [1200, 1000]], role="wire")
    gb = _builder(detections=_two_symbols(), texts=[], lines=[wire])
    model = gb.build("page.png")
    assert model.connections == []


def test_pe_group_sets_pe_kind() -> None:
    wire = GraphicLine(
        id="gl_0", points=[[80, 70], [120, 70]], role="wire", semantic_group="pe_wire"
    )
    gb = _builder(detections=_two_symbols(), texts=[], lines=[wire])
    model = gb.build("page.png")
    assert model.connections[0].kind == "pe"


def test_roi_drops_lines_fully_below_cutoff() -> None:
    size = (1000, 1000)  # cutoff przy frac 0.85 -> y=850
    top = GraphicLine(id="a", points=[[10, 100], [200, 100]], role="wire")
    bottom = GraphicLine(id="b", points=[[10, 900], [200, 900]], role="wire")  # tabliczka
    spanning = GraphicLine(id="c", points=[[10, 800], [10, 950]], role="wire")  # siega rysunku
    out = _apply_roi([top, bottom, spanning], size, 0.85)
    ids = {ln.id for ln in out}
    assert ids == {"a", "c"}  # dol odciety, linia siegajaca rysunku zostaje


def test_roi_noop_when_disabled_or_no_size() -> None:
    lines = [GraphicLine(id="a", points=[[10, 900], [200, 900]], role="wire")]
    assert len(_apply_roi(lines, (1000, 1000), 1.0)) == 1   # frac>=1 = bez ciecia
    assert len(_apply_roi(lines, None, 0.85)) == 1          # brak size = no-op
