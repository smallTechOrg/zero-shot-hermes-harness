"""
Domain models (Pydantic request/response shapes).
"""
from src.domain.run import QueryResponse, RunRequest, RunResult

__all__ = ["RunRequest", "RunResult", "QueryResponse"]
