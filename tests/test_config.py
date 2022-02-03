import unittest

import app.app
from model.config import Config
from tests.test_socketio import SocketTest


class ConfigSocketTest(SocketTest):
    """
    Tests on loading and updating configs via socketio events.
    """
    @staticmethod
    def get_default_config():
        default_config = app.app.get_default_config()
        default_config = Config.remove_json_comments(default_config)
        return default_config

    def load_config_from_file(self, filename):
        """
        @param filename config file, path is relative to the resource directory
                        and without / in the beginning
        @return tuple: (sent, received), where sent is the parsed json emitted
                to the server and received is the server's response, i.e., the
                (corrected) config
        """
        test_config = SocketTest.read_json(filename)
        self.socketio_client.emit("load_config", test_config)
        return test_config, self.socketio_client.get_received()

    def test_load_empty_config(self):
        config_to_load = dict()
        default_config = ConfigSocketTest.get_default_config()

        self.socketio_client.emit("load_config", config_to_load)
        received = self.socketio_client.get_received()
        received_config = received[0]["args"][0]

        self.assertDictEqual(received_config, default_config)

    def test_load_config_from_file(self):
        """
        test sending a configuration
        """
        test_config, received = self.load_config_from_file(
            "config/test_config.json")

        # make sure just one event was received
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["name"], "update_config")

        received_config = received[0]["args"][0]

        # check the sent config is a subset of the received config
        self.assertDictEqual(received_config, received_config | test_config)

    def test_load_custom_config(self):
        test_config = {"height": 42, "width": 42, "colors": ["black"],
                          "prevent_overlap": False, "move_step": 10}

        self.socketio_client.emit("load_config", test_config)
        received = self.socketio_client.get_received()
        received_config = received[0]["args"][0]

        # check the sent config is a subset of the received config
        self.assertDictEqual(received_config, received_config | test_config)

    def test_update_empty_config(self):
        # first load some custom config
        test_config, received = self.load_config_from_file(
            "config/test_config.json")
        previous_config = received[0]["args"][0]
        # then 'update' with an empty config (i.e., don't change anything)
        test_config = dict()
        self.socketio_client.emit("update_config", test_config)
        received = self.socketio_client.get_received()
        updated_config = received[0]["args"][0]

        # make sure the settings sent initially were preserved
        self.assertDictEqual(previous_config, updated_config)

    def test_update_custom_config(self):
        # first load some custom config
        test_config, received = self.load_config_from_file(
            "config/test_config.json")
        previous_config = received[0]["args"][0]

        # then update some keys
        test_config = {"verbose": True, "rotation_step": 1,
                       "lock_on_target": True,
                       "type_config": {"tiny_dot": [[1]]}}
        self.socketio_client.emit("update_config", test_config)
        received = self.socketio_client.get_received()
        updated_config = received[0]["args"][0]

        # make sure initial settings were preserved and updates were applied
        self.assertDictEqual(updated_config, previous_config | test_config)