"""
Business logic for project management.
"""
from typing import Dict, Any
from app.clients.hasura import HasuraClient
from app.clients.graphql_queries import (
    CREATE_PROJECT,
    GET_PROJECT_BY_KEY,
    CREATE_ACTIVITY_LOG
)
from app.models.project import ProjectCreate
from app.utils.exceptions import ValidationError


class ProjectService:
    """Service for project operations."""

    @staticmethod
    async def create_project(
            hasura: HasuraClient,
            project_data: ProjectCreate
    ) -> Dict[str, Any]:
        """
        Create a new project.

        Args:
            hasura: Hasura client with user context
            project_data: Project creation data

        Returns:
            dict: Created project data

        Raises:
            ValidationError: If project key already exists in workspace
        """
        # Check if project key already exists in workspace
        result = await hasura.query(
            GET_PROJECT_BY_KEY,
            {
                "workspace_id": project_data.workspace_id,
                "key": project_data.key
            }
        )

        if result.get("projects"):
            raise ValidationError(
                f"Project with key '{project_data.key}' already exists in this workspace",
                field="key"
            )

        # Create the project
        variables = {
            "object": {
                "workspace_id": project_data.workspace_id,
                "name": project_data.name,
                "description": project_data.description,
                "key": project_data.key,
                "color": project_data.color
            }
        }

        result = await hasura.mutate(CREATE_PROJECT, variables)
        project = result["insert_projects_one"]

        return project

    @staticmethod
    async def calculate_project_stats(
            hasura: HasuraClient,
            project_id: str
    ) -> Dict[str, Any]:
        """
        Calculate project statistics.

        Args:
            hasura: Hasura client with user context
            project_id: Project ID

        Returns:
            dict: Project statistics
        """
        from app.clients.graphql_queries import GET_PROJECT_STATS

        result = await hasura.query(GET_PROJECT_STATS, {"project_id": project_id})
        project = result.get("projects_by_pk")

        if not project:
            raise ValidationError(f"Project {project_id} not found")

        total_tasks = project["tasks_aggregate"]["aggregate"]["count"]
        done_tasks = project["done_tasks"]["aggregate"]["count"]

        # Count by status
        tasks_by_status = {}
        for task in project["tasks_by_status"]["nodes"]:
            status = task["status"]
            tasks_by_status[status] = tasks_by_status.get(status, 0) + 1

        # Count by priority
        tasks_by_priority = {}
        for task in project["tasks_by_priority"]["nodes"]:
            priority = task["priority"]
            tasks_by_priority[priority] = tasks_by_priority.get(priority, 0) + 1

        # Calculate completion rate
        completion_rate = (done_tasks / total_tasks * 100) if total_tasks > 0 else 0

        return {
            "total_tasks": total_tasks,
            "tasks_by_status": tasks_by_status,
            "tasks_by_priority": tasks_by_priority,
            "completion_rate": round(completion_rate, 2)
        }

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