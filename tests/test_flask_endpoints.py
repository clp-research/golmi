import unittest

from app import app

# Endpoints that return html upon a GET request
SERVED_PAGES = ["/", "/demo", "/pento_fractions/record", "/pento_fractions/replay"]


class Test(unittest.TestCase):
    """
    Test flask app
    """

    flask_test_client = app.test_client()

    def test_get_response(self):
        """Test for GET endpoints"""
        for page in SERVED_PAGES:
            get_response = self.flask_test_client.get(page)
            self.assertEqual(get_response.status, "200 OK")

    def test_post_response(self):
        """Test for POST endpoints"""
        for page in SERVED_PAGES:
            post_response = self.flask_test_client.post(page)
            self.assertEqual(post_response.status, "405 METHOD NOT ALLOWED")

    def test_post_logs(self):
        """Test for saving logs"""
        # post without data
        savelog_invalid1 = self.flask_test_client.post("/logs")
        self.assertEqual(savelog_invalid1.status, "400 BAD REQUEST")

        # post with non-json data
        savelog_invalid2 = self.flask_test_client.post(
            "/logs", data="absolutely_not_json"
        )
        self.assertEqual(savelog_invalid2.status, "400 BAD REQUEST")

    def test_get_logs(self):
        """Test for retrieving logs"""
        # Ensure any request to non-existant files is rejected
        getlog_invalid1 = self.flask_test_client.get(
            "/logs/super_secret_file.json")
        self.assertEqual(getlog_invalid1.status, "404 NOT FOUND")
        # attempt to get file in other directory
        # TODO
        getlog_invalid2 = self.flask_test_client.get(
            "/logs/../tasks/test_state.json")
        self.assertEqual(getlog_invalid2.status, "404 NOT FOUND")
