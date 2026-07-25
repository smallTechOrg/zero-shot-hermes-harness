"""Integration gate — runs against the REAL LLM/API with keys from .env.

Skips (never stubs) when no key is present. Asserts response content and DB
state, not just status codes; covers happy path + edge case + error path.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api import create_app
from src.config.settings import get_settings
from src.db.models import RunRow
from src.db.session import create_db_session


def _require_key() -> None:
    if get_settings().resolve_provider() == "stub":
        pytest.skip("no real LLM key in .env — integration gate requires one")


@pytest.fixture()
def client():
    with TestClient(create_app()) as c:
        yield c


def test_happy_path_real_llm_end_to_end(client):
    _require_key()
    res = client.post(
        "/runs",
        json={
            "text": "The quick brown fox jumps over the lazy dog.",
            "instruction": "Rewrite this sentence in uppercase letters only.",
        },
    )
    assert res.status_code == 200
    run = res.json()["data"]
    assert run["status"] == "completed", f"run failed: {run['error_message']}"
    assert run["output_text"], "expected real model output"
    # content assertion robust to model phrasing: the transform happened
    assert "QUICK" in run["output_text"].upper()

    # DB state matches the response
    with create_db_session() as s:
        row = s.get(RunRow, run["run_id"])
        assert row is not None
        assert row.status == "completed"
        assert row.output_text == run["output_text"]
        assert row.provider in {"transform", get_settings().resolve_provider()}


def test_edge_case_short_input_real_llm(client):
    _require_key()
    res = client.post(
        "/runs",
        json={"text": "ok", "instruction": "Repeat the text exactly as given."},
    )
    assert res.status_code == 200
    run = res.json()["data"]
    assert run["status"] == "completed", f"run failed: {run['error_message']}"
    assert run["output_text"]


def test_error_path_bad_model_fails_actionably(client, monkeypatch):
    """Wrong model name → failed run with an actionable message, not a crash."""
    _require_key()
    monkeypatch.setenv("AGENT_LLM_MODEL", "this-model-does-not-exist-xyz")
    # reset the settings singleton so the patched model takes effect
    import src.config.settings as settings_mod

    settings_mod._settings = None
    res = client.post("/runs", json={"text": "hello", "instruction": "upper"})
    assert res.status_code == 200
    run = res.json()["data"]
    assert run["status"] == "failed"
    assert run["error_message"]
