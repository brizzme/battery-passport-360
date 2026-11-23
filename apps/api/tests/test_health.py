import pytest
from fastapi.testclient import TestClient

from app.main import app, database_ready


@pytest.mark.parametrize("ready,code,status,database", [
    (True, 200, "ok", "ready"),
    (False, 503, "unavailable", "unavailable"),
])
def test_health_reports_database_state(ready, code, status, database):
    app.dependency_overrides[database_ready] = lambda: ready
    try:
        response = TestClient(app).get("/health")
        assert response.status_code == code
        assert response.json() == {"status": status, "database": database}
    finally:
        app.dependency_overrides.pop(database_ready)
