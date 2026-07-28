"""Baseline graph tests, adapted to the merged analyst/backward-compat graph."""
from fastapi.testclient import TestClient

from src.api import create_app
from src.graph.agent import agentic_ai
from src.graph.edges import after_transform
from src.graph.nodes import transform_text


def _styles_css_in(text: str) -> bool:
    return 'href="styles.css"' in text or "href='/app/styles.css'" in text


def test_graph_compiles_without_env():
    assert agentic_ai is not None
    nodes = set(agentic_ai.get_graph().nodes)
    assert {"transform_text", "handle_error", "finalize", "__end__"} <= nodes
    assert after_transform({"error": "boom"}) == "handle_error"
    assert after_transform({"error": None}) == "finalize"


def test_transform_node_surfaces_missing_key_as_error(no_keys):
    out = transform_text({"input_text": "hi", "instruction": "upper"})
    assert out is not None
    assert isinstance(out, dict)
    assert out.get("error") is not None
    assert "AGENT_" in out["error"]
    assert out.get("status") == "failed"


def test_frontend_served_at_app(no_keys):
    with TestClient(create_app()) as client:
        res = client.get("/app/")
        assert res.status_code == 200
        assert _styles_css_in(res.text)
        assert "app.js" in res.text
