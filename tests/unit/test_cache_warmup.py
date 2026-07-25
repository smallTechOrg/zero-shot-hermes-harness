"""warmup_cache tests — refresh + optional view creation."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.db.cache_sync import refresh_cache, warmup_cache


def test_warmup_refreshes_and_creates_views():
    mock_stats = {"tables_synced": 1, "total_rows": 10, "elapsed_ms": 5}

    mock_con = MagicMock()
    mock_con.__enter__ = MagicMock(return_value=mock_con)
    mock_con.__exit__ = MagicMock(return_value=False)

    def mock_execute(sql, *args, **kwargs):
        result = MagicMock()
        if "SHOW TABLES" in sql:
            result.fetchall.return_value = [("users",)]
        elif "PRAGMA table_info" in sql:
            result.fetchall.return_value = [
                (0, "id", "INTEGER", False, None, False),
                (1, "name", "VARCHAR", False, None, False),
                (2, "created_at", "TIMESTAMP", False, None, False),
            ]
        else:
            result.fetchall.return_value = []
        return result

    mock_con.execute.side_effect = mock_execute

    with patch("src.db.cache_sync.refresh_cache", return_value=mock_stats), patch(
        "src.db.cache_sync.duckdb.connect", return_value=mock_con
    ), patch("src.db.cache_sync._lock"):
        out = warmup_cache("sess1")

    assert out["tables_synced"] == 1
    assert out["total_rows"] == 10
    assert out.get("views_created", 0) >= 1, f"views_created missing or zero: {out}"
    assert "elapsed_ms" in out
