from fastapi.testclient import TestClient

from backend.db import load_schematic_graph
from labeler.app import app

client = TestClient(app)
pid = "22_A_153_PL_Adamed_AGV_SA2_20250706_p027"
raw = load_schematic_graph(pid)
print("raw line keys:", list(raw["lines"][0].keys()))
r = client.get(f"/api/graph/{pid}")
body = r.json()
print("api line keys:", list(body["lines"][0].keys()))
line0 = body["lines"][0]
print("from:", line0.get("from"))
print("from_ref:", line0.get("from_ref"))

# Simulate JS normalize
for l in body["lines"]:
    from_ = l.get("from") or l.get("from_ref")
    to = l.get("to") or l.get("to_ref")
    print(l["id"], "from_ok=", bool(from_), "to_ok=", bool(to))
