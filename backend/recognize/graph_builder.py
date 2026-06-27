# COWORK_TASK: sync/prompts/004-graph-builder.md

"""Budowa grafu polaczen z detekcji + OCR + linii.

Sklada SchemaModel z trzech filarow (kazdy GOTOWY — tu tylko orkiestracja):
- OnnxSymbolDetector  -> components (bbox, type, confidence, source=yolo)
- PaddleOcrEngine     -> tagi dopasowane do bbox + annotations[]
- LineTracer+Classifier -> graphic_lines[]

Regula krytyczna: GraphicLine != Connection. Connection powstaje WYLACZNIE
z linii gdzie LineClassifier.is_connection_candidate(line) == True (role wire|bus).
Linie device_stroke / frame / dash / crossing trafiaja tylko do graphic_lines.
"""

from __future__ import annotations

import json

from backend.models.label import BboxAnnotation
from backend.models.schema import (
    Component,
    Connection,
    GraphicLine,
    SchemaMeta,
    SchemaModel,
)
from backend.geometry.row_layout import ContextAssignment, ContextResolver
from backend.paths import REGISTRY_PATH
from backend.recognize.line_classifier import LineClassifier
from backend.recognize.line_sieve import apply_sieve
from backend.recognize.line_tracer import LineTracer
from backend.recognize.ocr_engine import PaddleOcrEngine
from backend.recognize.symbol_detector import OnnxSymbolDetector

# Tolerancja terminala: maks. odleglosc konca linii od bbox symbolu (px), przy
# ktorej uznajemy ze linia "wchodzi" w symbol. Skalowana z rozmiarem strony.
TERMINAL_TOL_FRAC = 0.012
TERMINAL_TOL_MIN = 12.0

# semantic_group / role -> ConnectionKind
_PE_GROUPS = frozenset({"pe", "pe_wire", "ground", "earth"})


class GraphBuilder:
    def __init__(
        self,
        detector: OnnxSymbolDetector | None = None,
        ocr: PaddleOcrEngine | None = None,
        tracer: LineTracer | None = None,
        classifier: LineClassifier | None = None,
    ) -> None:
        self._detector = detector
        self._ocr = ocr
        self._tracer = tracer
        self._classifier = classifier

    def resolve_context(self, bboxes: list[BboxAnnotation]) -> list[ContextAssignment]:
        """Faza 2: przypisanie rol kontekstowych (wiersze Y) na GT bboxach."""
        return ContextResolver().resolve(bboxes)

    # ------------------------------------------------------------------ build
    def build(self, image_path: str, source: str = "") -> SchemaModel:
        size = _image_size(image_path)

        # 1) Detekcja symboli -> components
        detections = self._detect(image_path)
        components = [
            Component(
                id=f"sym_{i}",
                type=d.class_name,
                bbox=[d.x, d.y, d.x + d.width, d.y + d.height],
                confidence=d.confidence,
                source="yolo",
            )
            for i, d in enumerate(detections)
        ]

        # 2) OCR -> dopasuj tagi do bbox; reszta tekstu -> annotations[]
        texts = self._ocr_engine().extract_text(image_path)
        annotations = self._assign_tags(texts, components)

        # 3) Trace + classify -> graphic_lines
        segments = self._trace(image_path)
        graphic_lines = self._classify(segments, size)

        # 3b) Sito: obramowki bbox -> frame, artefakty tekstu -> other (poza wire/bus)
        graphic_lines = apply_sieve(
            graphic_lines,
            components,
            [t.bbox for t in texts],
            edge_tol=_edge_tol(size),
        )

        # 4) Connections WYLACZNIE z linii wire/bus (po sicie)
        connections = self._build_connections(graphic_lines, components, size)

        # 5) Kontekst (best-effort na bboxach detekcji + tagach OCR)
        context_assignments = self._resolve_context_safe(detections, components)

        return SchemaModel(
            meta=SchemaMeta(
                source=source,
                page=0,
                model_version=_model_version(),
            ),
            components=components,
            graphic_lines=graphic_lines,
            connections=connections,
            context_assignments=context_assignments,
            annotations=annotations,
        )

    # ----------------------------------------------------------- filary (lazy)
    def _detect(self, image_path: str):
        det = self._detector or OnnxSymbolDetector(_active_model_path())
        return det.detect(image_path)

    def _trace(self, image_path: str):
        tracer = self._tracer or LineTracer()
        return tracer.trace(image_path)

    def _classify(self, segments, size):
        classifier = self._classifier or LineClassifier()
        return classifier.classify(segments, image_size=size)

    def _ocr_engine(self) -> PaddleOcrEngine:
        return self._ocr or PaddleOcrEngine()

    # -------------------------------------------------------------------- OCR
    def _assign_tags(self, texts, components: list[Component]) -> list[str]:
        """Dopasuj tekst do symbolu (bbox OCR ∩ bbox symbolu). Reszta -> annotations."""
        annotations: list[str] = []
        # najlepsze dopasowanie tekst->symbol po polu przeciecia
        for t in texts:
            best_i = -1
            best_overlap = 0.0
            for i, c in enumerate(components):
                ov = _intersection_area(t.bbox, c.bbox)
                if ov > best_overlap:
                    best_overlap = ov
                    best_i = i
            if best_i >= 0 and best_overlap > 0.0:
                c = components[best_i]
                # nie nadpisuj — pierwszy (najwiekszy overlap przetwarzany sekwencyjnie):
                # zostaw dotychczasowy tag jesli juz ustawiony, dopisz resztę do annotations
                if not c.tag:
                    c.tag = t.text
                else:
                    annotations.append(t.text)
            else:
                annotations.append(t.text)
        return annotations

    # ------------------------------------------------------------- connections
    def _build_connections(
        self,
        graphic_lines: list[GraphicLine],
        components: list[Component],
        size: tuple[int, int] | None,
    ) -> list[Connection]:
        tol = _terminal_tol(size)
        connections: list[Connection] = []
        seen: set[tuple[str, str, str]] = set()
        for line in graphic_lines:
            # KRYTYCZNE: tylko wire/bus. device_stroke/frame/dash/crossing -> pomin.
            if not LineClassifier.is_connection_candidate(line):
                continue
            if len(line.points) < 2:
                continue
            a = line.points[0]
            b = line.points[-1]
            from_c = _nearest_component(a, components, tol)
            to_c = _nearest_component(b, components, tol)
            if from_c is None or to_c is None or from_c.id == to_c.id:
                continue
            kind = _kind_for(line)
            key = (from_c.id, to_c.id, kind)
            rkey = (to_c.id, from_c.id, kind)
            if key in seen or rkey in seen:
                continue
            seen.add(key)
            connections.append(
                Connection(
                    from_ref=from_c.id,
                    to=to_c.id,
                    potential="",
                    kind=kind,
                )
            )
        return connections

    # ----------------------------------------------------------------- context
    def _resolve_context_safe(self, detections, components) -> list[ContextAssignment]:
        try:
            bboxes = [
                BboxAnnotation(
                    id=c.id,
                    class_name=d.class_name,
                    x=d.x,
                    y=d.y,
                    width=d.width,
                    height=d.height,
                    tag=c.tag,
                )
                for c, d in zip(components, detections)
            ]
            return self.resolve_context(bboxes)
        except Exception:
            return []


