"""
Business logic for workspace management.
"""
from typing import Dict, Any, List
from app.clients.hasura import HasuraClient
from app.clients.graphql_queries import (
    CREATE_WORKSPACE,
    GET_WORKSPACE_BY_SLUG,
    CREATE_ACTIVITY_LOG
)
from app.models.workspace import WorkspaceCreate
from app.utils.exceptions import ValidationError
from datetime import datetime, timezone


class WorkspaceService:
    """Service for workspace operations."""

    @staticmethod
    async def create_workspace(
            hasura: HasuraClient,
            workspace_data: WorkspaceCreate
    ) -> Dict[str, Any]:
        """
        Create a new workspace and automatically add creator as admin.

        Args:
            hasura: Hasura client with user context
            workspace_data: Workspace creation data

        Returns:
            dict: Created workspace data

        Raises:
            ValidationError: If slug already exists
        """
        # Check if slug already exists
        result = await hasura.query(
            GET_WORKSPACE_BY_SLUG,
            {"slug": workspace_data.slug}
        )

        if result.get("workspaces"):
            raise ValidationError(
                f"Workspace with slug '{workspace_data.slug}' already exists",
                field="slug"
            )

        # Create workspace with creator as admin member
        variables = {
            "object": {
                "name": workspace_data.name,
                "slug": workspace_data.slug,
                "description": workspace_data.description,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        }

        result = await hasura.mutate(CREATE_WORKSPACE, variables)
        return result["insert_workspaces_one"]


    @staticmethod
    async def check_user_permission(
            hasura: HasuraClient,
            workspace_id: str,
            required_role: str = None
    ) -> Dict[str, Any]:
        """
        Check if user has access to workspace and optionally verify role.

        Args:
            hasura: Hasura client with user context
            workspace_id: Workspace ID
            user_id: User ID
            required_role: Optional role requirement ('admin', 'member')

        Returns:
            dict: User's membership info

        Raises:
            ValidationError: If user lacks permission
        """
        from app.clients.graphql_queries import GET_USER_ROLE_IN_WORKSPACE

        result = await hasura.query(
            GET_USER_ROLE_IN_WORKSPACE,
            {"workspace_id": workspace_id}
        )

        members = result.get("workspace_members", [])
        if not members:
            raise ValidationError("You don't have access to this workspace")

        member = members[0]

        if required_role:
            allowed_roles = {
                "admin": ["admin"],
                "member": ["admin", "member"]
            }

            if member["role"] not in allowed_roles.get(required_role, []):
                raise ValidationError(
                    f"You need {required_role} role to perform this action"
                )

        return member

    @staticmethod
    async def _log_activity(
            hasura: HasuraClient,
            workspace_id: str,
            user_id: str,
            activity_type: str,
            entity_type: str,
            entity_id: str,
            metadata: Dict[str, Any] = None
    ) -> None:
        """Log an activity to activity_logs table."""
        variables = {
            "object": {
                "workspace_id": workspace_id,
                "user_id": user_id,
                "activity_type": activity_type,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "metadata": metadata or {}
            }
        }

        await hasura.mutate(CREATE_ACTIVITY_LOG, variables)