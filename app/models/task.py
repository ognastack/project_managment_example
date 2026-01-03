"""Pydantic models for tasks."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """Task status enumeration."""
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"


class TaskPriority(str, Enum):
    """Task priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskBase(BaseModel):
    """Base task model."""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.BACKLOG
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    """Model for creating a task."""
    project_id: str = Field(..., description="UUID of the project")


class TaskUpdate(BaseModel):
    """Model for updating a task."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None


class TaskStatusUpdate(BaseModel):
    """Model for updating task status (with validation)."""
    status: TaskStatus


class TaskAssignee(BaseModel):
    """Task assignee model."""
    id: str
    user_id: str
    task_id: str
    assigned_at: datetime
    assigned_by: Optional[str] = None


class TaskResponse(TaskBase):
    """Task response model."""
    id: str
    project_id: str
    task_number: int
    created_by: str
    created_at: datetime
    updated_at: datetime
    assignees: List[TaskAssignee] = []

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Paginated task list response."""
    tasks: List[TaskResponse]