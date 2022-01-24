from flask import Flask, request, session
from flask_cors import CORS
from flask_socketio import (
    SocketIO, emit, ConnectionRefusedError, join_room, rooms
)

from app import DEFAULT_CONFIG_FILE
from model.model import Model
from model.config import Config

# --- create the app --- #

# has to be passed by clients to connect
# might want to set this in the environment variables:
# AUTH = os.environ['GOLMI_AUTH']
AUTH = "GiveMeTheBigBluePasswordOnTheLeft"
app = Flask(__name__)
# --- app settings --- #
# Secret key used for sessions:
# Before publishing, generate random bytes e.g. using:
# $ python -c 'import os; print(os.urandom(16))'
# (This is the recommendation by the Flask documentation:
# https://flask.palletsprojects.com/en/2.0.x/quickstart/#sessions)
app.config["SECRET_KEY"] = "change this to some random value!".encode("utf-8")
app.config['CORS_HEADERS'] = 'Content-Type'

# enable cross-origin requests
# TODO: restrict sources
CORS(app)
# add socket io
socketio = SocketIO(
    app,
    logger=True,
    engineio_logger=True,
    cors_allowed_origins='*'
)

# --- create a data model --- #
# session ids mapped to Model instances
client_models = dict()


def check_parameters(params, model, keys):
    """
    Function to make sure the passed parameters are valid.
    Checks:
        - parameters are passed as dictionary
        - some keys are present in the dictionary
        - the gripper is not None
    """
    good_param = isinstance(params, dict)
    keys_in_param = keys.issubset(set(params.keys()))
    if "id" in params:
        gripper_not_none = model.get_gripper_by_id(
            str(params["id"])
        ) is not None
    else:
        # if the gripper is not needed (es. random init)
        # set it to True so that only other 2 checks
        # need to be True
        gripper_not_none = True

    return good_param and keys_in_param and gripper_not_none


def param_is_integer(param):
    """
    @return True if param is of type int, or is a float and convertible to int
    """
    return isinstance(param, int) or \
        (isinstance(param, float) and param.is_integer())


# --- socketio events --- #
# --- connection --- #
@socketio.on("connect")
def client_connect(auth):
    # authenticate the client:
    if "password" not in auth:
        raise ConnectionRefusedError("authentication failed")
    if not isinstance(auth, dict):
        raise ConnectionRefusedError("authentication failed")
    if auth["password"] != AUTH:
        raise ConnectionRefusedError("authentication failed")

    # add client to the list, for now each client gets their own room
    # create and server for this client
    client_model = Model(
        Config.from_json(app.config[DEFAULT_CONFIG_FILE]),
        socketio,
        request.sid
    )
    client_models[request.sid] = client_model
    room = session.get("room")
    join_room(room)

    # send config and state
    client_model_config = client_model.config.to_dict()
    emit("update_config", client_model_config)

    client_model_state = client_model.state.to_dict()
    emit("update_state", client_model_state)


@socketio.on("disconnect")
def client_disconnect():
    # delete the client's model
    for room in rooms(request.sid):
        client_models.pop(room)


# --- state --- #
@socketio.on("load_state")
def load_state(json):
    client_models[request.sid].set_state(json)


@socketio.on("reset_state")
def reset_state():
    """Reset the server's state."""
    client_models[request.sid].reset()


# --- configuration --- #
@socketio.on("load_config")
def load_config(json):
    client_models[request.sid].set_config(json)


# --- pieces --- #
@socketio.on("random_init")
def init_from_Random(params):
    model = client_models[request.sid]
    good_params = check_parameters(
        params,
        model,
        {"n_objs", "n_grippers"}
    )

    if good_params:
        model.set_random_state(
            **params
        )


# --- gripper --- #
@socketio.on("add_gripper")
def add_gripper(gr_id=None):
    # if no id was passed (or None), use the session id
    if not gr_id:
        gr_id = request.sid
    # add gripper to the model
    client_models[request.sid].add_gr(gr_id)
    emit("attach_gripper", gr_id)


@socketio.on("remove_gripper")
def remove_gripper(gr_id=None):
    # if no id was passed (or None), use the session id
    if not gr_id:
        gr_id = request.sid
    # delete the gripper
    client_models[request.sid].remove_gr(gr_id)


# For all actions: move, flip, rotate, grip, there are 2 options:
# 'one-time action' and 'looped action'.
# See the documentation for details.


@socketio.on("move")
def move(params):
    model = client_models[request.sid]
    # check the arguments and make sure the gripper exists
    good_params = check_parameters(params, model, {"id", "dx", "dy"})
    # dx and dy can only be integers:
    good_params = good_params and \
        param_is_integer(params["dx"]) and param_is_integer(params["dy"])

    if good_params:
        # continuous / looped action
        if params.get("loop"):
            model.start_moving(
                str(params["id"]), params["dx"], params["dy"])
        # one-time action
        else:
            model.mover.apply_movement(
                model.state,
                model.config,
                model,
                "move",
                str(params["id"]),
                x_steps=params["dx"],
                y_steps=params["dy"]
            )


@socketio.on("stop_move")
def stop_move(params):
    model = client_models[request.sid]
    # check the arguments and make sure the gripper exists
    good_params = check_parameters(params, model, {"id"})

    if good_params:
        client_models[request.sid].stop_moving(str(params["id"]))


@socketio.on("rotate")
def rotate(params):
    model = client_models[request.sid]
    # check the arguments and make sure the gripper exists
    good_params = check_parameters(params, model, {"id", "direction"})

    if good_params:
        step_size = params.get("step_size")
        # continuous / looped action
        if params.get("loop"):
            model.start_rotating(
                str(params["id"]), params["direction"], step_size
            )
        # one-time action
        else:
            model.mover.apply_movement(
                model.state,
                model.config,
                model,
                "rotate",
                str(params["id"]),
                direction=params["direction"],
                rotation_step=step_size
            )


@socketio.on("stop_rotate")
def stop_rotate(params):
    model = client_models[request.sid]
    # check the arguments and make sure the gripper exists
    good_params = check_parameters(params, model, {"id"})

    if good_params:
        model.stop_rotating(str(params["id"]))


@socketio.on("flip")
def flip(params):
    model = client_models[request.sid]
    # check the arguments and make sure the gripper exists
    good_params = check_parameters(params, model, {"id"})

    if good_params:
        # continuous / looped action
        if params.get("loop"):
            model.start_flipping(str(params["id"]))
        # one-time action
        else:
            model.mover.apply_movement(
                model.state,
                model.config,
                model,
                "flip",
                str(params["id"])
            )


@socketio.on("stop_flip")
def stop_flip(params):
    model = client_models[request.sid]
    # check the arguments and make sure the gripper exists
    good_params = check_parameters(params, model, {"id"})

    if good_params:
        model.stop_flipping(str(params["id"]))


@socketio.on("grip")
def grip(params):
    model = client_models[request.sid]
    # check the arguments and make sure the gripper exists
    good_params = check_parameters(params, model, {"id"})

    if good_params:
        # continuous / looped action
        if params.get("loop"):
            client_models[request.sid].start_gripping(str(params["id"]))
        # one-time action
        else:
            client_models[request.sid].grip(str(params["id"]))


@socketio.on("stop_grip")
def stop_grip(params):
    model = client_models[request.sid]
    # check the arguments and make sure the gripper exists
    good_params = check_parameters(params, model, {"id"})

    if good_params:
        model.stop_gripping(str(params["id"]))
