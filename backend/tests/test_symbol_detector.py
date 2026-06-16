"""Testy detektora ONNX — bez onnxruntime/GPU (wstrzykniety fake session)."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from backend.recognize.symbol_detector import OnnxSymbolDetector


class _FakeSession:
    """Atrapa onnxruntime.InferenceSession — zwraca staly tensor wyjsciowy."""

    def __init__(self, output: np.ndarray) -> None:
        self._output = output

    def get_inputs(self):
        return [type("Inp", (), {"name": "images"})()]

    def run(self, _out_names, _feed):
        return [self._output]


def _detector_with_output(output: np.ndarray, imgsz: int = 640) -> OnnxSymbolDetector:
    det = OnnxSymbolDetector(model_path="fake.onnx", class_map={"element": 0}, imgsz=imgsz)
    det._session = _FakeSession(output)  # pomija _ensure_session / onnxruntime
    det._input_name = "images"
    return det


def _write_image(tmp_path: Path, w: int = 1280, h: int = 640) -> str:
    path = tmp_path / "page.png"
    cv2.imwrite(str(path), np.zeros((h, w, 3), dtype=np.uint8))
    return str(path)


def test_detect_maps_box_to_original_coords(tmp_path: Path) -> None:
    # 1280x640 -> letterbox: scale 0.5, pad_top=160 (wysrodkowane).
    # detekcja cx=320,cy=320,w=100,h=80 w przestrzeni letterboxa 640x640.
    output = np.array([[[320.0], [320.0], [100.0], [80.0], [0.9]]], dtype=np.float32)
    det = _detector_with_output(output)
    results = det.detect(_write_image(tmp_path))

    assert len(results) == 1
    d = results[0]
    assert d.class_id == 0
    assert d.class_name == "element"
    assert abs(d.confidence - 0.9) < 1e-5
    # mapowanie do oryginalu: x=(320-50-0)/0.5=540, y=(320-40-160)/0.5=240
    assert abs(d.x - 540.0) < 1.0
    assert abs(d.y - 240.0) < 1.0
    assert abs(d.width - 200.0) < 1.0
    assert abs(d.height - 160.0) < 1.0


def test_detect_filters_low_confidence(tmp_path: Path) -> None:
    output = np.array([[[320.0], [160.0], [100.0], [80.0], [0.05]]], dtype=np.float32)
    det = _detector_with_output(output)
    assert det.detect(_write_image(tmp_path), conf_threshold=0.25) == []


def test_detect_unknown_class_falls_back_to_id(tmp_path: Path) -> None:
    # 2 klasy w wyjsciu, brak mapy nazw -> class_name = str(id)
    det = OnnxSymbolDetector(model_path="fake.onnx", imgsz=640)  # pusty class_map
    output = np.array([[[320.0], [160.0], [100.0], [80.0], [0.1], [0.8]]], dtype=np.float32)
    det._session = _FakeSession(output)
    det._input_name = "images"
    results = det.detect(_write_image(tmp_path))
    assert len(results) == 1
    assert results[0].class_id == 1
    assert results[0].class_name == "1"
