"""
Hasura GraphQL client.

CRITICAL CONSTRAINTS:
1. NEVER use admin secret
2. ALWAYS forward user JWT in headers
3. All queries use variables (no string interpolation)
"""
import httpx
from typing import Any, Dict, Optional
from app.utils.exceptions import HasuraError


class HasuraClient:
    """
    GraphQL client for Hasura.

    This client forwards the user's JWT to Hasura for row-level security.
    It NEVER uses the admin secret.
    """

    def __init__(self, url: str, token: str):
        """
        Initialize Hasura client.

        Args:
            url: Hasura GraphQL endpoint URL
            token: User JWT token (forwarded from Kong)
        """
        self.url = url
        self.token = token

    def _get_headers(self) -> Dict[str, str]:
        """
        Build request headers with user JWT.

        CRITICAL: This forwards the user JWT, NOT admin secret.
        Hasura will enforce RBAC based on JWT claims.
        """
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }

    async def execute(
            self,
            query: str,
            variables: Optional[Dict[str, Any]] = None,
            operation_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a GraphQL query or mutation.

        Args:
            query: GraphQL query/mutation string
            variables: Query variables (ALWAYS use variables, not string interpolation)
            operation_name: Optional operation name for debugging

        Returns:
            dict: Response data from Hasura

        Raises:
            HasuraError: If query fails or returns errors
        """
        payload = {
            "query": query,
            "variables": variables or {}
        }

        if operation_name:
            payload["operationName"] = operation_name

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.url,
                    json=payload,
                    headers=self._get_headers(),
                    timeout=30.0
                )
                response.raise_for_status()

                result = response.json()

                # Check for GraphQL errors
                if "errors" in result:
                    error_messages = [e.get("message", "Unknown error")
                                      for e in result["errors"]]
                    raise HasuraError(
                        f"Hasura query failed: {'; '.join(error_messages)}",
                        errors=result["errors"]
                    )

                return result.get("data", {})

            except httpx.HTTPStatusError as e:
                raise HasuraError(
                    f"HTTP error calling Hasura: {e.response.status_code}",
                    status_code=e.response.status_code
                )
            except httpx.RequestError as e:
                raise HasuraError(f"Network error calling Hasura: {str(e)}")

    async def query(
            self,
            query: str,
            variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a GraphQL query."""
        return await self.execute(query, variables)

    async def mutate(
            self,
            mutation: str,
            variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a GraphQL mutation."""
        return await self.execute(mutation, variables)