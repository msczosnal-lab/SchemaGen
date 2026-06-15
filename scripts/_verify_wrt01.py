"""Weryfikacja stanu WRT01 po resecie."""
import sqlite3
from pathlib import Path

db = Path("data/schemagen.db")
c = sqlite3.connect(db)
w = c.execute(
    "SELECT status, COUNT(*) FROM pages WHERE id LIKE 'SchematWRT01%' GROUP BY status"
).fetchall()
ann = c.execute(
    "SELECT COUNT(*) FROM annotations WHERE page_id LIKE 'SchematWRT01%'"
).fetchone()[0]
print("WRT01 page status:", w)
print("WRT01 annotations:", ann)
