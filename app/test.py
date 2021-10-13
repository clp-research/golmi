""" tests for GOLMI's endpoints 
Makes some tests for each of the served endpoints

author: clpresearch, Karla Friedrichs
"""

from app import app, socketio, AUTH
from os.path import join

# directory html is served from
TEMPLATE_DIR = "app/templates"


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

	# TODO
	# --- loading a state --- #
	# save received state

	# --- gripper position --- #
	# move gripper once with default step size
	# move gripper with custom step size
	# stop moving the gripper

	# --- rotating the gripped object --- #
	# even if no object is gripped, should return OK

	# --- flipping the gripped object --- # 
	# flip once

	# --- gripping --- #
	# both data structures show no object gripped or same object is gripped
	
	# bad request: missing gripper id
	# valid request

	# stop gripping

	# --- objects --- #

	# --- deleting the state --- #

	# --- create more test cases for extensions below --- # 