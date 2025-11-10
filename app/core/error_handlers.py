"""
Global exception handlers for the FastAPI application.
Provides consistent error response format across all endpoints.
"""

import logging
from typing import Union

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from pymongo.errors import DuplicateKeyError, ConnectionFailure, OperationFailure
from bson.errors import InvalidId

from app.core.exceptions import BaseAPIException

# Configure logger
logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI application."""

    @app.exception_handler(BaseAPIException)
    async def base_api_exception_handler(request: Request, exc: BaseAPIException) -> JSONResponse:
        """Handle all custom API exceptions."""
        logger.error(
            f"API Exception: {exc.code} - {exc.message}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "details": exc.details
            }
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details
                }
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle Pydantic validation errors with detailed field information."""
        errors = []
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            errors.append({
                "field": field,
                "message": error["msg"],
                "type": error["type"]
            })

        logger.warning(
            f"Validation error on {request.url.path}",
            extra={"errors": errors, "method": request.method}
        )

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Input validation failed",
                    "details": {
                        "errors": errors
                    }
                }
            }
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
        """Handle Pydantic model validation errors."""
        errors = []
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            errors.append({
                "field": field,
                "message": error["msg"],
                "type": error["type"]
            })

        logger.warning(
            f"Pydantic validation error on {request.url.path}",
            extra={"errors": errors, "method": request.method}
        )

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Data validation failed",
                    "details": {
                        "errors": errors
                    }
                }
            }
        )

    @app.exception_handler(DuplicateKeyError)
    async def duplicate_key_exception_handler(request: Request, exc: DuplicateKeyError) -> JSONResponse:
        """Handle MongoDB duplicate key errors."""
        logger.error(
            f"Duplicate key error on {request.url.path}",
            extra={"error": str(exc), "method": request.method}
        )

        # Extract field name from error message if possible
        error_msg = str(exc)
        field_name = "field"
        if "dup key" in error_msg:
            # Try to extract field name from error message
            try:
                field_start = error_msg.find("{ ") + 2
                field_end = error_msg.find(":", field_start)
                if field_start > 1 and field_end > field_start:
                    field_name = error_msg[field_start:field_end].strip()
            except Exception:
                pass

        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": {
                    "code": "DUPLICATE_RESOURCE",
                    "message": f"A resource with this {field_name} already exists",
                    "details": {
                        "field": field_name
                    }
                }
            }
        )

    @app.exception_handler(ConnectionFailure)
    async def connection_failure_exception_handler(request: Request, exc: ConnectionFailure) -> JSONResponse:
        """Handle MongoDB connection failures."""
        logger.critical(
            f"Database connection failure on {request.url.path}",
            extra={"error": str(exc), "method": request.method}
        )

        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": {
                    "code": "DATABASE_CONNECTION_ERROR",
                    "message": "Database connection failed. Please try again later",
                    "details": {}
                }
            }
        )

    @app.exception_handler(OperationFailure)
    async def operation_failure_exception_handler(request: Request, exc: OperationFailure) -> JSONResponse:
        """Handle MongoDB operation failures."""
        logger.error(
            f"Database operation failure on {request.url.path}",
            extra={"error": str(exc), "method": request.method}
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "DATABASE_OPERATION_ERROR",
                    "message": "Database operation failed. Please try again",
                    "details": {}
                }
            }
        )

    @app.exception_handler(InvalidId)
    async def invalid_id_exception_handler(request: Request, exc: InvalidId) -> JSONResponse:
        """Handle invalid MongoDB ObjectId format."""
        logger.warning(
            f"Invalid ObjectId on {request.url.path}",
            extra={"error": str(exc), "method": request.method}
        )

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "INVALID_OBJECT_ID",
                    "message": "Invalid ID format. Expected valid MongoDB ObjectId",
                    "details": {}
                }
            }
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        Catch-all handler for unexpected exceptions.
        Logs the full error but returns a safe message to the user.
        """
        logger.critical(
            f"Unhandled exception on {request.url.path}: {type(exc).__name__}",
            extra={
                "error": str(exc),
                "method": request.method,
                "type": type(exc).__name__
            },
            exc_info=True
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An internal server error occurred. Please contact support if the problem persists",
                    "details": {}
                }
            }
        )
