from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from model import Model
from config import Config
import requests
import json
from time import sleep
import argparse

# GOLMI's model API
# author: clpresearch, Karla Friedrichs
# usage: python3 model_api.py [-h] [--host HOST] [--port PORT] [--test]
# Runs on host 127.0.0.1 and port 5000 per default

# --- define globals --- #

# TODO: /gripper/{id} (+ grip?)
# TODO: /objects/{id}

app = Flask(__name__)
# enable cross-origin requests 
# TODO: restrict sources
CORS(app)

# todo: endpoint to change config
config = Config("resources/type_config/pentomino_types.json")
model = Model(config)

# --- define routes --- # 

@app.route("/attach-view", methods=["POST", "DELETE"])
#@cross_origin(origin='localhost')
def attach_view():
	if not request.data:
		return "1", 400
	elif request.method == "POST":
		json_data = json.loads(request.data)
		model.attach_view(json_data["url"])
		return "0"
	elif request.method == "DELETE":
		json_data = json.loads(request.data)
		return "0" if model.detach_view(json_data["url"]) else ("1", 400)
	else:
		return "1", 405

@app.route("/config", methods=["GET", "POST"])
def config():
	if request.method == "GET":
		return model.get_config()
	elif request.method == "POST": 
		print("POST at /config endpoint: not implemented")
		return "1", 404
	else: 
		return "1", 405


@app.route("/gripper", methods=["GET"])
def gripper():
	if request.method == "GET":
		return model.get_grippers()
	else: 
		return "1", 405

@app.route("/gripper/position", methods=["POST", "DELETE"])
def gripper_position():
	if request.method == "POST":
		if not request.data:
			return "1", 400
		else:
			json_data = json.loads(request.data)
		if type(json_data) == dict and "id" in json_data and "dx" in json_data and "dy" in json_data:
			# Make sure the gripper exists
			if not model.get_gripper_by_id(str(json_data["id"])):
				return "1", 404

			if "step_size" in json_data:
				model.start_moving_gr(str(json_data["id"]), json_data["dx"], json_data["dy"], json_data["step_size"])
			else:
				model.start_moving_gr(str(json_data["id"]), json_data["dx"], json_data["dy"])
			return "0"
		else: 
			return "1", 400
	elif request.method == "DELETE":
		if not request.data:
			return "1", 400
		else:
			json_data = json.loads(request.data)
		if type(json_data) == dict and "id" in json_data:
			# Make sure the gripper exists
			if not model.get_gripper_by_id(str(json_data["id"])):
				return "1", 404
			model.stop_moving_gr(str(json_data["id"]))
			return "0"
		else: 
			return "1", 400 

@app.route("/gripper/rotate", methods=["POST", "DELETE"])
def gripper_rotate():
	"""
	Rotate the gripped object.
	"""
	if not request.data:
		return "1", 400
	else:
		json_data = json.loads(request.data)
	# assert the request has the right parameters
	if type(json_data) != dict or "id" not in json_data:
		return "1", 400
	# assert the gripper exists
	if not model.get_gripper_by_id(str(json_data["id"])):
			return "1", 404
	# rotate the gripped object
	if request.method == "POST":
		if "direction" not in json_data:
			return "1", 400
		if "step_size" in json_data:
			model.start_rotating(str(json_data["id"]), float(json_data["direction"]), float(json_data["step_size"]))
		else:
			model.start_rotating(str(json_data["id"]), float(json_data["direction"]))
		return "0", 200
	elif request.method == "DELETE":
		model.stop_rotating(str(json_data["id"]))
		return "0", 200


@app.route("/gripper/grip", methods=["POST", "GET", "DELETE"])
def gripper_grip():
	if request.method == "GET":
		grippers = model.get_grippers()
		return {gr_id: gr["gripped"] for gr_id, gr in grippers.items()}
	elif request.method == "POST":
		# load request json, if present
		if not request.data:
			return "1", 400
		else:
			json_data = json.loads(request.data)

		# assert the request has the right parameters
		if type(json_data) != dict or "id" not in json_data:
			return "1", 400

		# assert the gripper exists
		if not model.get_gripper_by_id(str(json_data["id"])):
			return "1", 404

		model.start_gripping(str(json_data["id"]))
		return "0"
	elif request.method == "DELETE":
		# load request json, if present
		if not request.data:
			return "1", 400
		else:
			json_data = json.loads(request.data)

		# assert the request has the right parameters
		if type(json_data) != dict or "id" not in json_data:
			return "1", 400

		# assert the gripper exists
		if not model.get_gripper_by_id(str(json_data["id"])):
			return "1", 404

		model.stop_gripping(str(json_data["id"]))
		return "0"
	else: 
		return "1", 405

