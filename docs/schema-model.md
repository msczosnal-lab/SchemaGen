# SchemaModel

Centralny kontrakt JSON — wszystkie moduly (labeler, CLI, API, web) uzywaja tego samego formatu.

## Pliki

- JSON Schema: `schema/schema-model.json`
- Pydantic: `backend/models/schema.py`
- Fixture GT: `schema/fixtures/page1_expected.json`

## Pola kluczowe

- `components[]` — id, type, tag, bbox, confidence, source
- `connections[]` — from, to, potential, kind
- `user_intent` — drive_type, power_kw (z formularza lub XML)
- `meta.model_version` — wersja ONNX uzyta przy recognize

## LabelRecord → SchemaModel

Labeler eksportuje oba formaty przez `labeler/export.py`.
