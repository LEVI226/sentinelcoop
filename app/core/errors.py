"""Format d'erreur commun — CDC §45 & §46.

{"success":false,"error":{"code":"...","message":"...","details":{}},"requestId":"..."}
{"success":true,"data":{},"meta":{"requestId":"..."}}
"""
from __future__ import annotations

import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    """Erreur applicative structurée."""

    def __init__(self, code: str, message: str, status: int = 400, details: dict | None = None):
        self.code = code
        self.message = message
        self.status = status
        self.details = details or {}
        super().__init__(message)


def _req_id(request: Request) -> str:
    return request.state.request_id


def _error_body(code: str, message: str, details: dict, request_id: str) -> dict:
    return {
        "success": False,
        "error": {"code": code, "message": message, "details": details},
        "requestId": request_id,
    }


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status,
        content=_error_body(exc.code, exc.message, exc.details, _req_id(request)),
    )


async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body("HTTP_ERROR", str(exc.detail) if exc.detail else "error",
                            {}, _req_id(request)),
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=_error_body(
            "VALIDATION_ERROR",
            "Données invalides",
            {"errors": exc.errors()},
            _req_id(request),
        ),
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=_error_body("INTERNAL_ERROR", "Erreur interne du serveur",
                            {}, _req_id(request)),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)                 # type: ignore
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)


def request_id_middleware(request: Request, call_next):
    request.state.request_id = "req_" + uuid.uuid4().hex[:12]
    if request.headers.get("x-request-id"):
        request.state.request_id = request.headers["x-request-id"][:40]
    return call_next(request)
