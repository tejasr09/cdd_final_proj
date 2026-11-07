from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.database import database_is_ready

app = FastAPI(
    title="Ripple Effect API",
    version="0.1.0",
    description=(
        "API foundation for Ripple Effect. Impact analysis will report estimates, "
        "not probabilities or guaranteed outcomes."
    ),
)


@app.get("/api/v1/health/live", tags=["health"], summary="Check process liveness")
def liveness() -> dict[str, str]:
    return {"status": "alive"}


@app.get("/api/v1/health/ready", tags=["health"], summary="Check application readiness")
def readiness() -> JSONResponse:
    if not database_is_ready():
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": "database_unavailable"},
        )
    return JSONResponse(status_code=200, content={"status": "ready"})
