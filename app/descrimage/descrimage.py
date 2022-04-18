import os.path

from flask_cors import cross_origin

from app import DEFAULT_CONFIG_FILE
from flask import render_template, Blueprint
import json
from app.app import app, socketio, room_manager, get_default_config

from neureg.data.types import DataCollectionState


def apply_config_to(app):
    app.config[
        DEFAULT_CONFIG_FILE
    ] = "app/descrimage/static/resources/config/descrimage_config.json"


descrimage_bp = Blueprint(
    "descrimage_bp",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/descrimage",
)


@cross_origin
@descrimage_bp.route("/", methods=["GET"])
def home():
    return render_template("home.html")


@cross_origin
@descrimage_bp.route("/r/<token>", methods=["GET"])
def receiver_page(token):
    return receiver(token)


@cross_origin
@descrimage_bp.route("/g/<token>", methods=["GET"])
def giver_page(token):
    states = __load_states(token)
    return render_template(
        "giver.html", token=token, n_states=len(states), this_state=0
    )


def receiver(token):
    __prepare_log_file(token)
    room_manager.add_room(token, get_default_config())
    states = __load_states(token)
    state_to_load = states[0]
    room_manager.get_model_of_room(token).set_state(state_to_load)
    return render_template(
        "receiver.html", token=token, n_states=len(states), this_state=0
    )


# SOCKETIO EVENTS
@socketio.on("descrimage_description")
def send_description(data):
    description = data["description"]
    token = data["token"]
    state_index = int(data["state"])

    # get state identification number
    states_in_token = __load_states(token)
    state_id = str(states_in_token[state_index]["state_id"])

    # open log of this batch
    log_file_path = __prepare_log_file(token)
    with open(log_file_path, "r") as infile:
        data = json.load(infile)

    # add this description to the ist
    if state_id not in data:
        data["states"][state_id] = {"description": list(), "selected_obj": None}

    data["states"][state_id]["description"].append(description)

    with open(log_file_path, "w") as ofile:
        json.dump(data, ofile)

    # send to other view the description
    socketio.emit("description_from_server", description, room=token)


@socketio.on("warning")
def warning(data):
    """
    Warning from receiver:
        - go to next state
        - remove 1 point
    """
    token = data["token"]
    state_index = int(data["state"])

    # load log file
    log_file_path = __prepare_log_file(token)
    with open(log_file_path, "r") as infile:
        data = json.load(infile)

    data["score"] = -1

    # notify instruction giver he is not doing the task
    socketio.emit("warning", room=token)

    __next_state(state_index, token, to_add=-1)


@socketio.on("test_person_connected")
def test_person_connected(token):
    socketio.emit("incoming connection", room=token)


@socketio.on("timeout")
def test_person_connected(token):
    socketio.emit("timeout", room=token)


@socketio.on("load_state_index")
def load_state_index(index, token):
    states = __load_states(token)
    state = states[index]
    room_manager.get_model_of_room(token).set_state(state)


@socketio.on("descrimage_mouseclick")
def on_mouseclick(event):
    print("CLICK")
    # looks like we need a "mouse"-gripper b.c. everything expects a gripper instance
    token = event["token"]
    model = room_manager.get_model_of_room(token)
    x, y = __translate(event["offset_x"], event["offset_y"], event["block_size"])

    if "mouse" in model.state.grippers:
        model.remove_gr("mouse")
        for obj in model.state.objs.values():
            obj.gripped = False

    model.add_gr("mouse", x, y)
    model.grip("mouse")

    grippers = model.get_gripper_dict()
    gripped = grippers["mouse"]["gripped"]

    if gripped is not None:
        socketio.sleep(1)
        # user selected an item, go to next state
        target = model.state.to_dict()["targets"]

        # add gripped property to target dict
        for target_idn in target.keys():
            target[target_idn]["gripped"] = True

        if target == gripped:
            to_add = 1
        else:
            to_add = 0

        this_state = int(event["this_state"])
        states_in_token = __load_states(token)
        state_id = str(states_in_token[this_state]["state_id"])

        # load log file
        log_file_path = __prepare_log_file(token)
        with open(log_file_path, "r") as infile:
            data = json.load(infile)

        # log selected object
        selected_key = set(gripped.keys()).pop()
        gripped_id_n = gripped[selected_key]["id_n"]
        data["states"][state_id]["selected_obj"] = int(gripped_id_n)

        # log score
        data["score"] += to_add

        with open(log_file_path, "w") as ofile:
            json.dump(data, ofile)

        # load next state
        __next_state(this_state, token, to_add)

    else:
        # remove the mouse gripper
        if "mouse" in model.state.grippers:
            model.remove_gr("mouse")


@socketio.on("abort")
def abort(token):
    # log aborting of this session
    log_file_path = __prepare_log_file(token)
    with open(log_file_path, "r") as infile:
        data = json.load(infile)

    data["abort"] = True

    with open(log_file_path, "w") as ofile:
        json.dump(data, ofile)

    message = "your partner aborted this session <br> You can now close this window"
    socketio.emit("finish", message, room=token)


def __next_state(this_state: int, token: int, to_add: int):
    """
    load the next state
    parameters:
        - this_state: the index of the current state
        - token: the token of this batch
        - to_add: the points to add to the current score
    """
    states_in_token = __load_states(token)

    #
    if this_state < len(states_in_token) - 1:
        states = __load_states(token)
        state = states[this_state + 1]
        room_manager.get_model_of_room(token).set_state(state)
        socketio.emit(
            "next_state",
            {"next_state": this_state + 1, "score_delta": to_add},
            room=token,
        )
    # this is the last state, increase the progress bar
    # (front end is 1 indexed, backend 0)
    # we do not change the state of the model
    else:
        socketio.emit(
            "next_state",
            {"next_state": this_state + 1, "score_delta": to_add},
            room=token,
        )

        # calculate token
        final_token = __create_token()
        message = (
            f"We're done here.<br> Don't forget your token: {final_token}"
            "<br> Thank you for participating"
        )
        socketio.emit("finish", message, room=token)


def __create_token():
    """
    creates and logs a token
    """
    return "0bhWlm"


def __translate(x, y, granularity):
    return x // granularity, y // granularity


def __prepare_log_file(token):
    # todo make this path configurable
    log_dir = __get_collect_dir() + "/logs"
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)

    # create an empty log file
    logfile = f"{log_dir}/{token}.log.json"
    if not os.path.exists(logfile):
        print("Create log file at", logfile)
        with open(logfile, "w") as f:
            json.dump({"score": 0, "abort": False, "states": dict()}, f)
    return logfile


def __get_collect_dir():
    collect_dir = app.config["COLLECT_DIR"]
    return collect_dir


def __load_states(token):
    data = DataCollectionState.load_many(__get_collect_dir(), file_name=token)
    states = []
    for d in data:
        anno = d["annotation"]
        state = d["state"]
        target_idx = anno["target"]
        target = state["objs"][str(target_idx)]
        state["targets"][target["id_n"]] = target
        states.append(state)
    return states
