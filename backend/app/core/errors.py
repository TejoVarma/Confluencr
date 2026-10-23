"""Error types and handlers. Every error response has the shape {"error": "message"}."""

import logging
from collections.abc import Iterable
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

_LOCATION_PREFIXES = {"body", "query", "path"}


class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def error_response(message: str, status_code: int) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": message})


def format_validation_errors(errors: Iterable[dict[str, Any]]) -> str:
    """Turn pydantic errors into a single readable message."""
    messages: list[str] = []
    for err in errors:
        if err.get("type") == "json_invalid":
            messages.append("Request body must be valid JSON")
            continue
        field = ".".join(str(p) for p in err.get("loc", ()) if p not in _LOCATION_PREFIXES)
        msg = err.get("msg", "Invalid value")
        if err.get("type") == "missing":
            msg = f"{field} is required" if field else "Request body is required"
        elif msg.startswith("Value error, "):
            msg = msg.removeprefix("Value error, ")
        elif field:
            msg = f"{field}: {msg}"
        messages.append(msg)
    return "; ".join(messages) or "Invalid request"


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return error_response(exc.message, exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        return error_response(format_validation_errors(exc.errors()), 400)

    @app.exception_handler(ValidationError)
    async def handle_validation(_: Request, exc: ValidationError) -> JSONResponse:
        return error_response(format_validation_errors(exc.errors()), 400)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return error_response(str(exc.detail), exc.status_code)

    @app.exception_handler(Exception)
    async def handle_unexpected(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error", exc_info=exc)
        return error_response("Internal server error", 500)
