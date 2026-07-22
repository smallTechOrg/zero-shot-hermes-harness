"""Admin routes — audit log review (Phase 3)."""
from __future__ import annotations

from fastapi import APIRouter

from src.api._common import ok
from src.db.models import RunRow
from src.db.session import get_session

router = APIRouter()


@router.get("/audit/logs")
def audit_logs() -> dict:
    with get_session() as session:
        rows = session.query(RunRow).order_by(RunRow.created_at.desc()).limit(50).all()
        data = [
            {
                "run_id": row.id,
                "status": row.status,
                "provider": row.provider,
                "model": row.model,
                "error_message": row.error_message,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]
    return ok({"items": data})


@router.get("/reports/quality")
def quality_report() -> dict:
    return ok({"message": "quality report placeholder"})
