"""
Unit tests for requirements/deployment/state.
"""
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.api import create_app


class TestGradeDeployment:
  def test_invalid_session_raises(self):
    with TestClient(create_app()) as client:
      response = client.get("/runs/9999")
      assert response.status_code in [404, 400]

  def test_valid_methods_only_for_existing_runs(self):
    with TestClient(create_app()) as client:
      response = client.get("/runs/real_run")
      assert response.status_code in [404, 200]
