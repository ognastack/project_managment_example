"""
GraphQL queries and mutations for Hasura.

All queries use variables for safety.
Never use string interpolation.
"""

# ============================================================================
# WORKSPACE QUERIES
# ============================================================================

GET_WORKSPACES = """
query GetWorkspaces($limit: Int!, $offset: Int!) {
  workspaces(limit: $limit, offset: $offset, order_by: {created_at: desc}) {
    id
    name
    slug
    description
    created_by
    created_at
    updated_at
    members {
      id
      role
      user_id
      workspace_id
      joined_at
    }
    projects {
      id
    }
  }
  workspaces_aggregate {
    aggregate {
      count
    }
  }
}
"""

GET_WORKSPACE_BY_ID = """
query GetWorkspaceById($id: uuid!) {
  workspaces_by_pk(id: $id) {
    id
    name
    slug
    description
    created_by
    created_at
    updated_at
    members {
      id
      user_id
      role
      joined_at
      workspace_id
      auth_user {
        id
        email
      }
    }
    projects {
        name
        description
    }
  }
}
"""

GET_WORKSPACE_BY_SLUG = """
query GetWorkspaceBySlug($slug: String!) {
    workspaces(where: {slug: {_eq: $slug}}, limit: 1) {
        id
        name
        slug
        description
        created_by
        created_at
        updated_at
        members {
            id
            user_id
            role
            joined_at
            workspace_id
        }
    }
}
"""

CREATE_WORKSPACE = """
mutation CreateWorkspace($object: workspaces_insert_input!) {
    insert_workspaces_one(object: $object) {
        id
        name
        slug
        description
        created_by
        created_at
        updated_at
    }
}
"""

UPDATE_WORKSPACE = """
mutation UpdateWorkspace($id: uuid!, $updates: workspaces_set_input!) {
    update_workspaces_by_pk(
        pk_columns: {id: $id},
        _set: $updates
    ) {
        id
        name
        slug
        description
        created_by
        created_at
        updated_at
    }
}
"""

DELETE_WORKSPACE = """
mutation DeleteWorkspace($id: uuid!) {
    delete_workspaces_by_pk(id: $id) {
        id
    }
}
"""

# ============================================================================
# WORKSPACE MEMBERS QUERIES
# ============================================================================

GET_WORKSPACE_MEMBERS = """
query GetWorkspaceMembers($workspace_id: uuid!) {
    workspace_members(
        where: {workspace_id: {_eq: $workspace_id}},
        order_by: {joined_at: asc}
    ) {
        id
        user_id
        workspace_id
        role
        joined_at
        auth_user {
            id
            email
        }
    }
}
"""

ADD_WORKSPACE_MEMBER = """
mutation AddWorkspaceMember($object: workspace_members_insert_input!) {
    insert_workspace_members_one(object: $object) {
        id
        workspace_id
        user_id
        role
        joined_at
    }
}
"""

UPDATE_MEMBER_ROLE = """
mutation UpdateMemberRole($id: uuid!, $role: user_role!) {
    update_workspace_members_by_pk(
        pk_columns: {id: $id},
        _set: {role: $role}
    ) {
        id
        user_id
        role
    }
}
"""

REMOVE_WORKSPACE_MEMBER = """
mutation RemoveUserFromSpecificWorkspace($workspaceId: uuid!, $userId: uuid!) {
  delete_workspace_members(
    where: {
      workspace_id: {_eq: $workspaceId},
      user_id: {_eq: $userId}
    }
  ) {
    affected_rows
  }
}
"""

GET_USER_ROLE_IN_WORKSPACE = """
query GetUserRoleInWorkspace($workspace_id: uuid!) {
    workspace_members(
        where: {
            workspace_id: {_eq: $workspace_id}
        },
        limit: 1
    ) {
        role
    }
}
"""

# ============================================================================
# PROJECT QUERIES
# ============================================================================

GET_PROJECTS = """
query GetProjects($workspace_id: uuid!, $limit: Int!, $offset: Int!, $include_archived: Boolean!) {
    projects(
        where: {
            workspace_id: {_eq: $workspace_id},
            is_archived: {_eq: $include_archived}
        },
        limit: $limit,
        offset: $offset,
        order_by: {created_at: desc}
    ) {
        id
        workspace_id
        name
        description
        key
        color
        is_archived
        created_by
        created_at
        updated_at
        tasks {
          id
          status
          task_number
          title
        }
    }
}
"""

GET_PROJECT_BY_ID = """
query GetProjectById($id: uuid!) {
    projects_by_pk(id: $id) {
        id
        workspace_id
        name
        description
        key
        color
        is_archived
        created_by
        created_at
        updated_at
        tasks {
          id
          status
          task_number
          title
        }
    }
}
"""

GET_PROJECT_BY_KEY = """
query GetProjectByKey($workspace_id: uuid!, $key: String!) {
    projects(
        where: {
            workspace_id: {_eq: $workspace_id},
            key: {_eq: $key}
        },
        limit: 1
    ) {
        id
        workspace_id
        name
        description
        key
        color
        is_archived
        created_by
        created_at
        updated_at
    }
}
"""

CREATE_PROJECT = """
mutation CreateProject($object: projects_insert_input!) {
    insert_projects_one(object: $object) {
        id
        workspace_id
        name
        description
        key
        color
        is_archived
        created_at
        updated_at
    }
}
"""

UPDATE_PROJECT = """
mutation UpdateProject($id: uuid!, $updates: projects_set_input!) {
    update_projects_by_pk(
        pk_columns: {id: $id},
        _set: $updates
    ) {
        id
        workspace_id
        name
        description
        key
        color
        is_archived
        created_by
        created_at
        updated_at
    }
}
"""

DELETE_PROJECT = """
mutation DeleteProject($id: uuid!) {
    delete_projects_by_pk(id: $id) {
        id
    }
}
"""

GET_PROJECT_STATS = """
query GetProjectStats($project_id: uuid!) {
    projects_by_pk(id: $project_id) {
        tasks_aggregate {
            aggregate {
                count
            }
        }
        tasks_by_status: tasks_aggregate {
            nodes {
                status
            }
        }
        tasks_by_priority: tasks_aggregate {
            nodes {
                priority
            }
        }
        done_tasks: tasks_aggregate(where: {status: {_eq: done}}) {
            aggregate {
                count
            }
        }
    }
}
"""

# ============================================================================
# ACTIVITY LOG QUERIES
# ============================================================================

GET_WORKSPACE_ACTIVITY = """
query GetWorkspaceActivity($workspace_id: uuid!, $limit: Int!, $offset: Int!) {
    activity_logs(
        where: {workspace_id: {_eq: $workspace_id}},
        limit: $limit,
        offset: $offset,
        order_by: {created_at: desc}
    ) {
        id
        user_id
        activity_type
        entity_type
        entity_id
        metadata
        created_at
        actor {
            id
            email
        }
    }
    activity_logs_aggregate(where: {workspace_id: {_eq: $workspace_id}}) {
        aggregate {
            count
        }
    }
}
"""

CREATE_ACTIVITY_LOG = """
mutation CreateActivityLog($object: activity_logs_insert_input!) {
    insert_activity_logs_one(object: $object) {
        id
        workspace_id
        user_id
        activity_type
        entity_type
        entity_id
        metadata
        created_at
    }
}
"""