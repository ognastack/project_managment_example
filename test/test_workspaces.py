import unittest
import requests
import json
import uuid


class TestWorkSpaces(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method"""
        self.base_url = "http://localhost"
        self.signup_url = f"{self.base_url}/auth/signup"
        self.sign_in = f"{self.base_url}/auth/token?grant_type=password"

        self.tasks_url = f"{self.base_url}/api/v1/tasks/"
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

    def test_create_workspace(self):

        number_of_works = 3

        slugs = []
        names = []

        for x in range(0, number_of_works):
            name = f"Test workspace-{x}-{str(uuid.uuid4())[:3]}"

            slug = f"slug-{x}-{str(uuid.uuid4())[:10]}"

            names.append(name)
            slugs.append(slug)
            create_workspace_data = {
                "name": name,
                "slug": slug,
                "description": f"Workspace #{x}created from test cases"
            }

            create_workspace_response = self.session.post(self.workspaces_url, json=create_workspace_data)

            data = create_workspace_response.json()

            self.assertEqual(data['name'], name)
            self.assertEqual(data['slug'], slug)
            self.assertEqual(create_workspace_response.status_code, 201)

        list_workspace_response = self.session.get(self.workspaces_url)
        self.assertEqual(list_workspace_response.status_code, 202)

        workspace_data = list_workspace_response.json()

        self.assertEqual(len(workspace_data["workspaces"]), number_of_works)

        checked = False
        for work in workspace_data["workspaces"]:
            work_data_response = self.session.get(f"{self.workspaces_url}/{work['id']}")
            slug_data_response = self.session.get(f"{self.workspaces_url}/slug/{work['slug']}")
            work_data = work_data_response.json()
            slug_data = slug_data_response.json()

            self.assertEqual(work_data['name'], slug_data['name'])
            self.assertEqual(work_data['slug'], slug_data['slug'])

            self.assertIn(work_data['name'], names)
            self.assertIn(work_data['slug'], slugs)
            checked = True

        self.assertTrue(checked)

    def test_list_workspaces(self):
        list_workspace_response = self.session.get(self.workspaces_url)
        self.assertEqual(202,list_workspace_response.status_code )

    def test_update_workspace(self):
        number_of_works = 3

        slugs = []
        names = []

        for x in range(0, number_of_works):
            name = f"Test workspace-{x}-{str(uuid.uuid4())[:3]}"

            slug = f"slug-{x}-{str(uuid.uuid4())[:10]}"

            names.append(name)
            slugs.append(slug)
            create_workspace_data = {
                "name": name,
                "slug": slug,
                "description": f"Workspace #{x}created from test cases"
            }

            create_workspace_response = self.session.post(self.workspaces_url, json=create_workspace_data)

            data = create_workspace_response.json()

            self.assertEqual(data['name'], name)
            self.assertEqual(data['slug'], slug)
            self.assertEqual(create_workspace_response.status_code, 201)

            self.assertIn('id', data)

            work_space_id = data['id']

            update_data = {
                "name": f"Updated name work{x}",
                "description": f"Updated description work{x}"
            }

            update_response = self.session.patch(f"{self.workspaces_url}/{work_space_id}", json=update_data)

            print(update_response)
            get_work_response = self.session.get(f"{self.workspaces_url}/{work_space_id}")
            get_work = get_work_response.json()

            self.assertEqual(get_work['name'], update_data['name'])
            self.assertEqual(get_work['description'], update_data['description'])

    def test_delete_workspace(self):
        number_of_works = 3

        slugs = []
        names = []

        for x in range(0, number_of_works):
            name = f"Test workspace-{x}-{str(uuid.uuid4())[:3]}"

            slug = f"slug-{x}-{str(uuid.uuid4())[:10]}"

            names.append(name)
            slugs.append(slug)
            create_workspace_data = {
                "name": name,
                "slug": slug,
                "description": f"Workspace #{x}created from test cases"
            }

            create_workspace_response = self.session.post(self.workspaces_url, json=create_workspace_data)

            data = create_workspace_response.json()

            self.assertEqual(data['name'], name)
            self.assertEqual(data['slug'], slug)
            self.assertEqual(create_workspace_response.status_code, 201)

            self.assertIn('id', data)

            work_space_id = data['id']

            self.session.delete(f"{self.workspaces_url}/{work_space_id}")
            get_work_response = self.session.get(f"{self.workspaces_url}/{work_space_id}")
            print(get_work_response.json())
            print(get_work_response.status_code)
            self.assertEqual(404,get_work_response.status_code)

    def test_get_work_space_members(self):
        number_of_works = 3

        slugs = []
        names = []

        for x in range(0, number_of_works):
            name = f"Test workspace-{x}-{str(uuid.uuid4())[:3]}"

            slug = f"slug-{x}-{str(uuid.uuid4())[:10]}"

            names.append(name)
            slugs.append(slug)
            create_workspace_data = {
                "name": name,
                "slug": slug,
                "description": f"Workspace #{x}created from test cases"
            }

            create_workspace_response = self.session.post(self.workspaces_url, json=create_workspace_data)

            data = create_workspace_response.json()

            self.assertEqual(data['name'], name)
            self.assertEqual(data['slug'], slug)
            self.assertEqual(create_workspace_response.status_code, 201)

            self.assertIn('id', data)

            work_space_id = data['id']

            members_responses = self.session.get(f"{self.workspaces_url}/{work_space_id}/members")

            for mem in members_responses.json():
                self.assertIn('user_id', mem)
                self.assertEqual(mem['user_id'], self.main_user_id)

    def test_add_work_space_member(self):
        number_of_works = 3

        slugs = []
        names = []

        for x in range(0, number_of_works):
            name = f"Test workspace-{x}-{str(uuid.uuid4())[:3]}"

            slug = f"slug-{x}-{str(uuid.uuid4())[:10]}"

            names.append(name)
            slugs.append(slug)
            create_workspace_data = {
                "name": name,
                "slug": slug,
                "description": f"Workspace #{x}created from test cases"
            }

            create_workspace_response = self.session.post(self.workspaces_url, json=create_workspace_data)

            data = create_workspace_response.json()

            self.assertEqual(data['name'], name)
            self.assertEqual(data['slug'], slug)
            self.assertEqual(create_workspace_response.status_code, 201)

            self.assertIn('id', data)

            work_space_id = data['id']

            add_data = {
                "user_id": self.second_user_id,
                "role": "member"
            }

            self.session.post(f"{self.workspaces_url}/{work_space_id}/members", json=add_data)

            members_responses = self.session.get(f"{self.workspaces_url}/{work_space_id}/members")

            members_data = members_responses.json()

            self.assertEqual(len(members_data), 2)

            for mem in members_data:
                self.assertIn('user_id', mem)
                self.assertIn(mem['user_id'], [self.second_user_id, self.main_user_id])

    def test_delete_member(self):
        number_of_works = 3

        slugs = []
        names = []

        for x in range(0, number_of_works):
            name = f"Test workspace-{x}-{str(uuid.uuid4())[:3]}"

            slug = f"slug-{x}-{str(uuid.uuid4())[:10]}"

            names.append(name)
            slugs.append(slug)
            create_workspace_data = {
                "name": name,
                "slug": slug,
                "description": f"Workspace #{x}created from test cases"
            }

            create_workspace_response = self.session.post(self.workspaces_url, json=create_workspace_data)

            data = create_workspace_response.json()

            self.assertEqual(data['name'], name)
            self.assertEqual(data['slug'], slug)
            self.assertEqual(create_workspace_response.status_code, 201)

            self.assertIn('id', data)

            work_space_id = data['id']

            add_data = {
                "user_id": self.second_user_id,
                "role": "member"
            }

            self.session.post(f"{self.workspaces_url}/{work_space_id}/members", json=add_data)

            members_responses = self.session.get(f"{self.workspaces_url}/{work_space_id}/members")

            members_data = members_responses.json()

            self.assertEqual(len(members_data), 2)

            for mem in members_data:
                self.assertIn('user_id', mem)
                self.assertIn(mem['user_id'], [self.second_user_id, self.main_user_id])

            self.session.delete(
                f"{self.workspaces_url}/{work_space_id}/members/{self.second_user_id}")

            members_responses = self.session.get(f"{self.workspaces_url}/{work_space_id}/members")
            members_data = members_responses.json()
            self.assertEqual(len(members_data), 1)

            for mem in members_data:
                self.assertIn('user_id', mem)
                self.assertNotIn(mem['user_id'], [self.second_user_id])
                self.assertIn(mem['user_id'], [self.main_user_id])

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
