"""
Task management REST API endpoints.

This is the orchestration layer that:
1. Validates requests
2. Enforces business rules
3. Calls Hasura for data operations
4. Returns formatted responses
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from app.models.task import (
    TaskCreate, TaskUpdate, TaskResponse, TaskListResponse,
    TaskStatusUpdate, TaskStatus
)
from app.clients.hasura import HasuraClient
from app.dependencies import get_hasura_client, get_pagination_params, get_token
from app.services.task_service import TaskService
from app.utils.exceptions import (
    HasuraError, ValidationError, InvalidStatusTransitionError
)
import jwt

router = APIRouter(prefix="/tasks", tags=["tasks"])


def extract_user_id(token: str) -> str:
    """
    Extract user ID from JWT.

    Note: We don't validate the JWT (Kong does that).
    We only decode it to read claims.
    """
    try:
        # Decode without verification (Kong already verified)
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded.get("https://hasura.io/jwt/claims", {}).get("x-hasura-user-id")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format"
        )


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
        task_data: TaskCreate,
        hasura: HasuraClient = Depends(get_hasura_client)
):
    """
    Create a new task.

    - Validates project exists and user has access
    - Assigns next sequential task number
    - Records creation in activity log
    """
    try:

        task = await TaskService.create_task(hasura, task_data)
        return task
    except HasuraError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
        task_id: str,
        hasura: HasuraClient = Depends(get_hasura_client)
):
    """
    Get a task by ID.

    - Returns 404 if task doesn't exist or user lacks access
    """
    query = """
    query GetTask($id: uuid!) {
        tasks_by_pk(id: $id) {
            id
            project_id
            title
            description
            status
            priority
            task_number
            due_date
            created_by
            created_at
            updated_at
            assignees {
                id
                user_id
                assigned_at
                assigned_by
            }
        }
    }
    """

    try:
        result = await hasura.query(query, {"id": task_id})
        task = result.get("tasks_by_pk")

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )

        return task
    except HasuraError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=TaskListResponse)
async def list_tasks(
        project_id: Optional[str] = Query(None, description="Filter by project ID"),
        task_status: Optional[TaskStatus] = Query(None, description="Filter by status"),
        assigned_to_me: bool = Query(False, description="Show only tasks assigned to me"),
        hasura: HasuraClient = Depends(get_hasura_client),
        pagination: dict = Depends(get_pagination_params),
        token: str = Depends(get_token)
):
    """
    List tasks with optional filters.

    - Supports filtering by project, status, and assignment
    - Paginated results
    - Ordered by creation date (newest first)
    """
    user_id = extract_user_id(token) if assigned_to_me else None

    # Build where clause
    where_conditions = []
    if project_id:
        where_conditions.append({"project_id": {"_eq": project_id}})
    if task_status:
        where_conditions.append({"status": {"_eq": task_status.value}})
    if assigned_to_me and user_id:
        where_conditions.append({"assignees": {"user_id": {"_eq": user_id}}})

    where = {"_and": where_conditions} if where_conditions else {}

    query = """
    query ListTasks($where: tasks_bool_exp!, $limit: Int!, $offset: Int!) {
        tasks(
            where: $where,
            limit: $limit,
            offset: $offset,
            order_by: {created_at: desc}
        ) {
            id
            project_id
            title
            description
            status
            priority
            task_number
            due_date
            created_by
            created_at
            updated_at
            assignees {
                id
                user_id
                assigned_at
                assigned_by
            }
        }
    }
    """

    try:
        result = await hasura.query(
            query,
            {
                "where": where,
                "limit": pagination["limit"],
                "offset": pagination["offset"]
            }
        )

        return {
            "tasks": result["tasks"],
            "page": pagination["page"],
            "page_size": pagination["page_size"]
        }
    except HasuraError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
        task_id: str,
        task_data: TaskUpdate,
        hasura: HasuraClient = Depends(get_hasura_client)
):
    """
    Update task fields (except status - use dedicated endpoint).

    - Only updates provided fields
    - Status updates go through /tasks/{id}/status for validation
    """
    # Build update object
    updates = {}
    if task_data.title is not None:
        updates["title"] = task_data.title
    if task_data.description is not None:
        updates["description"] = task_data.description
    if task_data.priority is not None:
        updates["priority"] = task_data.priority.value
    if task_data.due_date is not None:
        updates["due_date"] = task_data.due_date.isoformat()

    # Don't allow status updates here
    if task_data.status is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use /tasks/{id}/status endpoint to update status"
        )

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    mutation = """
    mutation UpdateTask($id: uuid!, $updates: tasks_set_input!) {
        update_tasks_by_pk(pk_columns: {id: $id}, _set: $updates) {
            id
            project_id
            title
            description
            status
            priority
            task_number
            due_date
            created_by
            created_at
            updated_at
        }
    }
    """

    try:
        result = await hasura.mutate(
            mutation,
            {"id": task_id, "updates": updates}
        )

        updated_task = result.get("update_tasks_by_pk")
        if not updated_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )

        return updated_task
    except HasuraError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
        task_id: str,
        status_data: TaskStatusUpdate,
        hasura: HasuraClient = Depends(get_hasura_client)
):
    """
    Update task status with validation.

    - Validates status transition is allowed
    - Records status change in activity log
    - Returns 400 if transition is invalid
    """
    try:
        task = await TaskService.update_task_status(
            hasura,
            task_id,
            status_data.status
        )
        return task
    except InvalidStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except HasuraError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
        task_id: str,
        hasura: HasuraClient = Depends(get_hasura_client)
):
    """
    Delete a task.

    - Requires admin or member role
    - Cascades to assignees, comments, attachments
    """
    mutation = """
    mutation DeleteTask($id: uuid!) {
        delete_tasks_by_pk(id: $id) {
            id
        }
    }
    """

    try:
        result = await hasura.mutate(mutation, {"id": task_id})

        if not result.get("delete_tasks_by_pk"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )
    except HasuraError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )