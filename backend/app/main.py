from fastapi import FastAPI

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
def readiness() -> dict[str, str]:
    return {"status": "ready"}
