from app import DEFAULT_CONFIG_FILE
from flask import render_template, Blueprint, request, abort
from flask_cors import cross_origin
import json
import os
from datetime import datetime
import pickle
from app.app import socketio, room_manager


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
    return receiver(token, 0)


@descrimage_bp.route("/g/<token>", methods=["GET"])
def giver_page(token):
    return render_template("giver.html", token=token)

 
def receiver(token, state_index):
    with open(f"app/descrimage/data/{token}.json", "rb") as infile:
        data = json.load(infile)

    states = [i for i in range(len(data["states"]))]
    room_manager.add_room(token, data["config"])

    to_replace = list(data["states"][state_index]["grippers"].keys())[0]
    data["states"][state_index]["grippers"]["init"] = data["states"][0]["grippers"][to_replace]
    data["states"][state_index]["grippers"]["init"]["id_n"] = "init"
    del data["states"][state_index]["grippers"][to_replace]

    room_manager.get_model_of_room(token).set_state(data["states"][state_index])
    return render_template("receiver.html", token=token, STATES=states)


# SOCKETIO EVENTS
@socketio.on("descrimage_description")
def send_description(description):

    # do something with description?
    print(description)

    # send to other view the description
    socketio.emit("description_from_server", description)


@socketio.on("descrimage_bad_description")
def bad_description():

    # do something with description?
    print("BAD DESCRIPTION")

    # send to other view the description
    socketio.emit("descrimage_bad_description")


@socketio.on("load_file")
def load_file(files):
    import pickle
    to_open = pickle.loads(files["0"])
    print(to_open)


@socketio.on("test_person_connected")
def test_person_connected():
    socketio.emit("incoming connection")


@socketio.on("load_state_index")
def load_state_index(index, token):
    with open(f"app/descrimage/data/{token}.json", "rb") as infile:
        data = json.load(infile)

    to_replace = list(data["states"][index]["grippers"].keys())[0]
    data["states"][index]["grippers"]["init"] = data["states"][index]["grippers"][to_replace]
    data["states"][index]["grippers"]["init"]["id_n"] = "init"
    del data["states"][index]["grippers"][to_replace]

    room_manager.get_model_of_room(token).set_state(data["states"][index])


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
   

def translate(x, y, granularity):
    return x // granularity, y // granularity
