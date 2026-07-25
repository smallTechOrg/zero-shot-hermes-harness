"""
Upload record: metadata for a single uploaded CSV file in a session.

The ingest route writes these records so the frontend can show the
upload queue, table mappings, and last-refreshed timestamps.
"""
from __future__ import annotations

from pydantic import BaseModel


class UploadRecord(BaseModel):
    filename: str
    table_name: str
    row_count: int | None = None
    columns_count: int | None = None
    bytes: int | None = None
    mime_type: str = "text/csv"
    status: str = "uploaded"
    message: str | None = None
    source: str = "csv"
