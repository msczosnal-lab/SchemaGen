# Atlas symboli — setup lokalny

## Wymagania

- Python 3.11+ z `pillow` (`pip install pillow`)
- Git (do klonowania QET)

## Krok 1 — klonowanie biblioteki QET

```bash
git clone --depth 1 https://github.com/qelectrotech/qelectrotech-elements.git data/atlas/qet
```

Katalog `data/atlas/qet/` jest w `.gitignore` — nie trafi do repo (~115 MB, licencja GPL).

## Krok 2 — budowanie atlasu

```bash
python -m backend.atlas.build_reference \
    --qet-dir data/atlas/qet \
    --out config/symbol-reference.yaml \
    --crops-dir data/atlas/crops
```

Opcje:
- `--max-symbols 120` — limit wpisow (domyslnie 120)
- `--no-manufacturers` — pomija P2 (katalog producentow)
- `--dry-run` — podglad bez zapisu plikow

## Krok 3 — commit

```bash
git add config/symbol-reference.yaml data/atlas/crops/
git commit -m "[Claude] atlas: QET extract → symbol-reference.yaml (prompt 008a)"
```

## Struktura

| Sciezka | Zawartosc |
|---------|-----------|
| `data/atlas/qet/` | Raw biblioteka QET (poza gitem) |
| `data/atlas/crops/*.png` | Crop-y PNG symboli (128×128, commitujemy) |
| `config/symbol-reference.yaml` | Kanoniczny slownik symboli (commitujemy) |

## Licencja QET

Biblioteka qelectrotech-elements: GNU/GPL.  
Crop-y i YAML to atrybucja pochodna — zachowaj link do repo QET w `symbol-reference.yaml`.
