"""Edges for the data analyst agent graph."""
from __future__ import annotations


def route_from_plan(state):
    if state.get("error"):
        return "handle_error"
    return "generate_sql"


def route_from_sql(state):
    if state.get("sql_error"):
        return "handle_error"
    return "execute_query"


def route_from_execute(state):
    if state.get("sql_error"):
        return "handle_error"
    if state.get("error"):
        return "handle_error"
    return "render_answer"


def route_from_render(state):
    if state.get("error"):
        return "handle_error"
    return "recommend_chart"


def route_from_recommend(state):
    if state.get("error"):
        return "handle_error"
    return "render_chart"


def route_from_chart(state):
    if state.get("error"):
        return "handle_error"
    return "suggest_followups"


def route_from_suggest(state):
    if state.get("error"):
        return "handle_error"
    return "prepare_exports"


def route_from_exports(state):
    if state.get("error"):
        return "handle_error"
    return "finalize"


def after_transform(state):
    if state.get("error"):
        return "handle_error"
    return "finalize"
