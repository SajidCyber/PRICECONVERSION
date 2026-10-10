"""Centralized Domain Exceptions and Global FastAPI Exception Handlers."""

from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.logging_config import logger


class AppError(Exception):
    """Base exception for all application domain errors."""

    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


class EntityNotFoundError(AppError):
    def __init__(self, entity: str, identifier: Any):
        super().__init__(
            message=f"{entity} with ID '{identifier}' not found.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"entity": entity, "identifier": str(identifier)},
        )


class SSRFSecurityError(AppError):
    def __init__(self, url: str, reason: str):
        super().__init__(
            message=f"SSRF Security Violation: Request to '{url}' blocked. {reason}",
            status_code=status.HTTP_403_FORBIDDEN,
            details={"blocked_url": url, "reason": reason},
        )


class ScrapingError(AppError):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=f"Scraping Engine Failure: {message}",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details,
        )


class LandedCostCalculationError(AppError):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=f"Landed Cost Error: {message}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class DataIngestionError(AppError):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=f"Data Ingestion Failure: {message}",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Registers global exception handlers on the FastAPI application."""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        logger.warning(
            "Application error: %s (Path: %s, Status: %d)",
            exc.message,
            request.url.path,
            exc.status_code,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.__class__.__name__,
                    "message": exc.message,
                    "details": exc.details,
                },
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.warning("Request validation failed for %s: %s", request.url.path, exc.errors())
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "ValidationError",
                    "message": "The request payload failed validation constraints.",
                    "details": exc.errors(),
                },
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": "HTTPError",
                    "message": exc.detail or "HTTP Error",
                    "details": None,
                },
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled server exception on %s: %s", request.url.path, str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "InternalServerError",
                    "message": "An unexpected server error occurred. Please consult application logs.",
                    "details": str(exc) if app.debug else None,
                },
            },
        )
