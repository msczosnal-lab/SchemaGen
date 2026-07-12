"""Konfiguracja pytest — izolacja katalogu GT.

Autouse: każdy test dostaje własny, tymczasowy katalog ``gt/``, więc zapisy
grafów nie zaśmiecają repo i testy się nie przeplatają. Testy zależne od
konkretnego GT nadpisują to własnym monkeypatch (kolejność fixture: ten
uruchamia się pierwszy, indywidualny może ustawić inną ścieżkę).
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolate_gt_dir(tmp_path, monkeypatch):
    gt = tmp_path / "gt"
    gt.mkdir(parents=True, exist_ok=True)
    from backend import paths as paths_mod

    monkeypatch.setattr(paths_mod, "GT", gt)
    yield gt
