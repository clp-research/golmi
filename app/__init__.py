from flask import Flask, request
from flask_cors import CORS, cross_origin
from flask_socketio import SocketIO, send, emit, ConnectionRefusedError
from model.model import Model
from model.config import Config

# --- create the app --- #

# has to be passed by clients to connect
# might want to set this in the environment variables: AUTH = os.environ['GOLMI_AUTH']
AUTH = "GiveMeTheBigBluePasswordOnTheLeft"
app = Flask(__name__)
# --- app settings --- # 
# Secret key used for sessions: 
# Before publishing, generate random bytes e.g. using:
# $ python -c 'import os; print(os.urandom(16))'
# (This is the recommendation by the Flask documentation: https://flask.palletsprojects.com/en/2.0.x/quickstart/#sessions)
app.config["SECRET KEY"] = "definite change this to some random value!".encode("utf-8")
app.config["DATA_COLLECTION"] = "app/static/resources/"
# enable cross-origin requests 
# TODO: restrict sources
CORS(app)
# add socket io
socketio = SocketIO(app, logger=True, engineio_logger=True, cors_allowed_origins='*')

# --- create a data model --- #

config = Config("app/static/resources/config/pentomino_types.json")
model = Model(config, socketio)

# finally load the routes
from app import views

# --- socketio events --- #
# --- connection --- #
@socketio.on("connect")
def client_connect(auth):
	# authenticate the client:
	if auth != AUTH:
		raise ConnectionRefusedError("unauthorized")
	# send config and state
	emit("update_config", model.config.to_dict())
	emit("update_state", model.state.to_dict())

# --- state --- #
@socketio.on("load_state")
def load_state(json):
	model.set_state(json)

# --- configuration --- #
@socketio.on("load_config")
def load_config(json):
	model.set_config(json)

# --- gripper --- #
@socketio.on("add_gripper")
def add_gripper(gr_id=None):
	# if no id was passed (or None), use the session id
	if not gr_id:
		gr_id = request.sid
	# add gripper to the model
	model.add_gr(gr_id)
	emit("attach_gripper", gr_id)

@socketio.on("remove_gripper")
def remove_gripper(gr_id=None):
	# if no id was passed (or None), use the session id
	if not gr_id:
		gr_id = request.sid
	# delete the gripper
	model.remove_gr(gr_id)

# For all actions: move, flip, rotate, grip, there are 2 options: 'one-time action' and 'looped action'.
# See the documentation for details.

@socketio.on("move")
def move(params):
	# check the arguments and make sure the gripper exists
	if type(params) == dict and "id" in params and "dx" in params and "dy" in params and \
		model.get_gripper_by_id(str(params["id"])) != None:

		step_size = params["step_size"] if "step_size" in params else None
		# continuous / looped action
		if "loop" in params and params["loop"]:
			model.start_moving(str(params["id"]), params["dx"], params["dy"], step_size)
		# one-time action
		else:
			model.move(str(params["id"]), params["dx"], params["dy"], step_size)

@socketio.on("stop_move")
def stop_move(params):
	# check the arguments and make sure the gripper exists
	if type(params) == dict and "id" in params and \
		model.get_gripper_by_id(str(params["id"])):

		model.stop_moving(str(params["id"]))

@socketio.on("rotate")
def rotate(params):
	# check the arguments and make sure the gripper exists
	if type(params) == dict or "id" in params and "direction" in params and \
		model.get_gripper_by_id(str(params["id"])) != None:
		
		step_size = params["step_size"] if "step_size" in params else None
		# continuous / looped action
		if "loop" in params and params["loop"]:
			model.start_rotating(str(params["id"]), params["direction"], step_size)
		# one-time action
		else:
			model.rotate(str(params["id"]), params["direction"], step_size)

@socketio.on("stop_rotate")
def stop_rotate(params):
	# check the arguments and make sure the gripper exists
	if type(params) == dict or "id" in params and \
		model.get_gripper_by_id(str(params["id"])) != None:

		model.stop_rotating(str(params["id"]))

@socketio.on("flip")
def flip(params):
	# check the arguments and make sure the gripper exists
	if type(params) == dict or "id" in params and \
		model.get_gripper_by_id(str(params["id"])) != None:
		
		# continuous / looped action
		if "loop" in params and params["loop"]:
			model.start_flipping(str(params["id"]))
		# one-time action
		else:
			model.flip(str(params["id"]))

@socketio.on("stop_flip")
def stop_flip(params):
	# check the arguments and make sure the gripper exists
	if type(params) == dict or "id" in params and \
		model.get_gripper_by_id(str(params["id"])) != None:
		
		model.stop_flipping(str(params["id"]))

@socketio.on("grip")
def grip(params):
	# check the arguments and make sure the gripper exists
	if type(params) == dict and "id" in params and \
		model.get_gripper_by_id(str(params["id"])) != None:

		# continuous / looped action
		if "loop" in params and params["loop"]:
			model.start_gripping(str(params["id"]))
		# one-time action
		else:
			model.grip(str(params["id"]))

@socketio.on("stop_grip")
def stop_grip(params):
	# check the arguments and make sure the gripper exists
	if type(params) == dict or "id" in params and \
		model.get_gripper_by_id(str(params["id"])) != None:

		model.stop_gripping(str(params["id"]))