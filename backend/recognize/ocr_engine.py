# COWORK_TASK: sync/prompts/002-ocr-engine.md

"""OCR tekstu schematu — PaddleOCR offline (bez cloud API).

Filar 2/3 interpretacji schematu: TEKST (tagi -K1, opisy, adresy krosowe).
Leniwy import paddleocr — jak onnxruntime w symbol_detector. Bez biblioteki:
czytelny ImportError z hintem instalacji.

Gdy torch jest juz w procesie (YOLO), OCR idzie przez scripts/ocr_worker.py
(subprocess) — unika konfliktu libpaddle vs CUDA torch.
"""

from __future__ import annotations

import json
import subprocess
import sys
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


_REPO_ROOT = Path(__file__).resolve().parents[2]
_OCR_WORKER = _REPO_ROOT / "scripts" / "ocr_worker.py"
_OCR_VENV_PYTHON = _REPO_ROOT / ".venv-ocr" / "Scripts" / "python.exe"


def _ocr_python() -> str:
    """Osobny venv bez torch — unika konfliktu paddleocr 3.x + torch + paddle-gpu."""
    if _OCR_VENV_PYTHON.is_file():
        return str(_OCR_VENV_PYTHON)
    return sys.executable


def _parse_worker_stdout(stdout: str) -> list:
    """JSON z workera — ostatnia linia tablicy (ppocr logi moga trafic na stdout)."""
    for line in reversed(stdout.splitlines()):
        s = line.strip()
        if s.startswith("[{"):
            return json.loads(s)
    raise RuntimeError("OCR worker: brak JSON w stdout")


def _torch_loaded() -> bool:
    return "torch" in sys.modules


