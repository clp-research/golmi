from app import DEFAULT_CONFIG_FILE
from flask import render_template, Blueprint, request, abort
from flask_cors import cross_origin
import json
from datetime import datetime
from app.app import socketio, room_manager
from pathlib import Path


def apply_config_to(app):
    app.config[DEFAULT_CONFIG_FILE] = (
        "app/descrimage/static/resources/config/descrimage_config.json"
    )


descrimage_bp = Blueprint('descrimage_bp', __name__,
                         template_folder='templates',
                         static_folder='static',
                         url_prefix="/descrimage")


@descrimage_bp.route("/r/<token>", methods=["GET"])
def receiver_page(token):
    return receiver(token)


@descrimage_bp.route("/g/<token>", methods=["GET"])
def giver_page(token):
    with open(f"app/descrimage/data/{token}.json", "rb") as infile:
        data = json.load(infile)

    states = [i for i in range(len(data["states"]))]

    return render_template("giver.html", token=token, n_states=len(states), this_state=0)

 
def receiver(token):
    to_load = Path(f"app/descrimage/data/{token}.json")
    with open(to_load, "r") as infile:
        data = json.load(infile)

    logfile = Path(f"app/descrimage/data/{token}.log.json")
    if not logfile.exists:
        with open(logfile, "w") as infile:
            json.dump({}, infile)

    states = [i for i in range(len(data["states"]))]
    room_manager.add_room(token, data["config"])

    state_to_load = prepare_state(token, 0)

    room_manager.get_model_of_room(token).set_state(state_to_load)
    return render_template("receiver.html", token=token, STATES=states, n_states=len(states), this_state=0)


# SOCKETIO EVENTS
@socketio.on("descrimage_description")
def send_description(data):
    description = data["description"]
    token = data["token"]
    state_index = str(data["state"])

    with open(f"app/descrimage/data/{token}.log.json", "r") as infile:
        data = json.load(infile)

    if state_index not in data:
        data[state_index] = list()

    data[state_index].append({"description": description})

    with open(f"app/descrimage/data/{token}.log.json", "w") as infile:
        json.dump(data, infile)

    # send to other view the description
    socketio.emit("description_from_server", description)


@socketio.on("descrimage_bad_description")
def bad_description(data):

    description = data["description"]
    token = data["token"]
    state_index = str(data["state"])

    with open(f"app/descrimage/data/{token}.log.json", "r") as infile:
        data = json.load(infile)

    this_description = {"description": description}

    to_modify = data[str(state_index)].index(this_description)
    data[state_index][to_modify]["bad description"] = True

    with open(f"app/descrimage/data/{token}.log.json", "w") as infile:
        json.dump(data, infile)

    # send to other view the description
    socketio.emit("descrimage_bad_description")


@socketio.on("test_person_connected")
def test_person_connected():
    socketio.emit("incoming connection")


@socketio.on("load_state_index")
def load_state_index(index, token):
    state = prepare_state(token, index)
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
        if this_state < int(event["n_states"]) -1:
            state = prepare_state(token, this_state + 1)
            room_manager.get_model_of_room(token).set_state(state)
            socketio.emit("next_state", this_state + 1)
        else:
            socketio.emit("next_state", this_state + 1)
            socketio.emit("finish")
   

def translate(x, y, granularity):
    return x // granularity, y // granularity


def prepare_state(token, index):
    # open state
    with open(f"app/descrimage/data/{token}.json", "rb") as infile:
        data = json.load(infile)

    # replace gripper with init gripper
    to_replace = list(data["states"][index]["grippers"].keys())[0]
    data["states"][index]["grippers"]["init"] = data["states"][index]["grippers"][to_replace]
    data["states"][index]["grippers"]["init"]["id_n"] = "init"
    del data["states"][index]["grippers"][to_replace]

    return data["states"][index]