import unittest
import requests
import json
import uuid


class TestWorkSpaces(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method"""
        self.base_url = "http://localhost:8000"
        self.signup_url = f"{self.base_url}/auth/signup"
        self.sign_in = f"{self.base_url}/auth/token?grant_type=password"

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

        self.main_user_id = response_data['user']['id']

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

        email2 = f"{str(uuid.uuid4())}@example.com"

        self.payload = {
            "email": email2,
            "password": "strongpassword"
        }

        response2 = requests.post(
            self.signup_url,
            headers=self.headers,
            data=json.dumps(self.payload)
        )

        # Assert successful response
        self.assertEqual(200, response2.status_code)  # Or 200 depending on your API

        # Check response content (adjust based on your API response)
        response_data2 = response2.json()
        self.assertIn("user", response_data2)
        response_use2 = response_data2['user']
        self.assertIn("email", response_use2)
        self.assertEqual(response_use2["email"], email2)

        self.second_user_id = response_data2['user']['id']

    def test_create_project(self):
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

    def test_list_projects(self):
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

        params = {
            "workspace_id": workspace_data['id']
        }

        project_info_response = self.session.get(f"{self.projects_url}", params=params)

        print(project_info_response.json())

    def test_get_project(self):
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

        project_info_response = self.session.get(f"{self.projects_url}/{project_data['id']}")

        project_info_data = project_info_response.json()

        self.assertEqual(project_info_data['name'], create_project_data['name'])
        self.assertEqual(project_info_data['description'], create_project_data['description'])

    def test_update_project(self):
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

        update_data = {
            "name": f"Project updated {str(uuid.uuid4())}",
            "description": f"Project updated via test {str(uuid.uuid4())}",
            "color": "#697ac2"
        }

        self.session.patch(f"{self.projects_url}/{project_data['id']}", json=update_data)

        project_info_response = self.session.get(f"{self.projects_url}/{project_data['id']}")

        project_info_data = project_info_response.json()

        self.assertEqual(project_info_data['name'], update_data['name'])
        self.assertEqual(project_info_data['description'], update_data['description'])
        self.assertEqual(project_info_data['color'], update_data['color'])

    def test_delete_project(self):
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

        self.session.delete(f"{self.projects_url}/{project_data['id']}")

        project_info_response = self.session.get(f"{self.projects_url}/{project_data['id']}")

        self.assertEqual(404, project_info_response.status_code)

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
