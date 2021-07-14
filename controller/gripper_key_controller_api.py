from flask import Flask, request
from flask_cors import CORS, cross_origin
from gripper_key_controller import GripperKeyController
import requests
import json
import argparse

# ------------------------------------------------------------------------------ #
# An example implementation of a Controller module. This API allows for user
# interaction via a keyboard.

# author: clpresearch, Karla Friedrichs
# usage: python3 gripper_key_controller_api.py [-h] [--host HOST] [--port PORT] [--test]
# Runs on host 127.0.0.1 and port 5001 per default
# ------------------------------------------------------------------------------ #

# --- define globals --- #

app = Flask(__name__)
# enable cross-origin requests 
# TODO: restrict sources
CORS(app)

key_controller = GripperKeyController()
HOST = "127.0.0.1"
PORT = "5001"

# --- define routes --- # 

@app.route("/attach-model", methods=["POST", "DELETE"])
def attach_model():
	if not request.data:
		return "1", 400
	else:
		json_data = json.loads(request.data)
	
	if request.method == "POST":
		if type(json_data) == dict and "url" in json_data and "gripper" in json_data:
			return "0" if key_controller.attach_model(json_data["url"], json_data["gripper"]) else ("1", 400)
		return "1", 400
	elif request.method == "DELETE":
		if type(json_data) != dict or "url" not in json_data:
			return "1", 400
		# unsubscribe only a specific gripper-model combination
		elif "gripper" in json_data:
			return "0" if key_controller.detach_model(json_data["url"], json_data["gripper"]) else ("1", 400)
		# unsubscribe all grippers of a model
		else:
			return "0" if key_controller.detach_model(json_data["url"]) else ("1", 400)
	else:
		return "1", 405

@app.route("/key-pressed/<int:key_code>", methods=["POST", "DELETE"])
def key_pressed(key_code):
	# attempt to process the key. False is returned if no function is assigned.
	if request.method == "POST":
		if key_controller.key_pressed(key_code):
			return "0"
		return "1", 404
	elif request.method == "DELETE":
		if key_controller.key_released(key_code):
			return "0"
		return "1", 404
	return "1", 405

def selftest():
	with app.test_client() as c:
		# subscribe a model (API needs to be running!)
		dummy_model = "127.0.0.1:5000"
		# post a test state so we have a gripper with id "1" for the following tests
		f = open("resources/state/pentomino_testgame.json", mode="r", encoding="utf-8")
		json_state = f.read()
		f.close()
		requests.post("http://{}/state".format(dummy_model), data=json_state)
		test_state = json.loads(json_state)
		
		# subscribe the dummy model
		r_subscribe_model = c.post("/attach-model", data=json.dumps({"url": dummy_model, "gripper": "1"}))
		assert r_subscribe_model.status == "200 OK"
		# attempt to subscribe an already subscribed model
		r_subscribe_model2 = c.post("/attach-model", data=json.dumps({"url": dummy_model, "gripper": "1"}))
		assert r_subscribe_model2.status == "200 OK"
		# no duplicate subscription
		assert len(key_controller.models) == 1 

		# test key press and key release
		r_unassigned_keypress = c.post("/key-pressed/1")
		assert r_unassigned_keypress.status == "404 NOT FOUND"
		r_keypress_grip = c.post("/key-pressed/32")
		assert r_keypress_grip.status == "200 OK"
		r_keyrelease_grip = c.delete("/key-pressed/32")
		assert r_keyrelease_grip.status == "200 OK"

		r_keypress_move = c.post("/key-pressed/37")
		assert r_keypress_move.status == "200 OK"
		r_keyrelease_move = c.delete("/key-pressed/37")
		assert r_keyrelease_move.status == "200 OK"

		# unsubscribe a model
		r_unsubscribe_model = c.delete("/attach-model", data=json.dumps({"url": dummy_model}))
		assert r_unsubscribe_model.status == "200 OK"
		# attempt to unsubscribe a non-subscribed model
		r_unsubscribe_model2 = c.delete("/attach-model", data=json.dumps({"url": dummy_model}))
		assert r_unsubscribe_model2.status == "400 BAD REQUEST"

		# clean up 
		requests.delete("http://{}/state".format(dummy_model))

# --- command line arguments ---
parser = argparse.ArgumentParser(description="Run GOLMI's controller API.")
parser.add_argument("--host", type=str, default="127.0.0.1", help="Adress to run the API on. Default: localhost.")
parser.add_argument("--port", type=str, default="5001", help="Port to run the API on. Default: 5001.")
parser.add_argument("--test", action="store_true", help="Pass this argument to perform some tests before the API is run.")

if __name__ == "__main__":
	args = parser.parse_args()
	if args.test:
		selftest()
		print("All tests passed.")
	app.run(host=args.host, port=args.port)