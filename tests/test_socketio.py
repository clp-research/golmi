import json
from pathlib import Path
import unittest

from app.app import app, socketio, AUTH
from app import DEFAULT_CONFIG_FILE

# directory html is served from
TEMPLATE_DIR = "app/pentomino/templates"
# directory containing resources
RESOURCE_DIR = "app/pentomino/static/resources"


class ConnectionTest(unittest.TestCase):
    """
    Test connection and authentication to the server.
    """
    def setUp(self):
        """
        Create new flask and socketio test clients.
        """
        self.flask_client = app.test_client()
        # create an unauthenticated client
        self.socketio_client = socketio.test_client(
            app, flask_test_client=self.flask_client,
            auth={"password": AUTH}
        )
        app.config[DEFAULT_CONFIG_FILE] = (
            "app/pentomino/static/resources/config/pentomino_config.json"
        )

        self.socketio_client.disconnect()

    def tearDown(self):
        """
        If necessary, disconnect the socketio test client.
        """
        if self.socketio_client.is_connected():
            self.socketio_client.disconnect()

    def test_connection(self):
        """
        Test client connection with and without authentication.
        """
        self.assertFalse(self.socketio_client.is_connected())

        # provide authentication
        self.socketio_client.connect(auth={"password": AUTH})
        self.assertTrue(self.socketio_client.is_connected())

    def test_initial_messages(self):
        """
        Make sure the initial configuration
        and an empty state were sent.
        """
        # connect the socketio test client
        self.socketio_client.connect(auth={"password": AUTH})

        # obtain received objects
        received = self.socketio_client.get_received()

        received_config = False
        received_state = False

        for event in received:
            if event["name"] == "update_config":
                received_config = True
            elif event["name"] == "update_state":
                received_state = True
                # make sure state is empty
                self.assertEqual(len(event["args"][0]["grippers"]), 0)
                self.assertEqual(len(event["args"][0]["objs"]), 0)

        # assert both configuration and state were sent
        self.assertTrue(received_state)
        self.assertTrue(received_config)


class SocketTest(unittest.TestCase):
    """
    Base class implementing setup and teardown functionality for unit tests
    using socket events.
    """
    def setUp(self):
        """
        Create new flask and socketio test clients, connect to the server
        and remove the initial messages.
        """
        self.flask_client = app.test_client()
        # connect to the server
        self.socketio_client = socketio.test_client(
            app, flask_test_client=self.flask_client, auth={"password": AUTH}
        )
        # remove initially sent state and config
        self.socketio_client.get_received()

    def tearDown(self):
        """
        Disconnect the socketio test client.
        """
        if self.socketio_client.is_connected():
            self.socketio_client.disconnect()

    @staticmethod
    def read_json(filename):
        """
        @param filename file path relative to the resource directory. No / in
                        the beginning!
        @return parsed json as dict
        """
        file_path = Path(RESOURCE_DIR) / filename
        return json.loads(file_path.read_text())

    def load_state(self, filename):
        """
        @param filename state file, path is relative to the resource directory
                        and without / in the beginning
        @return tuple: (sent, received), where sent is the parsed json emitted
                to the server and received is the server's response, i.e., the
                (corrected) state
        """
        test_state = SocketTest.read_json(filename)
        self.socketio_client.emit("load_state", test_state)
        return test_state, self.socketio_client.get_received()

    def load_config(self, filename):
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

    def load_default_config_with_params(self, params):
        """
        Load a default Pentomino config, but modify the specified parameters.
        @param params   dict with settings that should be changed from default
        @return tuple: (sent, received), where sent is the parsed json emitted
                to the server and received is the server's response, i.e., the
                (corrected) config
        """
        default_config = SocketTest.read_json("config/pentomino_config.json")
        default_config.update(params)
        self.socketio_client.emit("load_config", default_config)
        return default_config, self.socketio_client.get_received()


