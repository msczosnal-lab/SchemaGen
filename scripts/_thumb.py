"""Miniatura crop -> PNG base64, z poprawa widocznosci cienkich/szarych linii.

- autocontrast: szara linia -> ciemniejsza (rozciagniecie zakresu),
- MinFilter (pogrubienie tuszu): cienka linia 1px przetrwa zmniejszenie,
- skalowanie w PIL (nie w przegladarce) do zadanej wysokosci.
"""
from __future__ import annotations

import base64
import io

import numpy as np
from PIL import Image, ImageOps, ImageFilter


def thumb_b64(arr: np.ndarray, height: int = 96, thicken: int = 1) -> str:
    im = Image.fromarray(arr).convert("L")
    im = ImageOps.autocontrast(im, cutoff=1)          # szare -> kontrastowe
    for _ in range(max(0, thicken)):
        im = im.filter(ImageFilter.MinFilter(3))      # tusz (ciemny) rosnie
    w, h = im.size
    if h > 0:
        scale = height / h
        im = im.resize((max(1, round(w * scale)), height), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()
