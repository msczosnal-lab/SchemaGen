# 025 — audyt integralności GT (A1)

Plików `gt/*.json`: **6** · CRIT: **1** · WARN: 12 · INFO: 1

## Strony

| page_id | symbole | linie |
|---|---:|---:|
| 22_A_153_PL_Adamed_AGV_SA2_20250706_p028 | 49 | 42 |
| 22_A_153_PL_Adamed_AGV_SA2_20250706_p029 | 94 | 76 |
| 22_A_153_PL_Adamed_AGV_SA2_20250706_p030 | 14 | 8 |
| 22_A_153_PL_Adamed_AGV_SA2_20250706_p031 | 1 | 0 |
| 22_A_153_PL_Adamed_AGV_SA2_20250706_p033 | 155 | 117 |
| 22_A_153_PL_Adamed_AGV_SA2_20250706_p034 | 108 | 0 |

## Znaleziska

| Sev | Kod | Strona | Opis |
|---|---|---|---|
| CRIT | `db_hot_journal` | - | Leży schemagen.db-journal (4616 B) — baza po nieczystym zamknięciu (rollback przy następnym otwarciu). Tryb DELETE, nie WAL. |
| WARN | `cache_table_missing` | - | Baza nie ma tabeli schematic_graph (tabele: ['annotations', 'model_versions', 'pages', 'tag_usage']) — init_db + rebuild odtworzy ze źródła |
| WARN | `png_missing` | 22_A_153_PL_Adamed_AGV_SA2_20250706_p028 | Brak PNG w data/raw/ — nie da się zweryfikować skali GT |
| WARN | `png_missing` | 22_A_153_PL_Adamed_AGV_SA2_20250706_p029 | Brak PNG w data/raw/ — nie da się zweryfikować skali GT |
| WARN | `png_missing` | 22_A_153_PL_Adamed_AGV_SA2_20250706_p030 | Brak PNG w data/raw/ — nie da się zweryfikować skali GT |
| WARN | `png_missing` | 22_A_153_PL_Adamed_AGV_SA2_20250706_p031 | Brak PNG w data/raw/ — nie da się zweryfikować skali GT |
| WARN | `png_missing` | 22_A_153_PL_Adamed_AGV_SA2_20250706_p033 | Brak PNG w data/raw/ — nie da się zweryfikować skali GT |
| WARN | `png_missing` | 22_A_153_PL_Adamed_AGV_SA2_20250706_p034 | Brak PNG w data/raw/ — nie da się zweryfikować skali GT |
| WARN | `val_page_without_gt` | 22_A_153_PL_Adamed_AGV_SA2_20250706_p025 | Strona z val-pages.yaml nie ma pliku gt/*.json |
| WARN | `val_page_without_gt` | 22_A_153_PL_Adamed_AGV_SA2_20250706_p035 | Strona z val-pages.yaml nie ma pliku gt/*.json |
| WARN | `val_page_without_gt` | 22_A_153_PL_Adamed_AGV_SA2_20250706_p040 | Strona z val-pages.yaml nie ma pliku gt/*.json |
| WARN | `val_page_without_gt` | 22_A_153_PL_Adamed_AGV_SA2_20250706_p045 | Strona z val-pages.yaml nie ma pliku gt/*.json |
| WARN | `val_page_without_gt` | 22_A_153_PL_Adamed_AGV_SA2_20250706_p050 | Strona z val-pages.yaml nie ma pliku gt/*.json |
| INFO | `gt_backup_dirs` | - | Podkatalogi w gt/: ['_backup_2026-07-12'] — glob('*.json') ich NIE łapie (6 plików w podkatalogach pominiętych). OK. |
