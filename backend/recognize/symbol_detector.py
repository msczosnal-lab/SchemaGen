# COWORK_TASK: sync/prompts/001-symbol-detector.md

"""Detekcja symboli — YOLOv8 ONNX na RTX 2080 (offline, bez cloud API)."""

from __future__ import annotations

import cv2
import numpy as np

from backend.geometry.row_layout import dedup_detections_by_row
from backend.ingest.image_utils import load_bgr
from backend.models.detection import SymbolDetection
from backend.runtime_config import yolo_conf_threshold, yolo_imgsz, yolo_runtime_exclude_classes
PROVIDERS = ["CUDAExecutionProvider", "CPUExecutionProvider"]


def _enable_cuda_dlls() -> None:
    """Windows: pozwol onnxruntime-gpu znalezc cublasLt64_12.dll / cuDNN 9 z torch (cu121).

    torch 2.5.1+cu121 wozi te DLL w site-packages/torch/lib. Bez tego CUDAExecutionProvider
    nie laduje sie i onnxruntime spada na CPU. Best-effort, bez wyjatkow.
    """
    import os

    if not hasattr(os, "add_dll_directory"):  # nie-Windows
        return
    candidates = []
    try:
        import torch

        candidates.append(os.path.join(os.path.dirname(torch.__file__), "lib"))
    except Exception:
        pass
    for mod in ("nvidia.cublas.bin", "nvidia.cudnn.bin"):
        try:
            import importlib

            candidates.append(os.path.dirname(importlib.import_module(mod).__file__))
        except Exception:
            pass
    for d in candidates:
        try:
            if d and os.path.isdir(d):
                os.add_dll_directory(d)
        except Exception:
            pass


