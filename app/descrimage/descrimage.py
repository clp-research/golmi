from datetime import datetime
import json
from pathlib import Path
import secrets
import string

from flask_cors import cross_origin
from flask import render_template, Blueprint

from app import DEFAULT_CONFIG_FILE
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
    __set_state(token, state_to_load)

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

    states = __load_states(token)
    state_id = str(states[state_index]["state_id"])
    data["states"][state_id]["outcome"] = 2

    with open(log_file_path, "w") as ofile:
        json.dump(data, ofile)

    # notify instruction giver he is not doing the task
    # and automatically load the next state
    socketio.emit("warning", room=token)
    __next_state(state_index, token, to_add=0)


@socketio.on("test_person_connected")
def test_person_connected(token):
    socketio.emit("incoming connection", room=token)


@socketio.on("timeout")
def test_person_connected(token):
    socketio.emit("timeout", room=token)


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
def abort(data):
    token = data["token"]
    state_index = data["state"]

    # log aborting of this session
    log_file_path = __prepare_log_file(token)
    with open(log_file_path, "r") as infile:
        data = json.load(infile)

    data["abort"] = True

    states = __load_states(token)
    state_id = str(states[state_index]["state_id"])
    data["states"][state_id]["outcome"] = 3

    with open(log_file_path, "w") as ofile:
        json.dump(data, ofile)

    final_token = __create_token(token)

    data = {
        "message": "Sorry, but the experiment has been aborted.",
        "message_color": "orange",
        "token": final_token,
    }
    __end_experiment(data, token)


def __next_state(this_state: int, token: int, to_add: int):
    """
    load the next state
    parameters:
        - this_state: the index of the current state
        - token: the token of this batch
        - to_add: the points to add to the current score
    """
    states_in_token = __load_states(token)

    # load next state and increase progress bar by 1
    if this_state < len(states_in_token) - 1:
        states = __load_states(token)
        state = states[this_state + 1]
        __set_state(token, state)
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
        final_token = __create_token(token)
        data = {
            "message": "Thanks for your participation!",
            "message_color": "green",
            "token": final_token,
        }
        __end_experiment(data, token)


def __create_token(token, token_len=10):
    """
    creates and logs a token
    the token will encode:
        - timestamp
        - batch_id (argument_token)
        - score
        - aborted
    """
    # TODO: change name of function to avoid confusion.
    # suggestion: score_token

    # TODO: change path and name of tokens.json?

    token_file = Path("app/descrimage/tokens.json")
    if not token_file.exists():
        with open(token_file, "w") as ofile:
            json.dump({}, ofile)

    # read score and if aborted from log file
    log_file_path = __prepare_log_file(token)
    with open(log_file_path, "r") as infile:
        data = json.load(infile)

    aborted = data["abort"]
    score = data["score"]

    # get timestamp in iso format (can be parsed with
    # datetime.fromisoformat())
    timestamp = datetime.now().isoformat()

    # create random token and make sure it's not given yet
    with open(token_file, "r") as infile:
        used_tokens = json.load(infile)

    alphabet = string.ascii_letters + string.digits

    while True:
        giver_token = "".join(secrets.choice(alphabet) for _ in range(token_len))
        if giver_token not in used_tokens:
            break

    used_tokens[giver_token] = {
        "batch_id": token,
        "score": score,
        "aborted": aborted,
        "timestamp": timestamp,
    }

    with open(token_file, "w") as ofile:
        json.dump(used_tokens, ofile)

    return giver_token


def __translate(x, y, granularity):
    return x // granularity, y // granularity


def __prepare_log_file(token):
    """
    returns the path of the log file
    if the log file does not exists yet, this function
    will create an empty one
    """
    # TODO: Problem: if the same token is used more than once
    # the logging function will update the same log file
    # this is problematic because score and descriptions will
    # be modified.
    # Options:
    #     1- make sure a token is only ever used once
    #     2- rename log file using the unique token for the receiver

    # todo make this path configurable
    log_dir = Path(f"{__get_collect_dir()}/logs")
    log_dir.mkdir(exist_ok=True)

    # create an empty log file
    logfile = Path(f"{log_dir}/{token}.log.json")
    if not logfile.exists():
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


def __set_state(token, state):
    """
    loads the given state and make sure
    that a log dictionary for this state
    is included in the log file

    an empty dictionary to log all informations about a state contains:
        description: a list with description(s) from IG
        selected_obj: the id_n of the object selected from the IR (none/null if nothing is selected)
        outcome: based on interactions between users:
            0: 0 points (IR selected the wrong object)
            1: 1 point (IR selected the correct object)
            2: warn (IR warned the IG)
            3: abort (IR aborted the experiment at this state)
    """

    empty_log = {"description": list(), "selected_obj": None, "outcome": None}

    state_id = state["state_id"]
    log_file_path = __prepare_log_file(token)
    with open(log_file_path, "r") as infile:
        data = json.load(infile)

    data["states"][state_id] = empty_log

    with open(log_file_path, "w") as ofile:
        json.dump(data, ofile)

    room_manager.get_model_of_room(token).set_state(state)


def __end_experiment(data, token):
    """
    end an experiment by sending the users a message
    and saving the log file to avoid further changes

    data: {
        "message": the message the IG will see,
        "message_color": color of message,
        "token": the score token for the IG receive payment
    }

    token: the batch_id of this experiment
    """
    unique_token = data["token"]
    log_file_path = __prepare_log_file(token)

    # prepare name for final log file
    filename = str(log_file_path).replace(".log.json", "")
    final_log_path = Path(f"{filename}.{unique_token}.log.json")

    # rename current log file to unique name
    log_file_path.rename(final_log_path)
    socketio.emit("finish", data, room=token)
