import unittest

from app.app import app
from app import DEFAULT_CONFIG_FILE, REGISTRY
from app import register_experiments


class Test(unittest.TestCase):
    """
    Test flask app
    """

    flask_test_client = app.test_client()
    app.config[DEFAULT_CONFIG_FILE] = (
        "app/pentomino/static/resources/config/pentomino_config.json"
    )
    register_experiments.register_app(app)
    pages = [experiment.ref for experiment in REGISTRY]
    save_log_endpoint = "/pentomino/save_log"

    def test_get_response(self):
        """
        tests for get endpoints
        """
        for page in self.pages:
            get_response = self.flask_test_client.get(page)
            self.assertEqual(get_response.status, "200 OK")

    def test_post_response(self):
        """
        test for post endpoints
        """
        for page in self.pages:
            post_response = self.flask_test_client.post(page)
            self.assertEqual(post_response.status, "405 METHOD NOT ALLOWED")

    def test_save_logs(self):
        """
        test for logs
        """
        # post without data
        save_log_invalid1 = self.flask_test_client.post(self.save_log_endpoint)
        self.assertEqual(save_log_invalid1.status, "400 BAD REQUEST")

        # post with non-json data
        save_log_invalid2 = self.flask_test_client.post(
            self.save_log_endpoint, data="absolutely_not_json"
        )
        self.assertEqual(save_log_invalid2.status, "400 BAD REQUEST")
