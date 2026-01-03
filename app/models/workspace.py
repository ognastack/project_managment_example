"""Pydantic models for workspaces."""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import re


class UserRole(str, Enum):
    """Workspace member role enumeration."""
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class WorkspaceMemberBase(BaseModel):
    """Base workspace member model."""
    user_id: str
    role: UserRole = UserRole.MEMBER


class WorkspaceMemberResponse(WorkspaceMemberBase):
    """Workspace member response model."""
    id: str
    workspace_id: str
    joined_at: datetime

    # Nested user info
    user: Optional[dict] = None  # From auth.users
    user_profile: Optional[dict] = None  # From user_profiles

    class Config:
        from_attributes = True


class WorkspaceBase(BaseModel):
    """Base workspace model."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

    @validator('slug')
    def validate_slug(cls, v):
        """Validate slug format (lowercase, alphanumeric, hyphens)."""
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v


class WorkspaceCreate(WorkspaceBase):
    """Model for creating a workspace."""
    pass


class WorkspaceUpdate(BaseModel):
    """Model for updating a workspace."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class WorkspaceResponse(WorkspaceBase):
    """Workspace response model."""
    id: str
    created_by: str
    created_at: datetime
    updated_at: datetime

    # Optional nested data
    members: List[WorkspaceMemberResponse] = []
    member_count: Optional[int] = None
    project_count: Optional[int] = None

    class Config:
        from_attributes = True


class WorkspaceListResponse(BaseModel):
    """Paginated workspace list response."""
    workspaces: List[WorkspaceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class WorkspaceMemberInvite(BaseModel):
    """Model for inviting a member to workspace."""
    user_id: str = Field(..., description="UUID of user to invite")
    role: UserRole = UserRole.MEMBER


class WorkspaceMemberUpdateRole(BaseModel):
    """Model for updating a member's role."""
    role: UserRole