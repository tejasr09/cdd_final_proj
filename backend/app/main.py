import logging
import re
from uuid import uuid4

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.api import router
from app.database import database_is_ready
from app.schemas import ErrorBody, ErrorDetail, ErrorEnvelope

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Ripple Effect API",
    version="0.1.0",
    description=(
        "API foundation for Ripple Effect. Impact analysis will report estimates, "
        "not probabilities or guaranteed outcomes."
    ),
)
app.include_router(router)


@app.middleware("http")
async def request_id_middleware(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    supplied_id = request.headers.get("x-request-id", "")
    request_id = (
        supplied_id if re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", supplied_id) else str(uuid4())
    )
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


def _error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    details: list[ErrorDetail] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid4()))
    envelope = ErrorEnvelope(
        error=ErrorBody(
            code=code,
            message=message,
            details=details or [],
            request_id=request_id,
        )
    )
    response_headers = {"X-Request-ID": request_id}
    if headers:
        response_headers.update(headers)
    return JSONResponse(
        status_code=status_code,
        content=envelope.model_dump(mode="json"),
        headers=response_headers,
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request,
    exception: StarletteHTTPException,
) -> JSONResponse:
    code_by_status = {
        400: "bad_request",
        401: "authentication_error",
        403: "permission_denied",
        404: "not_found",
        409: "conflict",
        422: "validation_error",
    }
    message = exception.detail if isinstance(exception.detail, str) else "The request failed."
    return _error_response(
        request,
        status_code=exception.status_code,
        code=code_by_status.get(exception.status_code, "request_error"),
        message=message,
        headers=exception.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exception: RequestValidationError,
) -> JSONResponse:
    details = [
        ErrorDetail(
            field=".".join(str(part) for part in error["loc"]),
            message=error["msg"],
            code=error["type"],
        )
        for error in exception.errors()
    ]
    return _error_response(
        request,
        status_code=422,
        code="validation_error",
        message="The request could not be validated.",
        details=details,
    )


@app.exception_handler(IntegrityError)
async def integrity_exception_handler(request: Request, _exception: IntegrityError) -> JSONResponse:
    return _error_response(
        request,
        status_code=409,
        code="conflict",
        message="The requested change conflicts with existing data.",
    )


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exception: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unavailable")
    logger.error(
        "Unhandled API request failed; request_id=%s exception_type=%s",
        request_id,
        type(exception).__name__,
    )
    return _error_response(
        request,
        status_code=500,
        code="internal_error",
        message="An unexpected server error occurred.",
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
