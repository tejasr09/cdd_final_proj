from app.main import app, liveness, readiness


def test_liveness_endpoint_contract() -> None:
    route_paths = {route.path for route in app.routes}

    assert "/api/v1/health/live" in route_paths
    assert liveness() == {"status": "alive"}


def test_readiness_endpoint_contract() -> None:
    route_paths = {route.path for route in app.routes}

    assert "/api/v1/health/ready" in route_paths
    assert readiness() == {"status": "ready"}
