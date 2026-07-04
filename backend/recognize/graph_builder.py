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
    GraphicLine,
    SchemaMeta,
    SchemaModel,
)
from backend.geometry.row_layout import ContextAssignment, ContextResolver
from backend.paths import REGISTRY_PATH
from backend.runtime_config import (
    connection_require_terminal,
    roi_bottom_cut_frac,
    terminal_tol_frac,
    terminal_tol_min,
)
from backend.recognize.line_classifier import LineClassifier
from backend.recognize.line_sieve import apply_sieve, recover_terminal_bridges
from backend.recognize.line_tracer import LineTracer
from backend.recognize.net_builder import (
    build_connections as build_net_connections,
    derive_auto_terminals,
)
from backend.recognize.ocr_engine import PaddleOcrEngine
from backend.recognize.relation_resolver import RelationResolver
from backend.recognize.symbol_detector import OnnxSymbolDetector

# Tolerancja terminala: maks. odleglosc konca linii od bbox symbolu (px), przy
# ktorej uznajemy ze linia "wchodzi" w symbol. Skalowana z rozmiarem strony.
# Wartosci domyslne (fallback gdy brak configu); zrodlo prawdy: config/runtime.yaml.
TERMINAL_TOL_FRAC = 0.012
TERMINAL_TOL_MIN = 12.0


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

        # 2) OCR — tekst surowy; tagi i annotations dopina RelationResolver (krok 6)
        texts = self._ocr_engine().extract_text(image_path)

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

        # 3c) ROI: odetnij linie z dolu arkusza (tabliczka/tabelki) — config
        graphic_lines = _apply_roi(graphic_lines, size, roi_bottom_cut_frac())

        # 4) Auto-zaciski: terminal = kontakt konca wire z krawedzia bboxa
        #    (komponenty bez recznych terminali GT). Daje adresowanie comp:terminal.
        tol = _terminal_tol(size)
        candidate_lines = [
            ln for ln in graphic_lines if LineClassifier.is_connection_candidate(ln)
        ]
        for c in components:
            if not c.terminals:
                c.terminals = derive_auto_terminals(c, candidate_lines, tol)

        # 4b) Odzysk mostkow w listwie: linie zdemotowane do 'other' przez sito, ktorych
        #     konce trafiaja w 2 terminale tego samego komponentu, wracaja jako wire
        #     (mostek terminal<->terminal -> Connection kind="link").
        graphic_lines = recover_terminal_bridges(
            graphic_lines, components, bridge_tol=tol
        )

        # 5) Nets: scal segmenty wire/bus w sieci -> Connection (Warstwa 1)
        connections, potentials = build_net_connections(
            graphic_lines,
            components,
            join_tol=tol,
            terminal_tol=tol,
            require_terminal=_require_terminal(),
        )

        # 6) Relacje: tagi, potencjaly, context runtime (prompt 015)
        components, connections, potentials, context_assignments, annotations = (
            RelationResolver().resolve(
                components,
                texts,
                connections,
                graphic_lines,
                potentials,
                image_size=size,
            )
        )

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
            potentials=potentials,
            annotations=annotations,
        )

    # ----------------------------------------------------------- filary (lazy)
    def _detect(self, image_path: str):
        det = self._detector or OnnxSymbolDetector(_active_model_path())
        from backend.runtime_config import yolo_tile_overlap, yolo_tile_win, yolo_tiled
        if yolo_tiled():
            return det.detect_tiled(image_path, win=yolo_tile_win(), overlap=yolo_tile_overlap())
        return det.detect(image_path)

    def _trace(self, image_path: str):
        tracer = self._tracer or LineTracer()
        return tracer.trace(image_path)

    def _classify(self, segments, size):
        classifier = self._classifier or LineClassifier()
        return classifier.classify(segments, image_size=size)

    def _ocr_engine(self) -> PaddleOcrEngine:
        return self._ocr or PaddleOcrEngine()


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


def _require_terminal() -> bool:
    try:
        return connection_require_terminal()
    except Exception:
        return False


def _terminal_tol(size: tuple[int, int] | None) -> float:
    try:
        frac = terminal_tol_frac()
        tmin = terminal_tol_min()
    except Exception:
        frac, tmin = TERMINAL_TOL_FRAC, TERMINAL_TOL_MIN
    if not size:
        return tmin
    w, h = size
    return max(tmin, frac * max(w, h))


def _edge_tol(size: tuple[int, int] | None) -> float:
    """Tolerancja 'linia lezy na boku bbox' — grubosc obrysu/rejestracja skanu."""
    if not size:
        return 6.0
    w, h = size
    return max(6.0, 0.004 * max(w, h))


def _apply_roi(
    lines: list[GraphicLine], size: tuple[int, int] | None, frac: float
) -> list[GraphicLine]:
    """Usun linie w CALOSCI ponizej frac*H (dol arkusza). frac>=1 lub brak size -> no-op."""
    if not size or frac >= 1.0:
        return lines
    cutoff = frac * size[1]
    out: list[GraphicLine] = []
    for ln in lines:
        if not ln.points:
            out.append(ln)
            continue
        top_y = min(p[1] for p in ln.points)  # najwyzszy punkt linii
        if top_y < cutoff:  # linia siega obszaru rysunku -> zostaw
            out.append(ln)
    return out


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
