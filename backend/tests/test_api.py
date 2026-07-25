from pathlib import Path

from fastapi.testclient import TestClient

from app.config import get_settings


def test_generation_and_replay(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("ARTIFACTS_PATH", str(tmp_path / "artifacts"))
    get_settings.cache_clear()

    import importlib
    import app.main

    module = importlib.reload(app.main)
    client = TestClient(module.app)
    assert client.get("/health").json()["mode"] == "demo"

    created = client.post("/api/generations", json={"prompt": "A verified alpine product photo"}).json()
    assert created["status"] == "completed"
    assert len(created["asset_sha256"]) == 64
    assert len(created["manifest_sha256"]) == 64

    replayed = client.post(f"/api/generations/{created['id']}/replay", json={}).json()
    assert replayed["parent_id"] == created["id"]
    assert len(client.get("/api/generations").json()) == 2
