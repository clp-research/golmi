""" tests for GOLMI's endpoints 
Makes some tests for each of the served endpoints

author: clpresearch, Karla Friedrichs
"""

from app import app, socketio, AUTH
from os.path import join
import json

# directory html is served from
TEMPLATE_DIR = "app/templates"
# directory containing resources
RESOURCE_DIR = "app/static/resources"


def selftest(): 
	"""Tests the Flask app and the Flask-SocketIO app."""

	# --- flask app / endpoints --- #

	flask_test_client = app.test_client()
	# --- html serving --- #
	# check GET-only endpoints
	for page in ["/", "/demo"]:
		get_response = flask_test_client.get(page)
		assert get_response.status == "200 OK"
		# other methods could be checked here as well ...
		post_response = flask_test_client.post(page)
		assert post_response.status == "405 METHOD NOT ALLOWED"

	# --- saving logs --- #
	# posting without data or non-json data
	savelog_invalid1 = flask_test_client.post("/save_log")
	savelog_invalid2 = flask_test_client.post("/save_log", data="absolutely_not_json")
	assert savelog_invalid1.status == "400 BAD REQUEST" and \
		savelog_invalid2.status == "400 BAD REQUEST"
	# sending valid log data is not tested here as is would create a file 
	# with a hardly predictable filename at every test run

	# --- socketio tests --- # 

	# Note: All of these tests assume the client connecting to the
	# defaul namespace "/"!

	# connect to Socket.IO without authentication
	socketio_test_client = socketio.test_client(
		app, flask_test_client=flask_test_client)
	# make sure the server rejected the connection
	assert not socketio_test_client.is_connected()
	
	# valid connection request
	# (room id will be None, as the client has no session id)
	socketio_test_client.connect(auth=AUTH)
	assert socketio_test_client.is_connected()

	# make sure the initial configuration and an empty state were sent
	received_config = False
	received_state = False
	for event in socketio_test_client.get_received():
		if event["name"] == "update_config":
			received_config = True
		elif event["name"] == "update_state":
			received_state = True
			# make sure state is empty
			assert len(event["args"][0]["grippers"]) == 0 and len(event["args"][0]["objs"]) == 0, \
				"Test failed: initially received state was not empty."
	assert received_config, "Test failed: did not receive a configuration after connection."
	assert received_state, "Test failed: did not receive a state after connection."

	# --- loading a state --- #
	f = open(join(RESOURCE_DIR, "tasks/pento_test.json"), mode="r", encoding="utf-8")
	test_state = f.read()
	f.close()
	# convert to json
	test_state = json.loads(test_state)
	socketio_test_client.emit("load_state", test_state)
	received = socketio_test_client.get_received()
	# make sure just one event was received
	assert len(received) == 1
	assert received[0]["name"] == "update_state"

	# Check the received properties correspond to the sent properties
	for gripper in received[0]["args"][0]["grippers"]:
		assert gripper in test_state["grippers"], "Test failed: gripper {} missing".format(gripper)
		for prop in received[0]["args"][0]["grippers"][gripper]:
			if prop in test_state["grippers"][gripper]:
				assert received[0]["args"][0]["grippers"][gripper][prop] == test_state["grippers"][gripper][prop], \
					"Test failed: properties differ: received: {}, sent: {}".format(
						received[0]["args"][0]["grippers"][gripper][prop],
						test_state["grippers"][gripper][prop])
	for obj in received[0]["args"][0]["objs"]:
		assert obj in test_state["objs"], "Test failed: obj {} missing".format(obj)
		for prop in received[0]["args"][0]["objs"][obj]:
			if prop in test_state["objs"][obj]:
				assert received[0]["args"][0]["objs"][obj][prop] == test_state["objs"][obj][prop], \
					"Test failed: properties differ: received: {}, sent: {}".format(
						received[0]["args"][0]["objs"][obj][prop],
						test_state["objs"][obj][prop])

	# --- loading a configuration --- # 
	test_step_size = 0.5

	# --- add / remove grippers --- #

	# --- gripper position --- #
	test_gripper = "0"

	# move gripper once with default step size
	socketio_test_client.emit("move", {"id":test_gripper, "dx":1, "dy":0})
	received = socketio_test_client.get_received()
	assert len(received) == 1
	assert received[0]["name"] == "update_grippers"

	# check the gripper was moved one block to the right
	assert received[0]["args"][0][test_gripper]["x"] == \
		(test_state["grippers"][test_gripper]["x"] + test_step_size)

