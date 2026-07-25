"""Session service: CRUD over analyst sessions and upload metadata."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select

from src.db.models import Base
from src.db.session import create_db_session
from src.db.session_models import Session as SessionRow
from src.db.session_models import UploadRecordRow
from src.domain.session import SessionCreateRequest, SessionState, SessionSummary
from src.domain.upload import UploadRecord


class SessionService:
    def create_session(self, req: SessionCreateRequest) -> SessionSummary:
        session_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        row = SessionRow(
            id=session_id,
            name=req.name,
            state=SessionState.active.value,
            default_data_source=req.default_data_source.value,
            table_count=0,
        )
        with create_db_session() as db:
            db.add(row)
        return SessionSummary(
            session_id=session_id,
            name=req.name,
            state=SessionState.active,
            default_data_source=req.default_data_source,
            table_count=0,
            last_activity=now,
        )

    def get_session(self, session_id: str) -> SessionSummary | None:
        with create_db_session() as db:
            row = db.get(SessionRow, session_id)
            if not row:
                return None
            return _to_summary(row)

    def list_sessions(self) -> list[SessionSummary]:
        with create_db_session() as db:
            rows = db.execute(select(SessionRow).order_by(SessionRow.updated_at.desc())).scalars().all()
            return [_to_summary(row) for row in rows]

    def touch_session(self, session_id: str) -> None:
        with create_db_session() as db:
            row = db.get(SessionRow, session_id)
            if row:
                row.updated_at = datetime.now(timezone.utc)
                db.add(row)

    def add_upload(self, session_id: str, rec: UploadRecord) -> UploadRecord:
        row = UploadRecordRow(
            id=str(uuid4()),
            session_id=session_id,
            filename=rec.filename,
            table_name=rec.table_name,
            row_count=rec.row_count,
            columns_count=rec.columns_count,
            bytes=rec.bytes,
            mime_type=rec.mime_type,
            status=rec.status,
            message=rec.message,
        )
        with create_db_session() as db:
            db.add(row)
            self._increment_table_count(db, session_id)
        return rec

    def _increment_table_count(self, db, session_id: str) -> None:
        row = db.get(SessionRow, session_id)
        if row:
            row.table_count = (row.table_count or 0) + 1


def _to_summary(row: SessionRow) -> SessionSummary:
    return SessionSummary(
        session_id=row.id,
        name=row.name,
        state=SessionState(row.state),
        default_data_source=row.default_data_source,
        table_count=row.table_count or 0,
        last_activity=row.updated_at.isoformat() if row.updated_at else None,
    )
