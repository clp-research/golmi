import json
from pathlib import Path
import unittest

from app import app, socketio, AUTH


# directory html is served from
TEMPLATE_DIR = "app/templates"
# directory containing resources
RESOURCE_DIR = "app/static/resources"


class Test(unittest.TestCase):
    """
    Test socketio connections
    """
    def get_client(self, initialized=True):
        """
        create a new client instance
        if initialized is True the client will
        establish a connection and remove the
        received initial state
        """
        flask_test_client = app.test_client()

        socketio_test_client = socketio.test_client(
            app, flask_test_client=flask_test_client
        )

        # remove initial state
        if initialized:
            socketio_test_client.connect(auth=AUTH)
            socketio_test_client.get_received()

        return socketio_test_client

    def test_connection(self):
        """
        test client connection
        """
        client = self.get_client(False)

        # not connected yet
        self.assertFalse(client.is_connected())

        # establish connection
        client.connect(auth=AUTH)
        self.assertTrue(client.is_connected())

    def test_initial_configuration(self):
        """
        make sure the initial configuration
        and an empty state were sent
        """
        client = self.get_client(False)

        # establish connection
        client.connect(auth=AUTH)

        # obtain received objects
        received = client.get_received()

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

    def test_load_state(self):
        """
        test if loading a state from a configuration file works
        """
        client = self.get_client(True)

        # read config file as string
        file_path = Path(f"{RESOURCE_DIR}/tasks/pento_test.json")
        with open(file_path, "r", encoding="utf-8") as f:
            test_state_string = f.read()

        # parse to dictionary
        test_state_json = json.loads(test_state_string)

        # send state as dictionary
        client.emit("load_state", test_state_json)
        received = client.get_received()

        # # make sure just one event was received
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

    def test_gripper_movement(self):
        """
        test movements of grippers with normal
        and user defined step size
        """
        client = self.get_client(True)

        # send a configuration
        file_path = Path(f"{RESOURCE_DIR}/tasks/pento_test.json")
        with open(file_path, "r", encoding="utf-8") as f:
            test_state_json = json.load(f)

        # send state as dictionary
        client.emit("load_state", test_state_json)
        client.get_received()

        # configuration
        test_gripper = "0"
        test_step_size = 0.5

        # send movement
        client.emit("move", {
            "id": test_gripper,
            "dx": 1,
            "dy": 0
        })
        received = client.get_received()

        # make sure we only received one object
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["name"], "update_grippers")

        # make sure new coordinates are correct
        new_x = received[0]["args"][0][test_gripper]["x"]
        old_x = test_state_json["grippers"][test_gripper]["x"]
        self.assertEqual(new_x, old_x + test_step_size)

        # test bigger movement on y coordinate
        test_step_size = 4
        client.emit("move", {
            "id": test_gripper,
            "dx": 0,
            "dy": 1,
            "step_size": test_step_size
        })
        received = client.get_received()

        # make sure we only received one object
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["name"], "update_grippers")

        # make sure new coordinates are correct
        new_y = received[0]["args"][0][test_gripper]["y"]
        old_y = test_state_json["grippers"][test_gripper]["y"]
        self.assertEqual(new_y, old_y + test_step_size)

    def test_rotate_object(self):
        client = self.get_client(True)

        # send a configuration
        file_path = Path(f"{RESOURCE_DIR}/tasks/gripped_test.json")
        with open(file_path, "r", encoding="utf-8") as f:
            test_state_json = json.load(f)

        # send state as dictionary
        client.emit("load_state", test_state_json)
        client.get_received()

        # configuration
        test_gripper = "0"
        rotation = -1
        obj = "4"

        client.emit("rotate", {
            "id": test_gripper,
            "direction": rotation
        })

        received = client.get_received()
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
        client = self.get_client(True)

        # send a configuration
        file_path = Path(f"{RESOURCE_DIR}/tasks/pento_test.json")
        with open(file_path, "r", encoding="utf-8") as f:
            test_state_json = json.load(f)

        # send state as dictionary
        client.emit("load_state", test_state_json)
        client.get_received()

        # configuration
        test_gripper = "0"
        rotation = -1

        client.emit("rotate", {
            "id": test_gripper,
            "direction": rotation
        })

        received = client.get_received()

        # even if no object is gripped, should return OK (?)
        self.assertEqual(len(received), 0)

    def test_flip_object(self):
        client = self.get_client(True)

        # send a configuration
        file_path = Path(f"{RESOURCE_DIR}/tasks/gripped_test.json")
        with open(file_path, "r", encoding="utf-8") as f:
            test_state_json = json.load(f)

        # send state as dictionary
        client.emit("load_state", test_state_json)
        client.get_received()

        # configuration
        test_gripper = "0"
        obj = "4"

        client.emit("flip", {
            "id": test_gripper
        })

        received = client.get_received()

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

    # test loop functionality?

    # --- gripping --- #
    # both data structures show no object gripped or same object is gripped

    # bad request: missing gripper id
    # valid request

    # stop gripping

    # --- objects --- #

    # --- deleting the state --- #

    # --- create more test cases for extensions below --- #
