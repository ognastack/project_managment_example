"""Custom exceptions for the application."""
from typing import Any, Dict, Optional


class HasuraError(Exception):
    """Raised when Hasura GraphQL query fails."""

    def __init__(
            self,
            message: str,
            errors: Optional[list] = None,
            status_code: Optional[int] = None
    ):
        self.message = message
        self.errors = errors or []
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(Exception):
    """Raised when business logic validation fails."""

    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class InvalidStatusTransitionError(ValidationError):
    """Raised when task status transition is invalid."""

    def __init__(self, from_status: str, to_status: str):
        message = f"Invalid status transition: {from_status} -> {to_status}"
        super().__init__(message)
        self.from_status = from_status
        self.to_status = to_status


class ResourceNotFoundError(Exception):
    """Raised when a resource is not found."""

    def __init__(self, resource_type: str, resource_id: str):
        self.message = f"{resource_type} with id {resource_id} not found"
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(self.message)


class PermissionDeniedError(Exception):
    """Raised when user lacks permission for an action."""

    def __init__(self, message: str = "Permission denied"):
        self.message = message
        super().__init__(self.message)