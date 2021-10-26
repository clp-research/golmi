import unittest

from app import app
from app.views import REPLAY_DIR
from os.path import join
from os import remove
import json

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
        save_log_invalid1 = self.flask_test_client.post("/logs")
        self.assertEqual(save_log_invalid1.status, "400 BAD REQUEST")

        # post with non-json data
        save_log_invalid2 = self.flask_test_client.post(
            "/logs", data="absolutely_not_json"
        )
        self.assertEqual(save_log_invalid2.status, "400 BAD REQUEST")

    def test_get_logs(self):
        """Test for retrieving logs"""
        # ensure any request to non-existent files is rejected
        get_log_invalid = self.flask_test_client.get(
            "/logs/super_secret_file.json")
        self.assertEqual(get_log_invalid.status, "404 NOT FOUND")
        # create a file to retrieve
        test_data = {"test_key": "test_value"}
        test_file_name = "this_is_a_very_special_test_file.json"
        with open(join(REPLAY_DIR, test_file_name), mode="w") as test_file:
            test_file.write(json.dumps(test_data))
        # retrieve the file via http
        get_log_valid = self.flask_test_client.get(
            join("/logs", test_file_name))
        self.assertEqual(json.loads(get_log_valid.data), test_data)
        # delete the test file afterwards
        remove(join(REPLAY_DIR, test_file_name))