def extract_text_inprocess(
    image_path: str | Path,
    *,
    use_gpu: bool = True,
    lang: str = "en",
) -> list[TextDetection]:
    """OCR w biezacym procesie — tylko worker/subprocess-free sciezki."""
    eng = PaddleOcrEngine(use_gpu=use_gpu, lang=lang)
    eng._subprocess_ok = False
    return eng.extract_text(image_path)


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
        self._subprocess_ok = True
        self._init_failed = False

    def _ensure_engine(self):
        if self._engine is not None:
            return self._engine
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "Brak paddleocr. Zainstaluj offline: "
                "`pip install paddlepaddle paddleocr` "
                "(GPU: `pip install paddlepaddle-gpu`). "
                "Modele pobieraja sie raz przy pierwszym uruchomieniu."
            ) from exc
        self._engine = self._build_engine(PaddleOCR)
        return self._engine

    def _build_engine(self, paddle_ocr_cls):
        """Tworzy PaddleOCR tolerujac roznice API miedzy wersjami 2.x i 3.x."""
        device = "gpu" if self._use_gpu else "cpu"
        attempts = [
            {
                "lang": self._lang,
                "device": device,
                "use_doc_orientation_classify": False,
                "use_doc_unwarping": False,
                "use_textline_orientation": False,
            },
            {"lang": self._lang, "device": device},
            {
                "use_angle_cls": True,
                "lang": self._lang,
                "use_gpu": self._use_gpu,
                "show_log": False,
            },
            {"use_angle_cls": True, "lang": self._lang},
            {"lang": self._lang},
            {},
        ]
        last_exc: Exception | None = None
        for kwargs in attempts:
            try:
                return paddle_ocr_cls(**kwargs)
            except (TypeError, ValueError) as exc:
                last_exc = exc
        if last_exc is not None:  # pragma: no cover
            raise last_exc
        return paddle_ocr_cls()  # pragma: no cover

    def extract_text(self, image_path: str | Path) -> list[TextDetection]:
        """Zwraca liste TextDetection (bbox w pikselach oryginalu)."""
        path = Path(image_path)
        use_worker = (
            self._subprocess_ok
            and _OCR_VENV_PYTHON.is_file()
            and _ocr_python() != sys.executable
        )
        if self._subprocess_ok and (use_worker or _torch_loaded() or self._init_failed):
            return self._extract_via_subprocess(path)
        try:
            return self._extract_inprocess(path)
        except ImportError:
            raise
        except Exception:
            if not self._subprocess_ok:
                raise
            self._init_failed = True
            return self._extract_via_subprocess(path)

    def _extract_inprocess(self, path: Path) -> list[TextDetection]:
        engine = self._ensure_engine()
        raw = self._run_engine(engine, str(path))
        return self._parse(raw)

    def _extract_via_subprocess(self, path: Path) -> list[TextDetection]:
        if not _OCR_WORKER.exists():  # pragma: no cover
            raise FileNotFoundError(f"Brak worker OCR: {_OCR_WORKER}")
        cmd = [
            _ocr_python(),
            str(_OCR_WORKER),
            str(path.resolve()),
            "--lang",
            self._lang,
        ]
        if not self._use_gpu:
            cmd.append("--cpu")
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(_REPO_ROOT),
        )
        if proc.returncode != 0:
            err = proc.stderr.strip() or proc.stdout.strip() or "OCR worker failed"
            try:
                payload = json.loads(err)
                err = payload.get("error", err)
            except json.JSONDecodeError:
                pass
            raise RuntimeError(err)
        data = _parse_worker_stdout(proc.stdout)
        return [
            TextDetection(
                text=str(item["text"]),
                bbox=[float(v) for v in item["bbox"]],
                confidence=float(item["confidence"]),
            )
            for item in data
        ]

    @staticmethod
    def _run_engine(engine, image_path: str):
        """Wywoluje OCR — preferuje .ocr(), z fallbackiem na .predict() (3.x)."""
        if hasattr(engine, "ocr"):
            try:
                return engine.ocr(image_path, cls=True)
            except TypeError:
                return engine.ocr(image_path)
        if hasattr(engine, "predict"):  # pragma: no cover
            return engine.predict(image_path)
        raise AttributeError("Silnik PaddleOCR nie ma metody .ocr ani .predict")

    @classmethod
    def _parse(cls, raw) -> list[TextDetection]:
        """Normalizuje wynik PaddleOCR 2.x (.ocr) i 3.x (.predict)."""
        if not raw:
            return []
        if isinstance(raw, list) and raw:
            first = raw[0]
            if isinstance(first, dict):
                return cls._parse_predict_page(first)
            if hasattr(first, "rec_texts"):
                return cls._parse_predict_obj(first)
        lines = raw[0] if isinstance(raw, list) and raw and isinstance(raw[0], list) else raw
        if not lines:
            return []
        detections: list[TextDetection] = []
        for line in lines:
            parsed = cls._parse_line(line)
            if parsed is not None:
                detections.append(parsed)
        return detections

    @classmethod
    def _parse_predict_page(cls, page: dict) -> list[TextDetection]:
        texts = page.get("rec_texts") or page.get("texts") or []
        scores = page.get("rec_scores") or page.get("scores") or []
        polys = (
            page.get("rec_polys")
            or page.get("dt_polys")
            or page.get("rec_boxes")
            or []
        )
        out: list[TextDetection] = []
        for i, text in enumerate(texts):
            conf = float(scores[i]) if i < len(scores) else 0.0
            bbox = cls._poly_to_bbox(polys[i]) if i < len(polys) else [0.0, 0.0, 0.0, 0.0]
            out.append(TextDetection(text=str(text), bbox=bbox, confidence=conf))
        return out

    @classmethod
    def _parse_predict_obj(cls, page) -> list[TextDetection]:
        texts = getattr(page, "rec_texts", None) or []
        scores = getattr(page, "rec_scores", None) or []
        polys = getattr(page, "rec_polys", None) or getattr(page, "dt_polys", None) or []
        out: list[TextDetection] = []
        for i, text in enumerate(texts):
            conf = float(scores[i]) if i < len(scores) else 0.0
            bbox = cls._poly_to_bbox(polys[i]) if i < len(polys) else [0.0, 0.0, 0.0, 0.0]
            out.append(TextDetection(text=str(text), bbox=bbox, confidence=conf))
        return out

    @staticmethod
    def _poly_to_bbox(poly) -> list[float]:
        if poly is None:
            return [0.0, 0.0, 0.0, 0.0]
        if len(poly) == 4 and all(isinstance(v, (int, float)) for v in poly):
            x1, y1, x2, y2 = (float(v) for v in poly)
            return [min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)]
        xs = [float(p[0]) for p in poly]
        ys = [float(p[1]) for p in poly]
        return [min(xs), min(ys), max(xs), max(ys)]

    @staticmethod
    def _parse_line(line) -> TextDetection | None:
        try:
            poly, text_conf = line[0], line[1]
            text = str(text_conf[0])
            confidence = float(text_conf[1])
        except (TypeError, IndexError, ValueError):
            return None
        return TextDetection(
            text=text,
            bbox=PaddleOcrEngine._poly_to_bbox(poly),
            confidence=confidence,
        )
