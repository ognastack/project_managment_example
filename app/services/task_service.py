"""
Business logic for task management.

This service layer enforces business rules like status transitions
while delegating data access to Hasura.
"""
from typing import Dict, Any, List
from app.clients.hasura import HasuraClient
from app.models.task import TaskStatus, TaskCreate, TaskUpdate
from app.utils.exceptions import InvalidStatusTransitionError, ValidationError

# Valid status transitions
VALID_TRANSITIONS: Dict[TaskStatus, List[TaskStatus]] = {
    TaskStatus.BACKLOG: [TaskStatus.TODO],
    TaskStatus.TODO: [TaskStatus.IN_PROGRESS, TaskStatus.BACKLOG],
    TaskStatus.IN_PROGRESS: [TaskStatus.BLOCKED, TaskStatus.DONE, TaskStatus.TODO],
    TaskStatus.BLOCKED: [TaskStatus.IN_PROGRESS, TaskStatus.TODO],
    TaskStatus.DONE: [TaskStatus.TODO],  # Allow reopening
}


class TaskService:
    """Service for task operations."""

    @staticmethod
    def validate_status_transition(from_status: TaskStatus, to_status: TaskStatus) -> None:
        """
        Validate if a status transition is allowed.

        Args:
            from_status: Current task status
            to_status: Desired task status

        Raises:
            InvalidStatusTransitionError: If transition is not allowed
        """
        if from_status == to_status:
            return  # No transition needed

        allowed_transitions = VALID_TRANSITIONS.get(from_status, [])
        if to_status not in allowed_transitions:
            raise InvalidStatusTransitionError(from_status.value, to_status.value)

    @staticmethod
    async def create_task(
            hasura: HasuraClient,
            task_data: TaskCreate
    ) -> Dict[str, Any]:
        """
        Create a new task.

        Args:
            hasura: Hasura client with user context
            task_data: Task creation data

        Returns:
            dict: Created task data
        """
        # Get next task number for the project

        next_number = 1

        # Create the task
        mutation = """
        mutation CreateTask($object: tasks_insert_input!) {
            insert_tasks_one(object: $object) {
                id
                project_id
                title
                description
                status
                priority
                task_number
                due_date
                created_at
                updated_at
                created_by
            }
        }
        """

        variables = {
            "object": {
                "project_id": task_data.project_id,
                "title": task_data.title,
                "description": task_data.description,
                "status": task_data.status.value,
                "priority": task_data.priority.value,
                "task_number": next_number,
                "due_date": task_data.due_date.isoformat() if task_data.due_date else None
            }
        }

        result = await hasura.mutate(mutation, variables)

        return result["insert_tasks_one"]

    @staticmethod
    async def update_task_status(
            hasura: HasuraClient,
            task_id: str,
            new_status: TaskStatus
    ) -> Dict[str, Any]:
        """
        Update task status with validation.

        Args:
            hasura: Hasura client with user context
            task_id: Task ID
            new_status: New status

        Returns:
            dict: Updated task data

        Raises:
            InvalidStatusTransitionError: If transition is invalid
        """
        # Get current task
        query = """
        query GetTask($id: uuid!) {
            tasks_by_pk(id: $id) {
                id
                status
                project {
                    workspace_id
                }
            }
        }
        """

        result = await hasura.query(query, {"id": task_id})
        task = result.get("tasks_by_pk")

        if not task:
            raise ValidationError(f"Task {task_id} not found")

        current_status = TaskStatus(task["status"])

        # Validate transition
        TaskService.validate_status_transition(current_status, new_status)

        # Update status
        mutation = """
        mutation UpdateTaskStatus($id: uuid!, $status: task_status!) {
            update_tasks_by_pk(
                pk_columns: {id: $id},
                _set: {status: $status}
            ) {
                id
                status
                updated_at
                created_at
                created_by
                project_id
                title
                description
                task_number
            }
        }
        """

        result = await hasura.mutate(
            mutation,
            {"id": task_id, "status": new_status.value}
        )

        return result["update_tasks_by_pk"]

    @staticmethod
    async def _log_activity(
            hasura: HasuraClient,
            task_id: str,
            user_id: str,
            activity_type: str,
            workspace_id: str = None,
            metadata: Dict[str, Any] = None
    ) -> None:
        """Log an activity to activity_logs table."""
        # If workspace_id not provided, fetch it
        if not workspace_id:
            query = """
            query GetWorkspace($task_id: uuid!) {
                tasks_by_pk(id: $task_id) {
                    project {
                        workspace_id
                    }
                }
            }
            """
            result = await hasura.query(query, {"task_id": task_id})
            workspace_id = result["tasks_by_pk"]["project"]["workspace_id"]

        mutation = """
        mutation LogActivity($object: activity_logs_insert_input!) {
            insert_activity_logs_one(object: $object) {
                id
            }
        }
        """

        variables = {
            "object": {
                "workspace_id": workspace_id,
                "user_id": user_id,
                "activity_type": activity_type,
                "entity_type": "task",
                "entity_id": task_id,
                "metadata": metadata or {}
            }
        }

        await hasura.mutate(mutation, variables)