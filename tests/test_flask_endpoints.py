import unittest

from app import app


class Test(unittest.TestCase):
    """
    Test flask app
    """

    flask_test_client = app.test_client()

    def test_get_response(self):
        """
        tests for get endpoints
        """
        for page in ["/", "/demo"]:
            get_response = self.flask_test_client.get(page)
            self.assertEqual(get_response.status, "200 OK")

    def test_post_response(self):
        """
        test for post endpoints
        """
        for page in ["/", "/demo"]:
            post_response = self.flask_test_client.post(page)
            self.assertEqual(post_response.status, "405 METHOD NOT ALLOWED")

    def test_save_logs(self):
        """
        test for logs
        """
        # post without data
        savelog_invalid1 = self.flask_test_client.post("/save_log")
        self.assertEqual(savelog_invalid1.status, "400 BAD REQUEST")

        # post with non-json data
        savelog_invalid2 = self.flask_test_client.post(
            "/save_log", data="absolutely_not_json"
        )
        self.assertEqual(savelog_invalid2.status, "400 BAD REQUEST")