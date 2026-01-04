import unittest
import requests
import json
import uuid


class TesApiHealth(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method"""
        self.base_url = "http://localhost:8000"
        self.signup_url = f"{self.base_url}/auth/signup"
        self.sign_in = f"{self.base_url}/auth/token?grant_type=password"

        self.tasks_url = f"{self.base_url}/api/v1/tasks"
        self.projects_url = f"{self.base_url}/api/v1/projects"
        self.workspaces_url = f"{self.base_url}/api/v1/workspaces"

        self.headers = {
            "Content-Type": "application/json"
        }

        email = f"{str(uuid.uuid4())}@example.com"
        self.payload = {
            "email": email,
            "password": "strongpassword"
        }

        response = requests.post(
            self.signup_url,
            headers=self.headers,
            data=json.dumps(self.payload)
        )

        # Assert successful response
        self.assertEqual(200, response.status_code)  # Or 200 depending on your API

        # Check response content (adjust based on your API response)
        response_data = response.json()

        self.assertIn("user", response_data)
        response_use = response_data['user']
        self.assertIn("email", response_use)
        self.assertEqual(response_use["email"], email)

        response_sign_in = requests.post(self.sign_in, headers=self.headers, json=self.payload)

        self.assertIn("access_token", response_sign_in.json())

        access_token = response_sign_in.json()["access_token"]

        # Create session
        self.session = requests.session()

        # Set headers including authorization
        self.session.headers.update({
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        })

    def test_list_tasks(self):
        name = f"Test workspace-1-{str(uuid.uuid4())[:3]}"

        slug = f"slug-1-{str(uuid.uuid4())[:10]}"

        create_workspace_data = {
            "name": name,
            "slug": slug,
            "description": f"Workspace #1 created from test cases"
        }

        create_workspace_response = self.session.post(self.workspaces_url, json=create_workspace_data)

        workspace_data = create_workspace_response.json()

        self.assertIn('id', workspace_data)

        create_project_data = {
            "workspace_id": workspace_data['id'],
            "name": "Project test",
            "description": "Project created via text",
            "key": f"TEST",
        }

        create_project = self.session.post(self.projects_url, json=create_project_data)

        project_data = create_project.json()

        self.assertEqual(project_data['name'], create_project_data['name'])
        self.assertIn('id', project_data)

        project_id = project_data['id']

        create_task_data = {
            "project_id": project_id,
            "title": "Test task",
            "description": "Tas created via test",
            "status": "backlog",
            "priority": "medium",
        }

        create_task_response = self.session.post(self.tasks_url, json=create_task_data)

        self.assertEqual(create_task_response.status_code, 201)

        list_task_response = self.session.get(self.tasks_url)

        task_list = list_task_response.json()

        self.assertEqual(1, len(task_list['tasks']))

        get_task_data = task_list['tasks'][0]

        self.assertEqual(get_task_data['title'], create_task_data['title'])
        self.assertEqual(get_task_data['description'], create_task_data['description'])
        self.assertEqual(get_task_data['status'], create_task_data['status'])
        self.assertEqual(get_task_data['priority'], create_task_data['priority'])

    def test_create_task(self):
        name = f"Test workspace-1-{str(uuid.uuid4())[:3]}"

        slug = f"slug-1-{str(uuid.uuid4())[:10]}"

        create_workspace_data = {
            "name": name,
            "slug": slug,
            "description": f"Workspace #1 created from test cases"
        }

        create_workspace_response = self.session.post(self.workspaces_url, json=create_workspace_data)

        workspace_data = create_workspace_response.json()

        self.assertIn('id', workspace_data)

        create_project_data = {
            "workspace_id": workspace_data['id'],
            "name": "Project test",
            "description": "Project created via text",
            "key": f"TEST",
        }

        create_project = self.session.post(self.projects_url, json=create_project_data)

        project_data = create_project.json()

        self.assertEqual(project_data['name'], create_project_data['name'])
        self.assertIn('id', project_data)

        project_id = project_data['id']

        create_task_data = {
            "project_id": project_id,
            "title": "Test task",
            "description": "Tas created via test",
            "status": "backlog",
            "priority": "medium",
        }

        create_task_response = self.session.post(self.tasks_url, json=create_task_data)

        self.assertEqual(create_task_response.status_code, 201)

    def test_get_task(self):
        name = f"Test workspace-1-{str(uuid.uuid4())[:3]}"

        slug = f"slug-1-{str(uuid.uuid4())[:10]}"

        create_workspace_data = {
            "name": name,
            "slug": slug,
            "description": f"Workspace #1 created from test cases"
        }

        create_workspace_response = self.session.post(self.workspaces_url, json=create_workspace_data)

        workspace_data = create_workspace_response.json()

        self.assertIn('id', workspace_data)

        create_project_data = {
            "workspace_id": workspace_data['id'],
            "name": "Project test",
            "description": "Project created via text",
            "key": f"TEST",
        }

        create_project = self.session.post(self.projects_url, json=create_project_data)

        project_data = create_project.json()

        self.assertEqual(project_data['name'], create_project_data['name'])
        self.assertIn('id', project_data)

        project_id = project_data['id']

        create_task_data = {
            "project_id": project_id,
            "title": "Test task",
            "description": "Tas created via test",
            "status": "backlog",
            "priority": "medium",
        }

        create_task_response = self.session.post(self.tasks_url, json=create_task_data)

        task_data = create_task_response.json()
        self.assertIn('id', task_data)

        get_task_response = self.session.get(f"{self.tasks_url}/{task_data['id']}")

        self.assertEqual(200, get_task_response.status_code)

        get_task_data = get_task_response.json()

        self.assertEqual(get_task_data['title'], create_task_data['title'])
        self.assertEqual(get_task_data['description'], create_task_data['description'])
        self.assertEqual(get_task_data['status'], create_task_data['status'])
        self.assertEqual(get_task_data['priority'], create_task_data['priority'])

    def test_update_task(self):
        name = f"Test workspace-1-{str(uuid.uuid4())[:3]}"

        slug = f"slug-1-{str(uuid.uuid4())[:10]}"

        create_workspace_data = {
            "name": name,
            "slug": slug,
            "description": f"Workspace #1 created from test cases"
        }

        create_workspace_response = self.session.post(self.workspaces_url, json=create_workspace_data)

        workspace_data = create_workspace_response.json()

        self.assertIn('id', workspace_data)

        create_project_data = {
            "workspace_id": workspace_data['id'],
            "name": "Project test",
            "description": "Project created via text",
            "key": f"TEST",
        }

        create_project = self.session.post(self.projects_url, json=create_project_data)

        project_data = create_project.json()

        self.assertEqual(project_data['name'], create_project_data['name'])
        self.assertIn('id', project_data)

        project_id = project_data['id']

        create_task_data = {
            "project_id": project_id,
            "title": "Test tas",
            "description": "Task created via test",
            "status": "backlog",
            "priority": "medium",
        }

        create_task_response = self.session.post(self.tasks_url, json=create_task_data)

        task_data = create_task_response.json()
        self.assertIn('id', task_data)

        get_task_response = self.session.get(f"{self.tasks_url}/{task_data['id']}")

        self.assertEqual(200, get_task_response.status_code)

        get_task_data = get_task_response.json()

        self.assertEqual(get_task_data['title'], create_task_data['title'])
        self.assertEqual(get_task_data['description'], create_task_data['description'])
        self.assertEqual(get_task_data['status'], create_task_data['status'])
        self.assertEqual(get_task_data['priority'], create_task_data['priority'])

        ## UPDATE TASK

        update_task_data = {
            "project_id": project_id,
            "title": "Update task via tes",
            "description": "Task updated via test",
            "priority": "medium",
        }

        up_response = self.session.patch(f"{self.tasks_url}/{task_data['id']}", json=update_task_data)

        self.assertEqual(up_response.status_code, 200)

        get_update_task_response = self.session.get(f"{self.tasks_url}/{task_data['id']}")

        self.assertEqual(200, get_update_task_response.status_code)

        get_updated_data = get_update_task_response.json()

        self.assertEqual(get_updated_data['title'], update_task_data['title'])
        self.assertEqual(get_updated_data['description'], update_task_data['description'])
        self.assertEqual(get_updated_data['priority'], update_task_data['priority'])

    def test_update_status(self):
        name = f"Test workspace-1-{str(uuid.uuid4())[:3]}"

        slug = f"slug-1-{str(uuid.uuid4())[:10]}"

        create_workspace_data = {
            "name": name,
            "slug": slug,
            "description": f"Workspace #1 created from test cases"
        }

        create_workspace_response = self.session.post(self.workspaces_url, json=create_workspace_data)

        workspace_data = create_workspace_response.json()

        self.assertIn('id', workspace_data)

        create_project_data = {
            "workspace_id": workspace_data['id'],
            "name": "Project test",
            "description": "Project created via text",
            "key": f"TEST",
        }

        create_project = self.session.post(self.projects_url, json=create_project_data)

        project_data = create_project.json()

        self.assertEqual(project_data['name'], create_project_data['name'])
        self.assertIn('id', project_data)

        project_id = project_data['id']

        create_task_data = {
            "project_id": project_id,
            "title": "Test tas",
            "description": "Task created via test",
            "status": "backlog",
            "priority": "medium",
        }

        create_task_response = self.session.post(self.tasks_url, json=create_task_data)

        task_data = create_task_response.json()
        self.assertIn('id', task_data)

        get_task_response = self.session.get(f"{self.tasks_url}/{task_data['id']}")

        self.assertEqual(200, get_task_response.status_code)

        get_task_data = get_task_response.json()

        self.assertEqual(get_task_data['title'], create_task_data['title'])
        self.assertEqual(get_task_data['description'], create_task_data['description'])
        self.assertEqual(get_task_data['status'], create_task_data['status'])
        self.assertEqual(get_task_data['priority'], create_task_data['priority'])

        ## UPDATE TASK

        update_task_data = {
            "status":"todo"
        }

        up_response = self.session.patch(f"{self.tasks_url}/{task_data['id']}/status", json=update_task_data)

        print(up_response.status_code)
        self.assertEqual(up_response.status_code, 200)

        get_update_task_response = self.session.get(f"{self.tasks_url}/{task_data['id']}")

        self.assertEqual(200, get_update_task_response.status_code)

        get_updated_data = get_update_task_response.json()

        self.assertEqual(get_updated_data['title'], create_task_data['title'])
        self.assertEqual(get_updated_data['description'], create_task_data['description'])
        self.assertEqual(get_updated_data['priority'], create_task_data['priority'])
        self.assertEqual(get_updated_data['project_id'], create_task_data['project_id'])

        self.assertEqual(get_updated_data['status'], "todo")

    def test_delete_status(self):
        name = f"Test workspace-1-{str(uuid.uuid4())[:3]}"

        slug = f"slug-1-{str(uuid.uuid4())[:10]}"

        create_workspace_data = {
            "name": name,
            "slug": slug,
            "description": f"Workspace #1 created from test cases"
        }

        create_workspace_response = self.session.post(self.workspaces_url, json=create_workspace_data)

        workspace_data = create_workspace_response.json()

        self.assertIn('id', workspace_data)

        create_project_data = {
            "workspace_id": workspace_data['id'],
            "name": "Project test",
            "description": "Project created via text",
            "key": f"TEST",
        }

        create_project = self.session.post(self.projects_url, json=create_project_data)

        project_data = create_project.json()

        self.assertEqual(project_data['name'], create_project_data['name'])
        self.assertIn('id', project_data)

        project_id = project_data['id']

        create_task_data = {
            "project_id": project_id,
            "title": "Test tas",
            "description": "Task created via test",
            "status": "backlog",
            "priority": "medium",
        }

        create_task_response = self.session.post(self.tasks_url, json=create_task_data)

        task_data = create_task_response.json()
        self.assertIn('id', task_data)

        get_task_response = self.session.get(f"{self.tasks_url}/{task_data['id']}")

        self.assertEqual(200, get_task_response.status_code)

        get_task_data = get_task_response.json()

        self.assertEqual(get_task_data['title'], create_task_data['title'])
        self.assertEqual(get_task_data['description'], create_task_data['description'])
        self.assertEqual(get_task_data['status'], create_task_data['status'])
        self.assertEqual(get_task_data['priority'], create_task_data['priority'])

        up_response = self.session.delete(f"{self.tasks_url}/{task_data['id']}")

        print(up_response.status_code)
        self.assertEqual(up_response.status_code, 204)

        get_update_task_response = self.session.get(f"{self.tasks_url}/{task_data['id']}")

        self.assertEqual(404, get_update_task_response.status_code)


    def tearDown(self):
        """Clean up after each test"""
        # Add any cleanup code here if needed
        # For example, delete test users from database
        pass


if __name__ == '__main__':
    # Run with more verbose output
    unittest.main(verbosity=2)

    # Alternative: Run specific test
    # unittest.main(defaultTest='TestSignupAPI.test_successful_signup')