# ---------------------------------------------------------------- helpers (czyste)
def _image_size(image_path: str) -> tuple[int, int] | None:
    try:
        import cv2

        img = cv2.imread(str(image_path))
        if img is None:
            return None
        h, w = img.shape[:2]
        return (int(w), int(h))
    except Exception:
        return None


def _terminal_tol(size: tuple[int, int] | None) -> float:
    if not size:
        return TERMINAL_TOL_MIN
    w, h = size
    return max(TERMINAL_TOL_MIN, TERMINAL_TOL_FRAC * max(w, h))


def _edge_tol(size: tuple[int, int] | None) -> float:
    """Tolerancja 'linia lezy na boku bbox' — grubosc obrysu/rejestracja skanu."""
    if not size:
        return 6.0
    w, h = size
    return max(6.0, 0.004 * max(w, h))


def _intersection_area(a: list[float], b: list[float]) -> float:
    """Pole przeciecia dwoch bboxow [x1,y1,x2,y2]. 0 gdy brak nakladania."""
    if len(a) < 4 or len(b) < 4:
        return 0.0
    ix1 = max(a[0], b[0])
    iy1 = max(a[1], b[1])
    ix2 = min(a[2], b[2])
    iy2 = min(a[3], b[3])
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    return (ix2 - ix1) * (iy2 - iy1)


def _point_bbox_dist(point: list[float], bbox: list[float]) -> float:
    """Odleglosc punktu od prostokata [x1,y1,x2,y2] (0 gdy w srodku)."""
    if len(bbox) < 4:
        return float("inf")
    px, py = point[0], point[1]
    dx = max(bbox[0] - px, 0.0, px - bbox[2])
    dy = max(bbox[1] - py, 0.0, py - bbox[3])
    return (dx * dx + dy * dy) ** 0.5


def _nearest_component(
    point: list[float], components: list[Component], max_dist: float
) -> Component | None:
    best: Component | None = None
    best_d = max_dist
    for c in components:
        d = _point_bbox_dist(point, c.bbox)
        if d <= best_d:
            best_d = d
            best = c
    return best


def _kind_for(line: GraphicLine) -> str:
    group = (line.semantic_group or "").lower()
    if group in _PE_GROUPS or "pe" in group:
        return "pe"
    return "power"


def _model_version() -> str:
    try:
        if REGISTRY_PATH.exists():
            registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
            active = registry.get("active")
            if active:
                return str(active)
    except Exception:
        pass
    return ""


def _active_model_path() -> str:
    try:
        if REGISTRY_PATH.exists():
            registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
            active = registry.get("active")
            versions = registry.get("versions", {})
            if active and active in versions:
                return str(versions[active].get("onnx_path", ""))
    except Exception:
        pass
    return ""
