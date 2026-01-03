"""
Configuration management for FastAPI application.
All settings loaded from environment variables.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""

    # Application
    app_name: str = "Team Project Management API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Hasura
    GRAPHQL_HOST: str = 'http://hasura:8080'
    GRAPHQL_ENDPOINT: str = '/v1/graphql'
    GRAPHQL_SECRET: str = '/v1/graphql'

    SECRET_KEY: str = 'vPDsBi2TafJuP4iqp40qx60AR34Qf6hQgC8GWBB7GoOKGqL9V6'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    # IMPORTANT: No admin secret stored here

    # S3/Storage (for file uploads)
    s3_bucket: str = "test"
    s3_region: str = "us-east-1"
    s3_endpoint_url: str | None = None

    # CORS
    cors_origins: list[str] = ["*"]

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
