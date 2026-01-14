"""
Custom exceptions for the application.
Provides specific exception types for different error scenarios.
"""

from typing import Any


class AppException(Exception):
    """Base exception for all application exceptions."""

    def __init__(self, message: str, status_code: int = 500, details: dict[str, Any] | None = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(AppException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed", details: dict[str, Any] | None = None):
        super().__init__(message, status_code=401, details=details)


class AuthorizationError(AppException):
    """Raised when user doesn't have permission."""

    def __init__(self, message: str = "Permission denied", details: dict[str, Any] | None = None):
        super().__init__(message, status_code=403, details=details)


class NotFoundError(AppException):
    """Raised when a resource is not found."""

    def __init__(self, resource: str, identifier: str | None = None):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(message, status_code=404)


class ValidationError(AppException):
    """Raised when validation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, status_code=422, details=details)


class ConflictError(AppException):
    """Raised when there's a conflict (e.g., duplicate resource)."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, status_code=409, details=details)


class RateLimitError(AppException):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int | None = None):
        details = {"retry_after": retry_after} if retry_after else {}
        super().__init__(message, status_code=429, details=details)


class ExternalServiceError(AppException):
    """Raised when an external service fails."""

    def __init__(self, service: str, message: str | None = None):
        msg = f"External service error: {service}"
        if message:
            msg += f" - {message}"
        super().__init__(msg, status_code=502)


class FileProcessingError(AppException):
    """Raised when file processing fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, status_code=400, details=details)