@app.route("/objects", methods=["GET", "POST"])
def objects():
	if request.method == "GET":
		return model.get_objects()
	elif request.method == "POST":
		# add an object
		print("POST at /objects: not implemented")
		return "not implemented"
	else: 
		return "1", 405

@app.route("/state", methods=["POST", "DELETE"])
def state():
	if request.method == "POST":
		# load a new state
		model.set_initial_state(json.loads(request.data))
		return "0"
	elif request.method == "DELETE":
		model.reset()
		return "0"
	else:
		return "1", 405
 
# --- tests --- #

def selftest():
	with app.test_client() as c:
		# --- attaching and detaching views --- #
		dummy_view = "127.0.0.1:666"
		rv = c.post("/attach-view", data=json.dumps({"url":dummy_view}))
		assert rv.status == "200 OK" and dummy_view in model.views
		# delete view again or there view be errors in the following tests
		# when the model tries to notify the dummy view
		c.delete("/attach-view", data=json.dumps({"url":dummy_view}))
		assert dummy_view not in model.views

		# --- loading a state --- #
		f = open("resources/state/pentomino_testgame.json", mode="r", encoding="utf-8")
		json_state = f.read()
		f.close()
		rv_state = c.post("/state", data=json_state)
		test_state = json.loads(json_state)

		# --- gripper position --- #
		rv2 = c.get("/gripper")
		gripper = rv2.get_json()
		assert gripper["1"]["x"] == test_state["grippers"]["1"]["x"] and \
			gripper["1"]["y"] == test_state["grippers"]["1"]["y"]
		# move gripper with default step size
		rv_move_gripper = c.post("/gripper/position", data=json.dumps({"id":"1", "dx":3, "dy":0}))
		assert rv_move_gripper.status == "200 OK"
		assert model.get_gripper_coords("1")[0] > gripper["1"]["x"] and \
			model.get_gripper_coords("1")[1] == gripper["1"]["y"]
		# move gripper with custom step size
		rv_move_gripper2 = c.post("/gripper/position", data=json.dumps({"id":"1", "dx":0, "dy":3, "step_size":1}))
		assert rv_move_gripper2.status == "200 OK"
		assert float(model.get_gripper_coords("1")[1]) == float(gripper["1"]["y"] + 3)
		# stop moving the gripper
		rv_stop_gripper = c.delete("/gripper/position", data=json.dumps({"id": "1"}))
		assert rv_stop_gripper.status == "200 OK"

		# --- rotating the gripped object --- #
		rv_rotate = c.post("/gripper/rotate", data=json.dumps({"id": "1", "direction": 1, "step_size": 45}))
		# even if no object is gripped, should return OK
		assert rv_rotate.status == "200 OK"
		rv_stop_rotate = c.delete("/gripper/rotate", data=json.dumps({"id": "1"}))
		assert rv_rotate.status == "200 OK"

		# --- gripping --- #
		rv4 = c.get("/gripper/grip")
		assert test_state["grippers"]["1"]["gripped"] in rv4.get_json()["1"].keys()
		# bad request: missing gripper id
		rv5_bad_request = c.post("/gripper/grip")
		# valid request
		assert rv5_bad_request.status == "400 BAD REQUEST"
		rv5_start_gripping = c.post("/gripper/grip", data=json.dumps({"id":"1"}))
		assert rv5_start_gripping.status == "200 OK"

		# stop gripping
		rv5_stop_gripping = c.delete("/gripper/grip", data=json.dumps({"id":"1"}))
		assert rv5_stop_gripping.status == "200 OK"

		# --- objects --- #
		rv6 = c.get("/objects")
		assert rv6.get_json().keys() == test_state["objs"].keys()

		# --- deleting the state --- #
		rv_reset = c.delete("/state")
		assert rv_reset.status == "200 OK" and len(model.get_objects()) == 0

# --- command line arguments ---
parser = argparse.ArgumentParser(description="Run GOLMI's model API.")
parser.add_argument("--host", type=str, default="127.0.0.1", help="Adress to run the API on. Default: localhost.")
parser.add_argument("--port", type=str, default="5000", help="Port to run the API on. Default: 5000.")
parser.add_argument("--test", action="store_true", help="Pass this argument to perform some tests before the API is run.")

if __name__ == "__main__":
	args = parser.parse_args()
	if args.test:
		selftest()
		print("All tests passed.")
	app.run(host=args.host, port=args.port)