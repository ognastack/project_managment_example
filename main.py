"""
FastAPI application entry point.

ARCHITECTURE:
- Kong handles authentication and JWT validation
- FastAPI orchestrates business logic
- Hasura enforces data access and RBAC
- PostgreSQL stores data
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.config import get_settings
from app.api import workspaces, projects, tasks
from app.utils.exceptions import (
    HasuraError,
    ValidationError,
    InvalidStatusTransitionError,
    ResourceNotFoundError,
    PermissionDeniedError
)

# Initialize settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production-grade Team Project Management API",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(HasuraError)
async def hasura_error_handler(request: Request, exc: HasuraError):
    """Handle Hasura GraphQL errors."""
    return JSONResponse(
        status_code=exc.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": "Database operation failed",
            "detail": exc.errors(),
            "request_id": getattr(request.state, "request_id", None),
        }
    )


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """Handle business logic validation errors."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": True,
            "message": "Validation failed",
            "detail": exc.message,
            "request_id": getattr(request.state, "request_id", None),
        }
    )


@app.exception_handler(InvalidStatusTransitionError)
async def invalid_transition_handler(request: Request, exc: InvalidStatusTransitionError):
    """Handle invalid status transition errors."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "message": "Invalid status transition",
            "detail": exc.message,
            "from_status": exc.from_status,
            "to_status": exc.to_status,
            "error": True,
            "request_id": getattr(request.state, "request_id", None),
        }
    )


@app.exception_handler(ResourceNotFoundError)
async def not_found_handler(request: Request, exc: ResourceNotFoundError):
    """Handle resource not found errors."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "resource_type": exc.resource_type,
            "resource_id": exc.resource_id,
            "error": True,
            "message": "Resource not found",
            "detail": exc.message,
            "request_id": getattr(request.state, "request_id", None),
        }
    )


@app.exception_handler(PermissionDeniedError)
async def permission_denied_handler(request: Request, exc: PermissionDeniedError):
    """Handle permission denied errors."""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "message": "Permission denied",
            "error": True,
            "detail": exc.message,
            "request_id": getattr(request.state, "request_id", None),
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "message": "Request validation failed",
            "error": True,
            "detail": exc.errors(),
            "request_id": getattr(request.state, "request_id", None),

        }
    )


# Health check endpoint
@app.get("/v1/health", tags=["health"])
async def health_check():
    """Health check endpoint for load balancers."""
    return {
        "status": "healthy",
        "version": settings.app_version
    }


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """API root endpoint."""
    return {
        "message": "Team Project Management API",
        "version": settings.app_version,
        "docs": "/api/docs"
    }


app.include_router(workspaces.router, prefix="/v1")
app.include_router(projects.router, prefix="/v1")
app.include_router(tasks.router, prefix="/v1")

# Additional routers would be included here:
# app.include_router(workspaces.router, prefix="/api/v1")
# app.include_router(projects.router, prefix="/api/v1")
# app.include_router(comments.router, prefix="/api/v1")
# app.include_router(attachments.router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
