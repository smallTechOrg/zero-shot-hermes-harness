"""Server entry point: `uv run python -m src` (from the repo root)."""
from __future__ import annotations

import os

import uvicorn


def main() -> None:
    port = int(os.environ.get("PORT", "8001"))
    from src.api.__init__ import create_app
    uvicorn.run(create_app(), host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()
