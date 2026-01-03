"""
Dependency injection for FastAPI.
Handles JWT extraction and Hasura client creation.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.clients.hasura import HasuraClient
from app.config import get_settings, Settings

# Security scheme for JWT extraction
security = HTTPBearer()


async def get_token(
        credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Extract JWT token from Authorization header.

    CRITICAL: This function does NOT validate the JWT.
    Kong has already validated it. We only extract it here
    to forward to Hasura.

    Args:
        credentials: HTTP Authorization credentials from request

    Returns:
        str: Raw JWT token (opaque to this application)

    Raises:
        HTTPException: If Authorization header is missing
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Return token as-is, treating it as opaque
    return credentials.credentials


async def get_hasura_client(
        token: str = Depends(get_token),
        settings: Settings = Depends(get_settings)
) -> HasuraClient:
    """
    Create Hasura GraphQL client with user JWT.

    CRITICAL: This forwards the user's JWT to Hasura for RBAC.
    NEVER use admin secret here.

    Args:
        token: User JWT from Authorization header
        settings: Application settings

    Returns:
        HasuraClient: Configured Hasura client with user context
    """
    return HasuraClient(
        url=f"{settings.GRAPHQL_HOST}/{settings.GRAPHQL_ENDPOINT}",
        token=token
    )


async def get_pagination_params(
        page: int = 1,
        page_size: int = 20,
        settings: Settings = Depends(get_settings)
) -> dict:
    """
    Extract and validate pagination parameters.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        settings: Application settings for max limits

    Returns:
        dict: Pagination parameters (limit, offset)

    Raises:
        HTTPException: If parameters are invalid
    """
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page must be >= 1"
        )

    if page_size < 1 or page_size > settings.max_page_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Page size must be between 1 and {settings.max_page_size}"
        )

    offset = (page - 1) * page_size

    return {
        "limit": page_size,
        "offset": offset,
        "page": page,
        "page_size": page_size
    }