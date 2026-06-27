"""Testy PaddleOcrEngine — bez paddleocr/GPU (wstrzykniety fake engine)."""

from __future__ import annotations

import builtins

import pytest

from backend.recognize.ocr_engine import PaddleOcrEngine, TextDetection


class _FakePaddle:
    """Atrapa PaddleOCR — zwraca staly wynik w formacie .ocr() 2.x."""

    def __init__(self, result) -> None:
        self._result = result

    def ocr(self, _image_path, cls=True):
        return self._result


def _engine_with(result) -> PaddleOcrEngine:
    eng = PaddleOcrEngine(use_gpu=False)
    eng._engine = _FakePaddle(result)  # pomija _ensure_engine / import paddleocr
    # KLUCZOWE: wymus in-process. Bez tego, gdy istnieje .venv-ocr (PC Filip),
    # extract_text deleguje do subprocesu i ignoruje wstrzyknieta atrape.
    eng._subprocess_ok = False
    return eng


def test_extract_text_parses_two_detections() -> None:
    # format PaddleOCR 2.x: raw[0] = lista linii [ [poly4], (text, conf) ]
    raw = [[
        [[[10, 20], [60, 20], [60, 40], [10, 40]], ("-K1", 0.98)],
        [[[100, 200], [180, 205], [180, 230], [100, 225]], ("MOTOR", 0.91)],
    ]]
    dets = _engine_with(raw).extract_text("page.png")

    assert len(dets) == 2
    assert all(isinstance(d, TextDetection) for d in dets)
    assert dets[0].text == "-K1"
    assert dets[0].bbox == [10.0, 20.0, 60.0, 40.0]
    assert abs(dets[0].confidence - 0.98) < 1e-6
    # bbox osiowy z poligonu nieprostokatnego (min/max)
    assert dets[1].bbox == [100.0, 200.0, 180.0, 230.0]


def test_extract_text_empty_page() -> None:
    assert _engine_with([None]).extract_text("page.png") == []
    assert _engine_with([]).extract_text("page.png") == []


def test_extract_text_skips_malformed_line() -> None:
    raw = [[
        [[[0, 0], [10, 0], [10, 10], [0, 10]], ("OK", 0.5)],
        ["garbage"],  # niepoprawna linia — pomijana
    ]]
    dets = _engine_with(raw).extract_text("page.png")
    assert len(dets) == 1
    assert dets[0].text == "OK"


def test_missing_paddleocr_raises_import_error(monkeypatch) -> None:
    real_import = builtins.__import__

    def _fake_import(name, *args, **kwargs):
        if name == "paddleocr" or name.startswith("paddleocr."):
            raise ImportError("no module")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _fake_import)
    eng = PaddleOcrEngine(use_gpu=False)
    with pytest.raises(ImportError, match="pip install"):
        eng.extract_text("page.png")


def test_build_engine_degrades_kwargs() -> None:
    """Nowsza wersja PaddleOCR bez use_gpu/show_log — degradacja kwargs."""
    seen = {}

    class _StrictPaddle:
        def __init__(self, lang="en", **kwargs):
            if kwargs:
                raise TypeError("unexpected kwargs")
            seen["lang"] = lang

    eng = PaddleOcrEngine(use_gpu=True, lang="latin")
    built = eng._build_engine(_StrictPaddle)
    assert isinstance(built, _StrictPaddle)
    assert seen["lang"] == "latin"


def test_parse_predict_dict_format() -> None:
    raw = [{
        "rec_texts": ["-K1", "MOTOR"],
        "rec_scores": [0.98, 0.91],
        "rec_polys": [
            [[10, 20], [60, 20], [60, 40], [10, 40]],
            [[100, 200], [180, 205], [180, 230], [100, 225]],
        ],
    }]
    dets = PaddleOcrEngine._parse(raw)
    assert len(dets) == 2
    assert dets[0].text == "-K1"
    assert dets[0].bbox == [10.0, 20.0, 60.0, 40.0]


def test_extract_text_uses_subprocess_when_torch_loaded(monkeypatch, tmp_path) -> None:
    import sys

    img = tmp_path / "page.png"
    img.write_bytes(b"fake")

    monkeypatch.setitem(sys.modules, "torch", object())

    payload = [{"text": "ABC", "bbox": [1, 2, 3, 4], "confidence": 0.5}]

    def _fake_run(cmd, **kwargs):
        class _Proc:
            returncode = 0
            stdout = __import__("json").dumps(payload)
            stderr = ""

        return _Proc()

    monkeypatch.setattr("backend.recognize.ocr_engine.subprocess.run", _fake_run)
    dets = PaddleOcrEngine(use_gpu=False, lang="en").extract_text(img)
    assert len(dets) == 1
    assert dets[0].text == "ABC"
