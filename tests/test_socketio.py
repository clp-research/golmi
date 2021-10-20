import json
from pathlib import Path
import unittest

from app import app, socketio, AUTH


# directory html is served from
TEMPLATE_DIR = "app/templates"
# directory containing resources
RESOURCE_DIR = "app/static/resources"

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
            app, flask_test_client=self.flask_client
        )

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


class SocketEventTest(unittest.TestCase):
    """
    Test event-based socket communication.
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

    def test_load_state(self):
        """
        test if loading a state from a configuration file works
        """
        # read state file as string and parse to dictionary
        file_path = Path(f"{RESOURCE_DIR}/tasks/test_state.json")
        with open(file_path, "r", encoding="utf-8") as f:
            test_state_json = json.load(f)

        # send state as dictionary
        self.socketio_client.emit("load_state", test_state_json)
        received = self.socketio_client.get_received()

        # make sure just one event was received
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["name"], "update_state")

        # make sure the received objects are equal (or subset) to the sent one
        # grippers
        for gripper in received[0]["args"][0]["grippers"]:
            # obtain gripper dict
            received_gripper = received[0]["args"][0]["grippers"][gripper]
            sent_gripper = test_state_json["grippers"][gripper]

            # sent should be a subset of received
            self.assertTrue(sent_gripper.items() <= received_gripper.items())

        # objects
        for obj in received[0]["args"][0]["objs"]:
            # obtain object dictionary
            received_obj = received[0]["args"][0]["objs"][obj]
            sent_obj = test_state_json["objs"][obj]

            # sent should be a subset of received
            self.assertTrue(sent_obj.items() <= received_obj.items())

    def test_reset_state(self):
        """
        Test resetting the model to an empty state.
        """
        # first send some state
        # read state file as string
        file_path = Path(f"{RESOURCE_DIR}/tasks/test_state.json")
        with open(file_path, "r", encoding="utf-8") as f:
            test_state = json.loads(f.read())
        self.socketio_client.emit("load_state", test_state)
        received = self.socketio_client.get_received()
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
        # read config from a file and parse to dictionary
        file_path = Path(f"{RESOURCE_DIR}/config/test_config.json")
        with open(file_path, "r", encoding="utf-8") as f:
            test_config = json.loads(f.read())

        # send state as dictionary
        self.socketio_client.emit("load_config", test_config)
        received = self.socketio_client.get_received()

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
        test movements of grippers with normal
        and user defined step size
        """
        # send a state
        file_path = Path(f"{RESOURCE_DIR}/tasks/test_state.json")
        with open(file_path, "r", encoding="utf-8") as f:
            test_state_json = json.load(f)

        # send state as dictionary
        self.socketio_client.emit("load_state", test_state_json)
        self.socketio_client.get_received()

        # configuration
        test_gripper = "0"
        test_step_size = 0.5

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
        old_x = test_state_json["grippers"][test_gripper]["x"]
        self.assertEqual(new_x, old_x + test_step_size)

        # test bigger movement on y coordinate
        test_step_size = 4
        self.socketio_client.emit("move", {
            "id": test_gripper,
            "dx": 0,
            "dy": 1,
            "step_size": test_step_size
        })
        received = self.socketio_client.get_received()

        # make sure we only received one object
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["name"], "update_grippers")

        # make sure new coordinates are correct
        new_y = received[0]["args"][0][test_gripper]["y"]
        old_y = test_state_json["grippers"][test_gripper]["y"]
        self.assertEqual(new_y, old_y + test_step_size)

    def test_rotate_object(self):
        # send a state
        file_path = Path(f"{RESOURCE_DIR}/tasks/gripped_test.json")
        with open(file_path, "r", encoding="utf-8") as f:
            test_state_json = json.load(f)

        # send state as dictionary
        self.socketio_client.emit("load_state", test_state_json)
        self.socketio_client.get_received()

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

        original_rotation = test_state_json["objs"][obj]["rotation"]
        new_rotation = (
            received[0]["args"][0][test_gripper]["gripped"][obj]["rotation"]
        )

        movement = abs(original_rotation - new_rotation)
        self.assertEqual(movement, 90)

    def test_rotate_empty_gripper(self):
        """
        rotation of an empty gripper
        """
        # send a state
        file_path = Path(f"{RESOURCE_DIR}/tasks/test_state.json")
        with open(file_path, "r", encoding="utf-8") as f:
            test_state_json = json.load(f)

        # send state as dictionary
        self.socketio_client.emit("load_state", test_state_json)
        self.socketio_client.get_received()

        # configuration
        test_gripper = "0"
        rotation = -1

        self.socketio_client.emit("rotate", {
            "id": test_gripper,
            "direction": rotation
        })

        received = self.socketio_client.get_received()

        # no update should have been sent
        self.assertEqual(len(received), 0)

    def test_flip_object(self):
        # send a state
        file_path = Path(f"{RESOURCE_DIR}/tasks/gripped_test.json")
        with open(file_path, "r", encoding="utf-8") as f:
            test_state_json = json.load(f)

        # send state as dictionary
        self.socketio_client.emit("load_state", test_state_json)
        self.socketio_client.get_received()

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
        original_flip = test_state_json["objs"][obj]["mirrored"]
        new_flip = (
            received[0]["args"][0][test_gripper]["gripped"][obj]["mirrored"]
        )

        flipped = original_flip != new_flip
        self.assertTrue(flipped)

    def test_grip_object(self):
        """Test gripping and ungripping an object."""
        # send a state were an object is already gripped
        file_path = Path(f"{RESOURCE_DIR}/tasks/gripped_test.json")
        with open(file_path, "r", encoding="utf-8") as f:
            test_state_json = json.load(f)
        
        # send state as dictionary
        self.socketio_client.emit("load_state", test_state_json)
        received = self.socketio_client.get_received()

        # configuration
        gr = "0"
        obj = "4"

        # make sure the object is gripped right now
        self.assertTrue(
            list(received[0]["args"][0]["grippers"][gr]["gripped"].keys()) >= [obj]
        )
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
                gr_has_gripped = msg["args"][0][gr]["gripped"] is not None and \
                    obj in msg["args"][0][gr]["gripped"].keys()

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
                gr_has_gripped = msg["args"][0][gr]["gripped"] is not None and \
                    obj in msg["args"][0][gr]["gripped"].keys()

        self.assertTrue(obj_gripped)
        self.assertTrue(gr_has_gripped)

    # --- create more test cases for extensions below --- #