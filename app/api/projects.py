"""
Project management REST API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from typing import Optional
from app.models.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    ProjectStats
)
from app.clients.hasura import HasuraClient
from app.clients.graphql_queries import (
    GET_PROJECTS,
    GET_PROJECT_BY_ID,
    UPDATE_PROJECT,
    DELETE_PROJECT
)
from app.dependencies import get_hasura_client, get_pagination_params, get_token
from app.services.project_service import ProjectService
from app.services.workspace_service import WorkspaceService
from app.utils.exceptions import HasuraError, ValidationError
import jwt

router = APIRouter(prefix="/projects", tags=["projects"])


def extract_user_id(token: str) -> str:
    """Extract user ID from JWT without validation."""
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded.get("https://hasura.io/jwt/claims", {}).get("x-hasura-user-id")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format"
        )


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
        project_data: ProjectCreate,
        hasura: HasuraClient = Depends(get_hasura_client)
):
    """
    Create a new project in a workspace.

    - Requires admin or member role in the workspace
    - Project key must be unique within the workspace
    - Key is automatically converted to uppercase
    - Records creation in activity log
    """
    try:

        # Check user has member or admin permission in workspace
        await WorkspaceService.check_user_permission(
            hasura,
            project_data.workspace_id,
            required_role="member"
        )

        project = await ProjectService.create_project(
            hasura,
            project_data
        )
        return project
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except HasuraError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=ProjectListResponse)
async def list_projects(
        workspace_id: Optional[str] = Query(None, description="Filter by workspace ID"),
        include_archived: bool = Query(False, description="Include archived projects"),
        hasura: HasuraClient = Depends(get_hasura_client),
        pagination: dict = Depends(get_pagination_params)
):
    """
    List projects in a workspace.

    - Returns only projects in workspaces user has access to
    - Can filter to show/hide archived projects
    - Includes task counts
    - Ordered by creation date (newest first)
    """
    try:

        variables = {
            "limit": pagination["limit"],
            "offset": pagination["offset"]
        }

        if workspace_id is not None:
            variables["where"] = {"_and": [{"workspace_id": {"_eq": workspace_id}}]}

        result = await hasura.query(
            GET_PROJECTS,
            variables
        )

        projects = []
        for project in result["projects"]:
            projects.append({
                **project,
                "task_count": len(project['tasks']),
                "open_task_count": 0
            })

        total = len(result["projects"])
        total_pages = (total + pagination["page_size"] - 1) // pagination["page_size"]

        return {
            "projects": projects,
            "total": total,
            "page": pagination["page"],
            "page_size": pagination["page_size"],
            "total_pages": total_pages
        }
    except HasuraError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
        project_id: str = Path(..., description="Project UUID"),
        hasura: HasuraClient = Depends(get_hasura_client)
):
    """
    Get a project by ID.

    - Returns 404 if project doesn't exist or user lacks access
    - Includes task counts
    """
    try:
        result = await hasura.query(
            GET_PROJECT_BY_ID,
            {"id": project_id}
        )

        project = result.get("projects_by_pk")
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )

        # Add task counts
        project["task_count"] = len(project['tasks'])
        project["open_task_count"] = 0

        return project
    except HasuraError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
        project_id: str,
        project_data: ProjectUpdate,
        hasura: HasuraClient = Depends(get_hasura_client),
        token: str = Depends(get_token)
):
    """
    Update project details.

    - Requires admin or member role
    - Cannot update project key (immutable)
    - Cannot change workspace
    - Can archive/unarchive project
    """
    try:

        # Get project to check workspace
        result = await hasura.query(GET_PROJECT_BY_ID, {"id": project_id})
        project = result.get("projects_by_pk")

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )

        # Check user has member or admin permission
        await WorkspaceService.check_user_permission(
            hasura,
            project["workspace_id"],
            required_role="member"
        )

        # Build updates
        updates = {}
        if project_data.name is not None:
            updates["name"] = project_data.name
        if project_data.description is not None:
            updates["description"] = project_data.description
        if project_data.color is not None:
            updates["color"] = project_data.color
        if project_data.is_archived is not None:
            updates["is_archived"] = project_data.is_archived

        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )

        result = await hasura.mutate(
            UPDATE_PROJECT,
            {"id": project_id, "updates": updates}
        )

        updated_project = result.get("update_projects_by_pk")
        if not updated_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )

        return updated_project
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.message
        )
    except HasuraError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
        project_id: str,
        hasura: HasuraClient = Depends(get_hasura_client)
):
    """
    Delete a project.

    - Requires admin role
    - Cascades to all tasks, comments, and attachments
    - This action is irreversible
    """
    try:
        # Get project to check workspace
        result = await hasura.query(GET_PROJECT_BY_ID, {"id": project_id})
        project = result.get("projects_by_pk")

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )

        # Check user has admin permission
        await WorkspaceService.check_user_permission(
            hasura,
            project["workspace_id"],
            required_role="admin"
        )

        result = await hasura.mutate(DELETE_PROJECT, {"id": project_id})

        if not result.get("delete_projects_by_pk"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.message
        )
    except HasuraError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

