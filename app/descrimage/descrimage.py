import os.path

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


@descrimage_bp.route("/r/<token>", methods=["GET"])
def receiver_page(token):
    return receiver(token)


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
    state_to_load = __prepare_state(states, 0)
    room_manager.get_model_of_room(token).set_state(state_to_load)
    return render_template("receiver.html", token=token, n_states=len(states), this_state=0)


# SOCKETIO EVENTS
@socketio.on("descrimage_description")
def send_description(data):
    description = data["description"]
    token = data["token"]
    state_index = str(data["state"])

    log_file_path = __prepare_log_file(token)
    with open(log_file_path, "r") as infile:
        data = json.load(infile)

    if state_index not in data:
        data[state_index] = list()

    data[state_index].append({"description": description})

    with open(log_file_path, "w") as infile:
        json.dump(data, infile)

    # send to other view the description
    socketio.emit("description_from_server", description)


@socketio.on("descrimage_bad_description")
def bad_description(data):
    description = data["description"]
    token = data["token"]
    state_index = str(data["state"])

    log_file_path = __prepare_log_file(token)
    with open(log_file_path, "r") as infile:
        data = json.load(infile)

    this_description = {"description": description}
    # TODO: if description was already bad cannot catch it
    if this_description in data[state_index]:
        to_modify = data[state_index].index(this_description)
        data[state_index][to_modify]["bad description"] = True
    else:
        this_description["bad description"] = True
        to_modify = data[state_index].append(this_description)

    with open(log_file_path, "w") as infile:
        json.dump(data, infile)

    # send to other view the description
    socketio.emit("descrimage_bad_description")


@socketio.on("test_person_connected")
def test_person_connected():
    socketio.emit("incoming connection")


@socketio.on("load_state_index")
def load_state_index(index, token):
    states = __load_states(token)
    state = __prepare_state(states, index)
    room_manager.get_model_of_room(token).set_state(state)


@socketio.on("descrimage_mouseclick")
def on_mouseclick(event):
    # looks like we need a "mouse"-gripper b.c. everything expects a gripper instance
    token = event["token"]
    model = room_manager.get_model_of_room(token)
    x, y = translate(event["offset_x"], event["offset_y"], event["block_size"])

    if "mouse" in model.state.grippers:
        model.remove_gr("mouse")
        for obj in model.state.objs.values():
            obj.gripped = False

    model.add_gr("mouse", x, y)
    model.grip("mouse")

    grippers = model.get_gripper_dict()
    target = grippers["init"]["gripped"]
    gripped = grippers["mouse"]["gripped"]

    if target == gripped:
        this_state = int(event["this_state"])
        if this_state < int(event["n_states"]) - 1:
            states = __load_states(token)
            state = __prepare_state(states, this_state + 1)
            room_manager.get_model_of_room(token).set_state(state)
            socketio.emit("next_state", this_state + 1)
        else:
            socketio.emit("next_state", this_state + 1)
            socketio.emit("finish")


def translate(x, y, granularity):
    return x // granularity, y // granularity


def __prepare_log_file(token):
    # todo make this path configurable
    log_dir = __get_collect_dir() + "/logs"
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    logfile = f"{log_dir}/{token}.log.json"
    if not os.path.exists(logfile):
        print("Create log file at", logfile)
        with open(logfile, "w") as f:
            json.dump({}, f)
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


def __prepare_state(states, index):
    # replace gripper with init gripper
    if len(states[index]["grippers"]) > 0:
        to_replace = list(states[index]["grippers"].keys())[0]
        states[index]["grippers"]["init"] = states[index]["grippers"][to_replace]
        states[index]["grippers"]["init"]["id_n"] = "init"
        del states[index]["grippers"][to_replace]
    else:
        init_gripper = {"id_n": "init", "x": 0, "y": 0, "color": "blue"}
        states[index]["grippers"]["init"] = init_gripper
    return states[index]
