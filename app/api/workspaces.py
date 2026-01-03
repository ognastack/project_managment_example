"""
Workspace management REST API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query

from typing import Optional
from app.models.workspace import (
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceResponse,
    WorkspaceListResponse,
    WorkspaceMemberInvite,
    WorkspaceMemberUpdateRole,
    WorkspaceMemberResponse
)
from app.clients.hasura import HasuraClient
from app.clients.graphql_queries import (
    GET_WORKSPACES,
    GET_WORKSPACE_BY_ID,
    GET_WORKSPACE_BY_SLUG,
    UPDATE_WORKSPACE,
    DELETE_WORKSPACE,
    GET_WORKSPACE_MEMBERS,
    ADD_WORKSPACE_MEMBER,
    UPDATE_MEMBER_ROLE,
    REMOVE_WORKSPACE_MEMBER,
    GET_WORKSPACE_ACTIVITY
)
from app.dependencies import get_hasura_client, get_pagination_params, get_token
from app.services.workspace_service import WorkspaceService
from app.utils.exceptions import HasuraError, ValidationError
import jwt
from app.config import get_settings

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

settings = get_settings()


def extract_user_id(token: str) -> str:
    """Get current authenticated user"""
    try:

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            audience="authenticated"
        )
        user_id: str = payload.get("sub")

        if user_id is None:
            raise Exception("Could not validate credentials")
    except Exception as e:
        raise e

    return user_id


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
        workspace_data: WorkspaceCreate,
        hasura: HasuraClient = Depends(get_hasura_client)
):
    """
    Create a new workspace.

    - Creator is automatically added as admin
    - Slug must be unique across all workspaces
    - Records creation in activity log
    """
    try:
        workspace = await WorkspaceService.create_workspace(
            hasura,
            workspace_data
        )
        return workspace
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


@router.get("", response_model=WorkspaceListResponse, status_code=status.HTTP_202_ACCEPTED)
async def list_workspaces(
        hasura: HasuraClient = Depends(get_hasura_client),
        pagination: dict = Depends(get_pagination_params)
):
    """
    List all workspaces the user has access to.

    - Returns only workspaces where user is a member
    - Includes member count and project count
    - Ordered by creation date (newest first)
    """
    try:
        result = await hasura.query(
            GET_WORKSPACES,
            {
                "limit": pagination["limit"],
                "offset": pagination["offset"]
            }
        )

        workspaces = []
        for ws in result["workspaces"]:
            workspaces.append({
                **ws,
                "member_count": len(ws['members']),
                "project_count": len(ws['projects'])
            })

        total = result["workspaces_aggregate"]["aggregate"]["count"]
        total_pages = (total + pagination["page_size"] - 1) // pagination["page_size"]

        return {
            "workspaces": workspaces,
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


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
        workspace_id: str = Path(..., description="Workspace UUID"),
        hasura: HasuraClient = Depends(get_hasura_client)
):
    """
    Get a workspace by ID.

    - Returns 404 if workspace doesn't exist or user lacks access
    - Includes member details
    """
    try:
        result = await hasura.query(
            GET_WORKSPACE_BY_ID,
            {"id": workspace_id}
        )

        workspace = result.get("workspaces_by_pk")
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace {workspace_id} not found"
            )
        print(result)
        # Add project count
        workspace["project_count"] = len(workspace["projects"])

        return workspace
    except HasuraError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/slug/{slug}", response_model=WorkspaceResponse)
async def get_workspace_by_slug(
        slug: str = Path(..., description="Workspace slug"),
        hasura: HasuraClient = Depends(get_hasura_client)
):
    """
    Get a workspace by slug.

    - Slugs are unique identifiers (e.g., 'my-company')
    - Returns 404 if not found or user lacks access
    """
    try:
        result = await hasura.query(
            GET_WORKSPACE_BY_SLUG,
            {"slug": slug}
        )

        workspaces = result.get("workspaces", [])
        if not workspaces:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace with slug '{slug}' not found"
            )

        return workspaces[0]
    except HasuraError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
        workspace_id: str,
        workspace_data: WorkspaceUpdate,
        hasura: HasuraClient = Depends(get_hasura_client),
        token: str = Depends(get_token)
):
    """
    Update workspace details.

    - Requires admin role
    - Only updates provided fields
    - Cannot update slug (immutable)
    """
    try:
        # Check user has admin permission
        await WorkspaceService.check_user_permission(
            hasura,
            workspace_id,
            required_role="admin"
        )

        # Build updates
        updates = {}
        if workspace_data.name is not None:
            updates["name"] = workspace_data.name
        if workspace_data.description is not None:
            updates["description"] = workspace_data.description

        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )

        result = await hasura.mutate(
            UPDATE_WORKSPACE,
            {"id": workspace_id, "updates": updates}
        )

        updated_workspace = result.get("update_workspaces_by_pk")
        if not updated_workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace {workspace_id} not found"
            )

        return updated_workspace
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


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
        workspace_id: str,
        hasura: HasuraClient = Depends(get_hasura_client),
        token: str = Depends(get_token)
):
    """
    Delete a workspace.

    - Requires admin role
    - Cascades to all projects, tasks, and members
    - This action is irreversible
    """
    try:

        # Check user has admin permission
        await WorkspaceService.check_user_permission(
            hasura,
            workspace_id,
            required_role="admin"
        )

        result = await hasura.mutate(DELETE_WORKSPACE, {"id": workspace_id})

        if not result.get("delete_workspaces_by_pk"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace {workspace_id} not found"
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


# ============================================================================
# WORKSPACE MEMBERS ENDPOINTS
# ============================================================================

@router.get("/{workspace_id}/members", response_model=list[WorkspaceMemberResponse])
async def get_workspace_members(
        workspace_id: str,
        hasura: HasuraClient = Depends(get_hasura_client)
):
    """
    Get all members of a workspace.

    - Includes user email from auth.users
    - Ordered by join date
    """
    try:
        result = await hasura.query(
            GET_WORKSPACE_MEMBERS,
            {"workspace_id": workspace_id}
        )

        return result.get("workspace_members", [])
    except HasuraError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{workspace_id}/members", response_model=WorkspaceMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_workspace_member(
        workspace_id: str,
        member_data: WorkspaceMemberInvite,
        hasura: HasuraClient = Depends(get_hasura_client)
):
    """
    Add a member to the workspace.

    - Requires admin role
    - User must exist in auth.users
    - Cannot add same user twice
    """
    try:

        # Check user has admin permission
        await WorkspaceService.check_user_permission(
            hasura,
            workspace_id,
            required_role="admin"
        )

        variables = {
            "object": {
                "workspace_id": workspace_id,
                "user_id": member_data.user_id,
                "role": member_data.role.value
            }
        }

        result = await hasura.mutate(ADD_WORKSPACE_MEMBER, variables)
        member = result["insert_workspace_members_one"]

        return member
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


@router.patch("/{workspace_id}/members/{member_id}/role")
async def update_member_role(
        workspace_id: str,
        member_id: str,
        role_data: WorkspaceMemberUpdateRole,
        hasura: HasuraClient = Depends(get_hasura_client),
        token: str = Depends(get_token)
):
    """
    Update a member's role.

    - Requires admin role
    - Cannot change your own role
    """
    try:

        # Check user has admin permission
        await WorkspaceService.check_user_permission(
            hasura,
            workspace_id,
            required_role="admin"
        )

        result = await hasura.mutate(
            UPDATE_MEMBER_ROLE,
            {"id": member_id, "role": role_data.role.value}
        )

        updated_member = result.get("update_workspace_members_by_pk")
        if not updated_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Member {member_id} not found"
            )

        return updated_member
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


@router.delete("/{workspace_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_workspace_member(
        workspace_id: str,
        member_id: str,
        hasura: HasuraClient = Depends(get_hasura_client),
        token: str = Depends(get_token)
):
    """
    Remove a member from the workspace.

    - Requires admin role
    - Cannot remove yourself if you're the last admin
    """
    try:
        # Check user has admin permission
        await WorkspaceService.check_user_permission(
            hasura,
            workspace_id,
            required_role="admin"
        )

        result = await hasura.mutate(REMOVE_WORKSPACE_MEMBER, {"userId": member_id, "workspaceId": workspace_id})

        if not result.get("delete_workspace_members_by_pk"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Member {member_id} not found"
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