class SocketEventTest(SocketTest):
    """
    Test event-based socket communication.
    """
    def test_load_state(self):
        """
        test if loading a state from a configuration file works
        """
        test_state, received = self.load_state("tasks/test_state.json")

        # make sure just one event was received
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["name"], "update_state")

        # make sure the received objects are equal (or subset) to the sent one
        # grippers
        for gripper in received[0]["args"][0]["grippers"]:
            # obtain gripper dict
            received_gripper = received[0]["args"][0]["grippers"][gripper]
            sent_gripper = test_state["grippers"][gripper]

            # sent should be a subset of received
            self.assertTrue(sent_gripper.items() <= received_gripper.items())

        # objects
        for obj in received[0]["args"][0]["objs"]:
            # obtain object dictionary
            received_obj = received[0]["args"][0]["objs"][obj]
            sent_obj = test_state["objs"][obj]

            # sent should be a subset of received
            self.assertTrue(sent_obj.items() <= received_obj.items())

    def test_reset_state(self):
        """
        Test resetting the model to an empty state.
        """
        test_state, received = self.load_state("tasks/test_state.json")

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["name"], "update_state")
        # make sure there are some grippers and objects now
        self.assertTrue(len(received[0]["args"][0]["grippers"]) > 0)
        self.assertTrue(len(received[0]["args"][0]["objs"]) > 0)

        # delete the state
        self.socketio_client.emit("reset_state")
        # make sure the received updated state is empty
        received = self.socketio_client.get_received()
        self.assertTrue(len(received[0]["args"][0]["grippers"]) == 0)
        self.assertTrue(len(received[0]["args"][0]["objs"]) == 0)

    def test_load_config(self):
        """
        test sending a configuration
        """
        test_config, received = self.load_config("config/test_config.json")

        # make sure just one event was received
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["name"], "update_config")

        # check the config was updated correctly. Here, the subset notion
        # cannot be used because not all properties are sent back by the model.
        for setting, value in test_config.items():
            if setting in received[0]["args"][0]:
                self.assertEqual(value, received[0]["args"][0][setting])

    def test_gripper_movement(self):
        """
        test movements of grippers
        """
        # configuration
        test_gripper = "0"
        test_step_size = 0.5

        self.load_default_config_with_params({"move_step": test_step_size})
        test_state, received = self.load_state("tasks/test_state.json")

        # send movement
        self.socketio_client.emit("move", {
            "id": test_gripper,
            "dx": 1,
            "dy": 0
        })
        received = self.socketio_client.get_received()

        # make sure we only received one object
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["name"], "update_grippers")

        # make sure new coordinates are correct
        new_x = received[0]["args"][0][test_gripper]["x"]
        old_x = test_state["grippers"][test_gripper]["x"]
        self.assertEqual(new_x, old_x + test_step_size)

    def test_rotate_object(self):
        test_state, received = self.load_state("tasks/gripped_test.json")

        # configuration
        test_gripper = "0"
        rotation = -1
        obj = "4"

        self.socketio_client.emit("rotate", {
            "id": test_gripper,
            "direction": rotation
        })
        received = self.socketio_client.get_received()
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["name"], "update_grippers")

        original_rotation = test_state["objs"][obj]["rotation"]
        new_rotation = (
            received[0]["args"][0][test_gripper]["gripped"][obj]["rotation"]
        )

        movement = abs(original_rotation - new_rotation)
        self.assertEqual(movement, 90)

    def test_rotate_empty_gripper(self):
        """
        rotation of an empty gripper
        """
        test_state, received = self.load_state("tasks/test_state.json")

        # configuration
        test_gripper = "0"
        rotation = -1

        self.socketio_client.emit("rotate", {
            "id": test_gripper,
            "direction": rotation
        })

        received = self.socketio_client.get_received()

        # mover always sends an update
        self.assertEqual(len(received), 1)

    def test_flip_object(self):
        test_state, received = self.load_state("tasks/gripped_test.json")

        # configuration
        test_gripper = "0"
        obj = "4"

        self.socketio_client.emit("flip", {
            "id": test_gripper
        })

        received = self.socketio_client.get_received()

        # make sure only one object was sent
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["name"], "update_grippers")

        # check if object was mirrored
        original_flip = test_state["objs"][obj]["mirrored"]
        new_flip = (
            received[0]["args"][0][test_gripper]["gripped"][obj]["mirrored"]
        )

        flipped = original_flip != new_flip
        self.assertTrue(flipped)

    def test_grip_object(self):
        """Test gripping and ungripping an object."""
        test_state, received = self.load_state("tasks/gripped_test.json")

        # configuration
        gr = "0"
        obj = "4"

        # make sure the object is gripped right now
        is_gripped = list(
                received[0]["args"][0]["grippers"][gr]["gripped"].keys()
            )
        self.assertTrue(is_gripped >= [obj])
        self.assertTrue(received[0]["args"][0]["objs"][obj]["gripped"])

        # ungrip
        self.socketio_client.emit("grip", {"id": gr})
        received = self.socketio_client.get_received()

        # make sure object is not gripped anymore
        self.assertEqual(len(received), 2)
        obj_gripped = True
        gr_has_gripped = True
        for msg in received:
            if msg["name"] == "update_objs":
                obj_gripped = msg["args"][0][obj]["gripped"]
            elif msg["name"] == "update_grippers":
                gr_has_gripped = (msg["args"][0][gr]["gripped"] is not None and
                                  msg["args"][0][gr]["gripped"].get(obj))

        self.assertFalse(obj_gripped)
        self.assertFalse(gr_has_gripped)

        # grip
        self.socketio_client.emit("grip", {"id": gr})
        received = self.socketio_client.get_received()

        # make sure object is not gripped anymore
        self.assertEqual(len(received), 2)
        for msg in received:
            if msg["name"] == "update_objs":
                obj_gripped = msg["args"][0][obj]["gripped"]
            elif msg["name"] == "update_grippers":
                gr_has_gripped = (msg["args"][0][gr]["gripped"] is not None and
                                  obj in msg["args"][0][gr]["gripped"].keys())

        self.assertTrue(obj_gripped)
        self.assertTrue(gr_has_gripped)


class ConfigTest(SocketTest):
    """
    Tests ensuring configuration parameters are working correctly.
    """
    def test_snap_to_grid(self):
        # set snap_to_grid and set move_step below 1
        self.load_default_config_with_params({"snap_to_grid": True,
                                              "move_step": 0.5})
        _, received_state = self.load_state("tasks/gripped_test.json")

        test_gripper = "0"
        test_obj = "4"

        for dimension in ["x", "y"]:
            # make sure we start at a full block:
            start_state = received_state[0]["args"][0]
            start_pos = start_state["objs"][test_obj][dimension]
            self.assertEqual(start_pos % 1, 0,
                             "Error in test state for test_snap_to_grid."
                             f"Object {test_obj} must start at a full block "
                             "(e.g., 10.0).")

            # move half a block to trigger "snap to grid"
            self.socketio_client.emit("move", {
                "id": test_gripper,
                "dx": 1 if dimension == "x" else 0,
                "dy": 1 if dimension == "y" else 0,
                "loop": False
            })
            # release the object
            self.socketio_client.emit("grip", {"id": test_gripper})

            # check whether the object "snapped back" to the nearest block
            received_updates = self.socketio_client.get_received()
            for update in received_updates:
                if update["name"] == "update_objs":
                    self.assertEqual(
                        update["args"][0][test_obj][dimension] % 1, 0
                    )
                    return
            raise RuntimeError("Did not receive 'update_objs' update")

    # --- create more test cases for extensions below --- #
