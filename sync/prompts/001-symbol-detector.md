# Zadanie: OnnxSymbolDetector.detect

## Plik: backend/recognize/symbol_detector.py
## Zaleznosci: onnxruntime-gpu, backend/ingest/image_utils.py

## Implementuj:

1. Session ONNX providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
2. Preprocess przez resize_for_yolo
3. NMS, map class_id → SymbolDetection

## Test: pytest backend/tests/test_symbol_detector.py (utworz)
## Fixture: schema/fixtures/page1_expected.json
## NIE uzywaj: openai, anthropic, cloud API
