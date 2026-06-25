# COWORK_TASK: sync/prompts/002-ocr-engine.md

"""OCR tekstu schematu — PaddleOCR offline (bez cloud API).

Filar 2/3 interpretacji schematu: TEKST (tagi -K1, opisy, adresy krosowe).
Leniwy import paddleocr — jak onnxruntime w symbol_detector. Bez biblioteki:
czytelny ImportError z hintem instalacji.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class TextDetection:
    """Pojedynczy detekt tekstu na stronie schematu.

    bbox: [x1, y1, x2, y2] — prostokat osiowy w pikselach ORYGINALU obrazu.
    """

    text: str
    bbox: list[float]
    confidence: float


class PaddleOcrEngine:
    """OCR offline na PNG strony — PaddleOCR.

    Konstruktor (sygnatura wymagana przez GraphBuilder) — NIE zmieniac.
    lang: domyslnie 'en'. Polskie znaki: model 'latin' (diakrytyki) — patrz
    sync/zw-to-filip.md. PaddleOCR zwraca poligon 4-punktowy; rzutujemy na bbox
    osiowy [x1, y1, x2, y2].
    """

    def __init__(self, use_gpu: bool = True, lang: str = "en") -> None:
        self._use_gpu = use_gpu
        self._lang = lang
        self._engine = None

    def _ensure_engine(self):
        if self._engine is not None:
            return self._engine
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:  # pragma: no cover - srodowisko bez paddleocr (CI/PC ZW)
            raise ImportError(
                "Brak paddleocr. Zainstaluj offline: "
                "`pip install paddlepaddle paddleocr` "
                "(GPU: `pip install paddlepaddle-gpu`). "
                "Modele pobieraja sie raz przy pierwszym uruchomieniu."
            ) from exc
        self._engine = self._build_engine(PaddleOCR)
        return self._engine

    def _build_engine(self, paddle_ocr_cls):
        """Tworzy PaddleOCR tolerujac roznice API miedzy wersjami.

        Starsze (2.x): use_gpu=..., show_log=... ; nowsze (3.x) usunely te kwargi
        (device=...). Probujemy bogaty zestaw, potem degradujemy do minimalnego.
        """
        attempts = [
            {"use_angle_cls": True, "lang": self._lang, "use_gpu": self._use_gpu, "show_log": False},
            {"use_angle_cls": True, "lang": self._lang},
            {"lang": self._lang},
            {},
        ]
        last_exc: Exception | None = None
        for kwargs in attempts:
            try:
                return paddle_ocr_cls(**kwargs)
            except (TypeError, ValueError) as exc:  # nieznane kwargi w danej wersji
                last_exc = exc
        if last_exc is not None:  # pragma: no cover - awaria konstrukcji silnika
            raise last_exc
        return paddle_ocr_cls()  # pragma: no cover

    def extract_text(self, image_path: str | Path) -> list[TextDetection]:
        """Zwraca liste TextDetection (bbox w pikselach oryginalu)."""
        engine = self._ensure_engine()
        raw = self._run_engine(engine, str(image_path))
        return self._parse(raw)

    @staticmethod
    def _run_engine(engine, image_path: str):
        """Wywoluje OCR — preferuje .ocr(), z fallbackiem na .predict() (3.x)."""
        if hasattr(engine, "ocr"):
            try:
                return engine.ocr(image_path, cls=True)
            except TypeError:
                return engine.ocr(image_path)
        if hasattr(engine, "predict"):  # pragma: no cover - PaddleOCR 3.x
            return engine.predict(image_path)
        raise AttributeError("Silnik PaddleOCR nie ma metody .ocr ani .predict")

    @classmethod
    def _parse(cls, raw) -> list[TextDetection]:
        """Normalizuje wynik PaddleOCR do list[TextDetection].

        Format .ocr (2.x): [[ [poly4], (text, conf) ], ...] zagniezdzone per-obraz,
        czyli raw[0] to lista linii. raw bywa [None] gdy brak tekstu.
        """
        if not raw:
            return []
        lines = raw[0] if isinstance(raw[0], list) else raw
        if not lines:
            return []
        detections: list[TextDetection] = []
        for line in lines:
            parsed = cls._parse_line(line)
            if parsed is not None:
                detections.append(parsed)
        return detections

    @staticmethod
    def _parse_line(line) -> TextDetection | None:
        try:
            poly, text_conf = line[0], line[1]
            text = str(text_conf[0])
            confidence = float(text_conf[1])
        except (TypeError, IndexError, ValueError):
            return None
        xs = [float(p[0]) for p in poly]
        ys = [float(p[1]) for p in poly]
        bbox = [min(xs), min(ys), max(xs), max(ys)]
        return TextDetection(text=text, bbox=bbox, confidence=confidence)