class OnnxSymbolDetector:
    """Detekcja symboli schematu — YOLOv8 ONNX."""

    def __init__(
        self,
        model_path: str,
        class_map: dict[str, int] | None = None,
        imgsz: int | None = None,
    ) -> None:
        self._model_path = model_path
        self._class_map = class_map or {}
        self._imgsz = imgsz if imgsz is not None else yolo_imgsz()
        self._id_to_name = {idx: name for name, idx in self._class_map.items()}
        self._session = None
        self._input_name: str | None = None

    def _ensure_session(self):
        if self._session is not None:
            return self._session
        try:
            import onnxruntime as ort
        except ImportError as exc:  # pragma: no cover - srodowisko bez GPU (PC ZW)
            raise RuntimeError(
                "Brak onnxruntime. Zainstaluj na PC z GPU: `pip install -e \".[gpu]\"`."
            ) from exc
        _enable_cuda_dlls()  # Windows: udostepnij CUDA/cuDNN z pakietu torch (cu121)
        self._session = ort.InferenceSession(self._model_path, providers=PROVIDERS)
        inp = self._session.get_inputs()[0]
        self._input_name = inp.name
        # Auto-rozmiar wejscia z modelu ONNX (statyczny) — chroni przed niezgodnoscia
        # imgsz miedzy modelem a runtime (np. model 640 vs yolo_imgsz 1280).
        shape = list(inp.shape or [])
        if len(shape) == 4 and isinstance(shape[2], int) and isinstance(shape[3], int):
            self._imgsz = int(shape[2])
        # KLUCZOWE: nazwy klas czytamy z metadanych MODELU (ultralytics zapisuje 'names'),
        # nie z globalnego symbol-classes.yaml — inaczej indeksy klas modelu mapuja sie
        # na zla liste, gdy plik zostal nadpisany przez pozniejszy eksport.
        names = self._names_from_model()
        if names:
            self._id_to_name = names
        return self._session

    def _names_from_model(self) -> dict[int, str]:
        try:
            meta = self._session.get_modelmeta().custom_metadata_map or {}
            raw = meta.get("names")
            if not raw:
                return {}
            import ast

            parsed = ast.literal_eval(raw)
            if isinstance(parsed, dict):
                return {int(k): str(v) for k, v in parsed.items()}
        except Exception:
            pass
        return {}

    def _letterbox(self, image: np.ndarray):
        """Letterbox jak w ultralytics: jednolita skala, WYSRODKOWANE, szare (114) tlo.

        Zwraca (blob, scale, pad_left, pad_top) do odwzorowania detekcji na oryginal.
        """
        size = self._imgsz
        h, w = image.shape[:2]
        scale = size / max(h, w)
        new_w, new_h = int(round(w * scale)), int(round(h * scale))
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        canvas = np.full((size, size, 3), 114, dtype=np.uint8)
        pad_left = (size - new_w) // 2
        pad_top = (size - new_h) // 2
        canvas[pad_top:pad_top + new_h, pad_left:pad_left + new_w] = resized
        rgb = canvas[:, :, ::-1]  # BGR -> RGB
        blob = rgb.transpose(2, 0, 1)[np.newaxis].astype(np.float32) / 255.0
        return np.ascontiguousarray(blob), scale, pad_left, pad_top

    def detect(
        self,
        image_path: str,
        conf_threshold: float | None = None,
        iou_threshold: float = 0.45,
    ) -> list[SymbolDetection]:
        """Zwraca bbox (w pikselach oryginalu) + class_id + confidence dla strony PNG."""
        if conf_threshold is None:
            conf_threshold = yolo_conf_threshold()
        image = load_bgr(image_path)
        return self._filter_excluded(
            dedup_detections_by_row(
                self._infer_bgr(image, conf_threshold, iou_threshold)
            )
        )

    def detect_tiled(
        self,
        image_path: str,
        win: int = 1536,
        overlap: float = 0.2,
        conf_threshold: float | None = None,
        iou_threshold: float = 0.45,
    ) -> list[SymbolDetection]:
        """Inferencja przesuwnym oknem (dla wielkich stron). Parowane z tiled_export."""
        from train.tiled_export import nms, windows

        if conf_threshold is None:
            conf_threshold = yolo_conf_threshold()
        image = load_bgr(image_path)
        H, W = image.shape[:2]
        dets: list[SymbolDetection] = []
        for (x0, y0, x1, y1) in windows(W, H, win, overlap):
            crop = image[y0:y1, x0:x1]
            for d in self._infer_bgr(crop, conf_threshold, iou_threshold):
                dets.append(d.model_copy(update={"x": d.x + x0, "y": d.y + y0}))
        if not dets:
            return []
        boxes = [(d.x, d.y, d.width, d.height) for d in dets]
        keep = nms(boxes, [d.confidence for d in dets], iou_threshold)
        return self._filter_excluded(
            dedup_detections_by_row([dets[i] for i in keep])
        )

    def _filter_excluded(self, detections: list[SymbolDetection]) -> list[SymbolDetection]:
        excluded = yolo_runtime_exclude_classes()
        if not excluded:
            return detections
        return [d for d in detections if d.class_name not in excluded]

    def _infer_bgr(self, image, conf_threshold: float, iou_threshold: float):
        """Rdzen inferencji na tablicy BGR -> detekcje w pikselach TEJ tablicy."""
        session = self._ensure_session()
        h0, w0 = image.shape[:2]

        blob, scale, pad_left, pad_top = self._letterbox(image)
        input_name = self._input_name or session.get_inputs()[0].name
        outputs = session.run(None, {input_name: blob})
        preds = np.asarray(outputs[0])

        # YOLOv8: (1, 4+nc, N) -> (N, 4+nc)
        preds = np.squeeze(preds, axis=0).T
        if preds.size == 0:
            return []
        boxes_xywh = preds[:, :4]
        class_scores = preds[:, 4:]
        class_ids = class_scores.argmax(axis=1)
        confidences = class_scores.max(axis=1)

        keep = confidences >= conf_threshold
        boxes_xywh = boxes_xywh[keep]
        class_ids = class_ids[keep]
        confidences = confidences[keep]
        if len(boxes_xywh) == 0:
            return []

        # (cx, cy, w, h) w przestrzeni letterboxa -> (x, y, w, h) w oryginale
        # (odejmij padding, podziel przez skale)
        xs = (boxes_xywh[:, 0] - boxes_xywh[:, 2] / 2 - pad_left) / scale
        ys = (boxes_xywh[:, 1] - boxes_xywh[:, 3] / 2 - pad_top) / scale
        ws = boxes_xywh[:, 2] / scale
        hs = boxes_xywh[:, 3] / scale

        nms_boxes = [[float(x), float(y), float(w), float(h)] for x, y, w, h in zip(xs, ys, ws, hs)]
        indices = cv2.dnn.NMSBoxes(
            nms_boxes, confidences.tolist(), conf_threshold, iou_threshold
        )
        if len(indices) == 0:
            return []

        detections: list[SymbolDetection] = []
        for i in np.asarray(indices).flatten():
            cid = int(class_ids[i])
            detections.append(
                SymbolDetection(
                    class_id=cid,
                    class_name=self._id_to_name.get(cid, str(cid)),
                    confidence=float(confidences[i]),
                    x=max(0.0, float(xs[i])),
                    y=max(0.0, float(ys[i])),
                    width=float(ws[i]),
                    height=float(hs[i]),
                )
            )
        return detections
