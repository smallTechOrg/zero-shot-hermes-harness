"""warmup_cache endpoint tests."""
from __future__ import annotations

from fastapi.testclient import TestClient

from src.api import create_app
from src.api.routes_db import router

client = TestClient(create_app())


def _raise_db_down(session_id="sess1"):
    raise RuntimeError("db down")


def test_db_warmup_endpoint_returns_success(monkeypatch):
    monkeypatch.setattr("src.api.routes_db.warmup_cache", lambda session_id="sess1": {"tables_synced": 2, "views_created": ["vw_fir_type", "vw_district_counts"]})
    resp = client.post("/db/warmup?session_id=sess1")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["tables_synced"] >= 0
    assert "vw_fir_type" in data["views_created"]


def test_db_warmup_endpoint_failure_returns_server_error(monkeypatch):
    monkeypatch.setattr("src.api.routes_db.warmup_cache", _raise_db_down)
    resp = client.post("/db/warmup?session_id=sess1")
    assert resp.status_code == 500
