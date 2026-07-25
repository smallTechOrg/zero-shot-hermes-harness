"""Unit tests for session and upload service."""
from __future__ import annotations

import time

import pytest

from src.services.session_service import SessionService
from src.domain.session import DataSource, SessionCreateRequest


@pytest.fixture()
def service(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_DATABASE_URL", f"sqlite:///{tmp_path}/app.db")
    from src.db.session import init_db
    init_db()
    return SessionService()


def test_create_and_get_session(service):
    req = SessionCreateRequest(name="Ops Alpha", default_data_source=DataSource.hybrid)
    created = service.create_session(req)
    assert created.session_id
    assert created.name == "Ops Alpha"
    assert created.state.value == "active"
    assert created.default_data_source == DataSource.hybrid

    fetched = service.get_session(created.session_id)
    assert fetched is not None
    assert fetched.session_id == created.session_id
    assert fetched.table_count == 0


def test_add_upload_updates_table_count(service):
    req = SessionCreateRequest(name="Ops Beta")
    created = service.create_session(req)
    record = service.add_upload(created.session_id, _record("fir.csv", "fir", 10, 5, 1024))
    assert record.row_count == 10

    summary = service.get_session(created.session_id)
    assert summary.table_count == 1


def test_list_sessions_sorted_by_updated(service):
    s1 = service.create_session(SessionCreateRequest(name="Alpha"))
    s2 = service.create_session(SessionCreateRequest(name="Beta"))
    time.sleep(0.05)
    service.add_upload(s2.session_id, _record("t.csv", "t", 1, 1, 10))
    rows = service.list_sessions()
    names = [r.name for r in rows]
    assert "Alpha" in names
    assert "Beta" in names


def _record(filename, table_name, row_count, columns_count, size):
    from src.domain.upload import UploadRecord
    return UploadRecord(
        filename=filename,
        table_name=table_name,
        row_count=row_count,
        columns_count=columns_count,
        bytes=size,
    )
