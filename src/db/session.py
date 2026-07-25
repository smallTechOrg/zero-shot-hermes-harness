"""
Database session management.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.config.settings import get_settings

_engine = None
_SessionLocal = None


def _get_engine():
  global _engine
  if _engine is None:
    _engine = create_engine(get_settings().database_url)
  return _engine


def _get_session_factory():
  global _SessionLocal
  if _SessionLocal is None:
    _SessionLocal = sessionmaker(bind=_get_engine())
  return _SessionLocal


@contextmanager
def create_db_session() -> Generator[Session, None, None]:
    session = _get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session() -> Generator[Session, None, None]:
  session = _get_session_factory()()
  try:
    yield session
    session.commit()
  except Exception:
    session.rollback()
    raise
  finally:
    session.close()


def init_db() -> None:
    from src.db.models import Base
    Base.metadata.create_all(bind=_get_engine())

    # Dev-time migration: SQLite `create_all` is non-destructive and won't add columns to existing tables.
    # This adds `latency_ms` if an older `runs` table is already present.
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(_get_engine())
        if "runs" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("runs")]
            if "latency_ms" not in columns:
                with _get_engine().connect() as conn:
                    conn.execute(text('ALTER TABLE runs ADD COLUMN latency_ms TEXT'))
                    conn.commit()
    except Exception:
        # Non-blocking: if migration fails, fastapi tests will still surface the schema mismatch.
        pass
