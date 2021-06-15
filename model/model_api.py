from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from model import Model
from config import Config
import requests
import json

# --- define globals --- #

app = Flask(__name__)
# enable cross-origin requests 
# TODO: restrict sources
CORS(app)

HOST = "127.0.0.1"
PORT = "5000"
# todo: endpoint to change config
config = Config("../pentomino/pentomino_types.json")
model = Model(config)

# --- define routes --- # 

@app.route("/attach-view", methods=["POST"])
#@cross_origin(origin='localhost')
def attach_view():
	json_data = json.loads(request.data)
	model.attach_view(json_data["url"])
	return "0"

@app.route("/detach-view", methods=["POST"])
def detach_view():
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
	else: 
		print("POST at /config endpoint: not implemented")
		return "1", 404

@app.route("/gripper/position", methods=["POST", "GET"])
def gripper_position():
	if request.method == "GET":
		x, y = model.get_gripper_coords()
		return {"x": x, "y": y}
	elif request.method == "POST":
		# TODO why does get_json() not return json data?
		json_data = json.loads(request.json)
		if type(json_data) == dict and "x" in json_data and "y" in json_data:
			if "speed" in json_data:
				model.move_gr(json_data["x"], json_data["y"], json_data["speed"])
			else:
				model.move_gr(json_data["x"], json_data["y"])
			return "0"
		elif type(json_data) == list and len(json_data) == 2:
			model.move_gr(json_data[0], json_data[1])
			return "0"
		else:
			return ("1", 400)

@app.route("/gripper/grip", methods=["POST", "GET"])
def gripper_grip():
	if request.method == "GET":
		return {"id": model.get_gripped_obj()}
	elif request.method == "POST":
		model.grip()
		return "0"

@app.route("/objects", methods=["GET", "POST"])
def objects():
	if request.method == "GET":
		# return all object ids
		return {"ids": list(model.get_object_ids())}
	elif request.method == "POST":
		# add an object
		print("POST at /objects: not implemented")
		return "not implemented"

@app.route("/state", methods=["POST"])
def state():
	# load a new state
	model.set_initial_state(request.json)
	return "0"

# --- tests --- #

def selftest():
	with app.test_client() as c:
		# --- attaching and detaching views --- #
		dummy_view = "127.0.0.1:666"
		rv = c.post("/attach-view", data=json.dumps({"url":dummy_view}))
		assert int(rv.data) == 0 and dummy_view in model.views
		# delete view again or there view be errors in the following tests
		# when the model tries to notify the dummy view
		c.post("/detach-view", data=json.dumps({"url":dummy_view}))
		assert dummy_view not in model.views

		# --- loading a state --- #
		f = open("../pentomino/pentomino_testgame.json", mode="r", encoding="utf-8")
		json_state = f.read()
		f.close()
		rv_state = c.post("/state", json=json_state)
		test_state = json.loads(json_state)

		# --- gripper position --- #
		rv2 = c.get("/gripper/position")
		gripper_coords = rv2.get_json()
		assert gripper_coords["x"] == test_state["gripper"]["x"] and \
			gripper_coords["y"] == test_state["gripper"]["y"]
		# move gripper with default step size
		rv_move_gripper = c.post("/gripper/position", json=json.dumps({"x":3, "y":0}))
		assert int(rv_move_gripper.data) == 0
		assert model.get_gripper_coords()[0] > gripper_coords["x"] and \
			model.get_gripper_coords()[1] == gripper_coords["y"]
		# move gripper with custom step size
		rv_move_gripper2 = c.post("/gripper/position", json=json.dumps({"x":0, "y":3, "speed":1}))
		assert int(rv_move_gripper2.data) == 0
		assert model.get_gripper_coords()[1] == gripper_coords["y"] + 3
		# --- gripping --- #
		rv4 = c.get("/gripper/grip")
		assert rv4.get_json()["id"] == test_state["gripper"]["gripped"]
		rv5 = c.post("/gripper/grip")
		assert int(rv5.data) == 0

		# --- objects --- #
		rv6 = c.get("/objects")
		assert rv6.get_json()["ids"] == list(test_state["objs"].keys())


if __name__ == "__main__":
	selftest()
	app.run(host=HOST, port=PORT)