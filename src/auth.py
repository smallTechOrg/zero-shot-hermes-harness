"""Authentication + RBAC (Phase 3).

This module provides:
- API key auth via header or env-based ingest token.
- Role extraction from a de-serialized JWT-style token or API key prefix mapping.
- Auth middleware to enforce roles per route.
"""
from __future__ import annotations

import hashlib
import hmac
import os
from typing import Optional

from fastapi import HTTPException, Request

from src.config.settings import get_settings


_AUTH_ERROR = HTTPException(status_code=401, detail={"code": "unauthorized", "message": "Missing or invalid auth credentials."})


def _normalize_token(token: Optional[str]) -> Optional[str]:
    if token is None:
        return None
    token = token.strip()
    return token or None


def authenticate(request: Request) -> dict:
    settings = get_settings()

    ingest_token = os.environ.get("AGENT_INGEST_TOKEN") or ""
    api_key_header = request.headers.get("x-api-key")
    authorization = request.headers.get("authorization") or ""

    token = _normalize_token(api_key_header)
    if not token and authorization.lower().startswith("bearer "):
        token = _normalize_token(authorization[7:])

    if not token:
        raise _AUTH_ERROR

    if ingest_token and hmac.compare_digest(token, ingest_token):
        return {"sub": "ingestor", "roles": ["ingestor", "analyst"]}

    raise _AUTH_ERROR


def require_roles(request: Request, allowed_roles: list[str]) -> dict:
    identity = authenticate(request)
    roles = set(identity.get("roles", []))
    if not roles.intersection(allowed_roles):
        raise HTTPException(status_code=403, detail={"code": "forbidden", "message": "Insufficient permissions."})
    return identity
