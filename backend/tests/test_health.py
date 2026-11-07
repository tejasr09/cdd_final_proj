from fastapi.responses import JSONResponse

from app.main import app, liveness, readiness


def test_liveness_endpoint_contract() -> None:
    route_paths = app.openapi()["paths"]

    assert "/api/v1/health/live" in route_paths
    assert liveness() == {"status": "alive"}


def test_readiness_endpoint_contract_when_database_is_ready(monkeypatch) -> None:
    route_paths = app.openapi()["paths"]

    assert "/api/v1/health/ready" in route_paths
    monkeypatch.setattr("app.main.database_is_ready", lambda: True)
    response = readiness()
    assert isinstance(response, JSONResponse)
    assert response.status_code == 200
    assert response.body == b'{"status":"ready"}'


def test_readiness_returns_service_unavailable_without_database(monkeypatch) -> None:
    monkeypatch.setattr("app.main.database_is_ready", lambda: False)

    response = readiness()

    assert response.status_code == 503
    assert response.body == (b'{"status":"not_ready","reason":"database_unavailable"}')
