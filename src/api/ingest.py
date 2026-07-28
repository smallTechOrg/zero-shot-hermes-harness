"""Ingest API — POST /ingest uploads CSV/Excel files into DuckDB."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse

from src.api._common import api_error, ok
from src.tools.duckdb_tools import build_connector, open_csv, open_excel
from src.config.settings import get_settings


router = APIRouter()


@router.post("/ingest")
def ingest_files(files: list[UploadFile] = File(...)) -> JSONResponse:
    if not files:
        raise api_error("no_files", "Upload at least one CSV or Excel file.", 422)

    connector = build_connector(get_settings().database_url)
    uploaded: list[dict[str, Any]] = []

    for upload in files:
        name = upload.filename or "upload"
        suffix = Path(name).suffix.lower()
        tmp_path = Path("data") / ("upload_" + name)
        tmp_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path.write_bytes(upload.file.read())

        table_name = _safe_name(name)
        try:
            if suffix == ".csv":
                meta = open_csv(tmp_path, table_name, connector)
            elif suffix in {".xlsx", ".xls"}:
                meta = open_excel(tmp_path, table_name, connector)
            else:
                raise ValueError(f"Unsupported file type: {suffix}")
        except Exception as exc:
            raise api_error("ingest_failed", f"Failed to ingest {name}: {exc}", 400) from exc
        finally:
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass

        uploaded.append(
            {
                "file": name,
                "table": table_name,
                "rows": meta.row_count,
                "columns": [c["name"] for c in meta.columns],
            }
        )

    try:
        connector.close()
    except Exception:
        pass

    return ok({"files": uploaded})


def _safe_name(name: str) -> str:
    stem = Path(name).stem
    safe = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in stem)
    return safe or "upload"
