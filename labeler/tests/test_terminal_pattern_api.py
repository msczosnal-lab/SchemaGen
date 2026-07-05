"""Testy API labelera — terminale i wzorce."""

from fastapi.testclient import TestClient

from labeler.app import app

client = TestClient(app)


def test_terminal_config_endpoint():
    res = client.get("/api/terminal-config")
    assert res.status_code == 200
    data = res.json()
    assert "contact_tol_frac" in data
    assert "contact_tol_min" in data


def test_save_terminal_pattern_from_bboxes(tmp_path, monkeypatch):
    from backend.recognize import terminal_patterns_io as tpio

    path = tmp_path / "terminal-patterns.yaml"
    monkeypatch.setattr(tpio, "TERMINAL_PATTERNS_PATH", path)

    res = client.post(
        "/api/save-terminal-pattern",
        json={
            "class_name": "zlaczka",
            "bboxes": [
                {
                    "class_name": "zlaczka",
                    "tag": "",
                    "terminals": [{"id": "1", "x": 0.0, "y": 0.5}, {"id": "2", "x": 1.0, "y": 0.5}],
                },
            ],
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["class_name"] == "zlaczka"
    assert body["sample_count"] == 1
    loaded = tpio.load_patterns(path)
    assert "zlaczka" in loaded["classes"]
