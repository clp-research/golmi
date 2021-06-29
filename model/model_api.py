from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from model import Model
from config import Config
import requests
import json

# --- define globals --- #

# TODO: /gripper/{id} (+ grip?)
# TODO: /objects/{id}

app = Flask(__name__)
# enable cross-origin requests 
# TODO: restrict sources
CORS(app)

HOST = "127.0.0.1"
PORT = "5000"
# todo: endpoint to change config
config = Config("resources/type_config/pentomino_types.json")
model = Model(config)

# --- define routes --- # 

@app.route("/attach-view", methods=["POST"])
#@cross_origin(origin='localhost')
def attach_view():
	if not request.data:
		return "1", 400
	else:
		json_data = json.loads(request.data)
	model.attach_view(json_data["url"])
	return "0"

@app.route("/detach-view", methods=["POST"])
def detach_view():
	if not request.data:
		return "1", 400
	else:
		json_data = json.loads(request.data)
	model.detach_view(json_data["url"])
	return "0"

@app.route("/config", methods=["GET", "POST"])
def config():
	if request.method == "GET":
		return {
			"width": model.get_width(),
			"height": model.get_height(),
			"type_config": model.get_type_config()
		}
	elif request.method == "POST": 
		print("POST at /config endpoint: not implemented")
		return "1", 404
	else: 
		return "1", 405


@app.route("/gripper", methods=["POST", "GET"])
def gripper():
	if request.method == "GET":
		gr_ids = model.get_gripper_ids()
		# construct the response: dictionary mapping ids to gripper details
		response = dict()
		for gr_id in gr_ids:
			gr = model.get_gripper_by_id(gr_id)
			response[gr_id] = _obj_to_dict(gr)
		return response
	elif request.method == "POST":
		if not request.data:
			return "1", 400
		else:
			json_data = json.loads(request.data)
		if type(json_data) == dict and "id" in json_data and "dx" in json_data and "dy" in json_data:
			# Make sure the gripper exists
			if not model.get_gripper_by_id(str(json_data["id"])):
				return "1", 404

			if "speed" in json_data:
				model.move_gr(str(json_data["id"]), json_data["dx"], json_data["dy"], json_data["speed"])
			else:
				model.move_gr(str(json_data["id"]), json_data["dx"], json_data["dy"])
			return "0"
		else: 
			return "1", 400
	else: 
		return "1", 405

@app.route("/gripper/grip", methods=["POST", "GET"])
def gripper_grip():
	if request.method == "GET":
		gr_ids = model.get_gripper_ids()
		response = dict()
		for gr_id in gr_ids:
			# get the id of a gripped object, or None if no object is gripped
			gripped_obj = model.get_gripped_obj(gr_id)
			if gripped_obj:
				response[gr_id] = {gripped_obj: _obj_to_dict(model.get_obj_by_id(gripped_obj))}
			else:
				response[gr_id] = None
		return response
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

		model.grip(str(json_data["id"]))
		return "0"
	else: 
		return "1", 405

@app.route("/objects", methods=["GET", "POST"])
def objects():
	if request.method == "GET":
		obj_ids = model.get_object_ids()
		# construct the response: dictionary mapping ids to object details
		response = dict()
		for obj_id in obj_ids:
			obj = model.get_obj_by_id(obj_id)
			response[obj_id] = _obj_to_dict(obj)
		return response
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

def _obj_to_dict(obj):
	"""
	Constructs a dictionary from an Obj instance.
	@param obj 	instance of Obj or Obj child classes
	"""
	return {
		"type": obj.type,
		"x": obj.x,
		"y": obj.y,
		"width": obj.width,
		"height": obj.height,
		"rotation": obj.rotation,
		"mirrored": obj.rotation,
		"color": obj.color
		}

# --- tests --- #

def selftest():
	with app.test_client() as c:
		# --- attaching and detaching views --- #
		dummy_view = "127.0.0.1:666"
		rv = c.post("/attach-view", data=json.dumps({"url":dummy_view}))
		assert rv.status == "200 OK" and dummy_view in model.views
		# delete view again or there view be errors in the following tests
		# when the model tries to notify the dummy view
		c.post("/detach-view", data=json.dumps({"url":dummy_view}))
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
		rv_move_gripper = c.post("/gripper", data=json.dumps({"id":"1", "dx":3, "dy":0}))
		assert rv_move_gripper.status == "200 OK"
		assert model.get_gripper_coords("1")[0] > gripper["1"]["x"] and \
			model.get_gripper_coords("1")[1] == gripper["1"]["y"]
		# move gripper with custom step size
		rv_move_gripper2 = c.post("/gripper", data=json.dumps({"id":"1", "dx":0, "dy":3, "speed":1}))
		assert rv_move_gripper2.status == "200 OK"
		assert model.get_gripper_coords("1")[1] == gripper["1"]["y"] + 3
		# --- gripping --- #
		rv4 = c.get("/gripper/grip")
		assert test_state["grippers"]["1"]["gripped"] in rv4.get_json()["1"].keys()
		rv5_bad_request = c.post("/gripper/grip")
		assert rv5_bad_request.status == "400 BAD REQUEST"
		rv5 = c.post("/gripper/grip", data=json.dumps({"id":"1"}))
		assert rv5.status == "200 OK"

		# --- objects --- #
		rv6 = c.get("/objects")
		assert rv6.get_json().keys() == test_state["objs"].keys()

		# --- deleting the state --- #
		rv_reset = c.delete("/state")
		assert rv_reset.status == "200 OK" and len(model.get_objects()) == 0


if __name__ == "__main__":
	selftest()
	app.run(host=HOST, port=PORT)