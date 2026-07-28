"""Graph assembly — StateGraph compiled once at import."""
from __future__ import annotations

from langgraph.graph import END, StateGraph

from src.graph.edges import after_transform
from src.graph.nodes import (
    execute_query,
    finalize,
    handle_error,
    prepare_exports,
    recommend_chart,
    render_answer,
    render_chart,
    suggest_followups,
    transform_text,
)
from src.graph.state import AgentState


def _build_graph():
    g = StateGraph(AgentState)
    g.add_node("transform_text", transform_text)
    g.add_node("handle_error", handle_error)
    g.add_node("finalize", finalize)
    g.set_entry_point("transform_text")
    g.add_conditional_edges(
        "transform_text",
        after_transform,
        {"finalize": "finalize", "handle_error": "handle_error"},
    )
    g.add_edge("finalize", END)
    g.add_edge("handle_error", END)
    return g.compile()


agentic_ai = _build_graph()
