"""Pydantic models for projects."""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
import re


class ProjectBase(BaseModel):
    """Base project model."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    key: str = Field(..., min_length=2, max_length=10, description="Project key (e.g., PROJ)")
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$', description="Hex color code")

    @validator('key')
    def validate_key(cls, v):
        """Validate project key format (uppercase letters only)."""
        v = v.upper()
        if not re.match(r'^[A-Z]{2,10}$', v):
            raise ValueError('Project key must be 2-10 uppercase letters')
        return v


class ProjectCreate(ProjectBase):
    """Model for creating a project."""
    workspace_id: str = Field(..., description="UUID of the workspace")


class ProjectUpdate(BaseModel):
    """Model for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    is_archived: Optional[bool] = None


class ProjectResponse(ProjectBase):
    """Project response model."""
    id: str
    workspace_id: str
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    # Optional nested data
    task_count: Optional[int] = None
    open_task_count: Optional[int] = None

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """Paginated project list response."""
    projects: List[ProjectResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ProjectStats(BaseModel):
    """Project statistics model."""
    total_tasks: int
    tasks_by_status: dict
    tasks_by_priority: dict
    completion_rate: float