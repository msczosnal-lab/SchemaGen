# COWORK_TASK: sync/prompts/001-symbol-detector.md

"""Detekcja symboli — YOLOv8 ONNX na RTX 2080 (offline, bez cloud API)."""

from __future__ import annotations

import cv2
import numpy as np

from backend.ingest.image_utils import load_bgr, resize_for_yolo
from backend.models.detection import SymbolDetection
from backend.runtime_config import yolo_conf_threshold, yolo_imgsz
PROVIDERS = ["CUDAExecutionProvider", "CPUExecutionProvider"]


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
        self._session = ort.InferenceSession(self._model_path, providers=PROVIDERS)
        self._input_name = self._session.get_inputs()[0].name
        return self._session

    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        canvas = resize_for_yolo(image, self._imgsz)
        rgb = canvas[:, :, ::-1]  # BGR -> RGB
        blob = rgb.transpose(2, 0, 1)[np.newaxis].astype(np.float32) / 255.0
        return np.ascontiguousarray(blob)

    def detect(
        self,
        image_path: str,
        conf_threshold: float | None = None,
        iou_threshold: float = 0.45,
    ) -> list[SymbolDetection]:
        """Zwraca bbox (w pikselach oryginalu) + class_id + confidence dla strony PNG."""
        if conf_threshold is None:
            conf_threshold = yolo_conf_threshold()
        session = self._ensure_session()
        image = load_bgr(image_path)
        h0, w0 = image.shape[:2]
        scale = self._imgsz / max(h0, w0)  # resize_for_yolo: top-left, jednolita skala

        blob = self._preprocess(image)
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

        # (cx, cy, w, h) w przestrzeni imgsz -> (x, y, w, h) top-left w oryginale
        xs = (boxes_xywh[:, 0] - boxes_xywh[:, 2] / 2) / scale
        ys = (boxes_xywh[:, 1] - boxes_xywh[:, 3] / 2) / scale
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
