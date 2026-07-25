"""Ingest routes — multipart /ingest and typed /ingest/json for CSV uploads."""
from __future__ import annotations

import csv
from typing import Any, Literal

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from src.api._common import ok
from src.db.duckdb_store import get_schema, init_session, ingest_csv
from src.domain.upload import UploadRecord

router = APIRouter()


class TableMap(BaseModel):
    filename: str
    table_name: str


class IngestRequest(BaseModel):
    session_id: str = "sess1"
    source: Literal["csv", "live"] = "csv"
    files: list[UploadFile] | None = None
    table_map: list[TableMap] | None = None


class IngestResponse(BaseModel):
    session_id: str
    session_name: str
    tables: list[dict[str, Any]]
    uploads: list[UploadRecord]
    schema_markdown: str


def _safe_table_name(filename: str) -> str:
    name = filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1].rsplit(".", 1)[0]
    name = "".join(c if (c.isalnum() or c == "_") else "_" for c in name) or "t"
    return name.lower()


def _validate_csv(headers: bytes) -> None:
    try:
        sample = headers[: 8 * 1024].decode("utf-8", errors="replace")
        if not sample.strip():
            return
        csv.Sniffer().sniff(sample)
    except csv.Error:
        raise HTTPException(
            status_code=415,
            detail="Uploaded file does not look like a CSV.",
        )


def _resolve_table_name(filename: str, table_map: list[TableMap] | None) -> str:
    if table_map:
        mapping = next((m for m in table_map if m.filename == filename), None)
        if mapping:
            return mapping.table_name
    return _safe_table_name(filename)


async def _ingest_file(
    session_id: str,
    upload: UploadFile,
    table_map: list[TableMap] | None,
) -> tuple[dict[str, Any], UploadRecord]:
    data = await upload.read()
    filename = upload.filename or "upload.csv"
    _validate_csv(data)
    table_name = _resolve_table_name(filename, table_map)
    info = ingest_csv(session_id, table_name, data)
    table_kind = {
        "name": table_name,
        "row_count": info.get("row_count", 0),
        "columns": info.get("columns", []),
    }
    record = UploadRecord(
        filename=filename,
        table_name=table_name,
        row_count=info.get("row_count"),
        columns_count=len(info.get("columns", [])),
        bytes=len(data),
    )
    return table_kind, record


@router.post("/ingest")
async def ingest_files(
    session_id: str = Form("sess1"),
    source: Literal["csv", "live"] = Form("csv"),
    files: list[UploadFile] = File(...),
    table_map_json: str | None = Form(None),
) -> dict:
    if not files:
        raise HTTPException(status_code=422, detail="Upload at least one CSV file.")

    table_map: list[TableMap] | None = None
    if table_map_json:
        import json
        try:
            table_map = [TableMap(**item) for item in json.loads(table_map_json)]
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Invalid table_map JSON: {exc}")

    init_session(session_id)

    tables: list[dict[str, Any]] = []
    uploads: list[UploadRecord] = []
    for upload in files:
        table_info, record = await _ingest_file(session_id, upload, table_map)
        tables.append(table_info)
        uploads.append(record)

    schema = get_schema(session_id)
    schema_md = _schema_to_text(schema)
    response = IngestResponse(
        session_id=session_id,
        session_name="Imported CSVs",
        tables=tables,
        uploads=uploads,
        schema_markdown=schema_md,
    )
    return ok(response.dict())


@router.post("/ingest/json")
async def ingest_json(req: IngestRequest) -> dict:
    if not req.files:
        raise HTTPException(status_code=422, detail="No files provided in request.")

    init_session(req.session_id)

    tables: list[dict[str, Any]] = []
    uploads: list[UploadRecord] = []
    for upload in req.files:
        table_info, record = await _ingest_file(req.session_id, upload, req.table_map)
        tables.append(table_info)
        uploads.append(record)

    schema = get_schema(req.session_id)
    schema_md = _schema_to_text(schema)
    response = IngestResponse(
        session_id=req.session_id,
        session_name="Imported CSVs",
        tables=tables,
        uploads=uploads,
        schema_markdown=schema_md,
    )
    return ok(response.dict())


def _schema_to_text(tables: list[dict[str, Any]]) -> str:
    lines = []
    for t in tables:
        cols = ", ".join(f"{c['name']} ({c['type']})" for c in t["columns"])
        lines.append(f"{t['name']} — {t['row_count']} rows: {cols}")
    return "\n".join(lines) or "(no tables)"
