"""Graph assembly — conditional baseline transform or analyst query mode."""
from __future__ import annotations

from langgraph.graph import END, StateGraph

from src.graph.edges import after_execute_tool, after_plan_query
from src.graph.nodes import (
    execute_tool,
    finalize,
    finalize_transform,
    handle_error,
    plan_query,
    plan_transform,
)
from src.graph.state import AgentState


def _build_graph(session_id: str = ""):
    g = StateGraph(AgentState)
    g.add_node("plan_query", plan_query)
    g.add_node("execute_tool", execute_tool)
    g.add_node("finalize", finalize)
    g.add_node("handle_error", handle_error)
    g.add_node("plan_transform", plan_transform)
    g.add_node("finalize_transform", finalize_transform)

    def _route_initial(state: AgentState) -> str:
        try:
            from src.db.duckdb_store import get_schema as cache_schema

            tables = cache_schema(session_id or state.get("session_id") or "")
            if tables:
                return "plan_query"
        except Exception:
            pass
        return "plan_transform"

    def _route_transform(state: AgentState) -> str:
        return "handle_error" if state.get("error") else "finalize_transform"

    g.set_conditional_entry_point(_route_initial)
    g.add_conditional_edges(
        "plan_transform",
        _route_transform,
        {"finalize_transform": "finalize_transform", "handle_error": "handle_error"},
    )
    g.add_edge("finalize_transform", END)
    g.add_conditional_edges(
        "plan_query",
        after_plan_query,
        {"execute_tool": "execute_tool", "handle_error": "handle_error"},
    )
    g.add_conditional_edges(
        "execute_tool",
        after_execute_tool,
        {"finalize": "finalize", "handle_error": "handle_error"},
    )
    g.add_edge("finalize", END)
    g.add_edge("handle_error", END)
    return g.compile()


agentic_ai = _build_graph()
