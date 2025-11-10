"""
Custom exception classes for the application.
These exceptions provide descriptive error messages and proper HTTP status codes.
"""

from typing import Any, Dict, Optional


class BaseAPIException(Exception):
    """Base exception class for all API exceptions."""

    def __init__(
        self,
        message: str,
        code: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ResourceNotFoundException(BaseAPIException):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str, identifier: str, field: str = "ID"):
        message = f"{resource} with {field} '{identifier}' not found"
        super().__init__(
            message=message,
            code="RESOURCE_NOT_FOUND",
            status_code=404,
            details={"resource": resource, field.lower(): identifier}
        )


class DuplicateResourceException(BaseAPIException):
    """Raised when trying to create a resource that already exists."""

    def __init__(self, resource: str, field: str, value: str):
        message = f"{resource} with {field} '{value}' already exists"
        super().__init__(
            message=message,
            code="DUPLICATE_RESOURCE",
            status_code=409,
            details={"resource": resource, "field": field, "value": value}
        )


class InvalidInputException(BaseAPIException):
    """Raised when business logic validation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="INVALID_INPUT",
            status_code=400,
            details=details or {}
        )


class DatabaseConnectionException(BaseAPIException):
    """Raised when database connection fails."""

    def __init__(self, message: str = "Database connection failed. Please try again later"):
        super().__init__(
            message=message,
            code="DATABASE_CONNECTION_ERROR",
            status_code=503,
            details={}
        )


class DatabaseOperationException(BaseAPIException):
    """Raised when a database operation fails."""

    def __init__(self, operation: str, message: str = "Database operation failed"):
        super().__init__(
            message=f"{message}: {operation}",
            code="DATABASE_OPERATION_ERROR",
            status_code=500,
            details={"operation": operation}
        )


class InvalidObjectIdException(BaseAPIException):
    """Raised when an invalid MongoDB ObjectId is provided."""

    def __init__(self, value: str, resource: str = "Resource"):
        message = f"Invalid {resource} ID format: '{value}'. Expected valid MongoDB ObjectId"
        super().__init__(
            message=message,
            code="INVALID_OBJECT_ID",
            status_code=400,
            details={"provided_value": value}
        )
