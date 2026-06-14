# Frontend SchemaGen (Faza 5)

Docelowo Next.js localhost — ten sam FastAPI backend co labeler.

## MVP

Uzyj labelera vanilla: `python -m labeler.app` → http://localhost:8765

## Przyszlosc

```bash
# Po inicjalizacji Next.js:
cd frontend
npm install
npm run dev   # proxy /api -> localhost:8780
```

Kontrakt API: `SchemaModel` JSON — bez zmian przy migracji UI.
