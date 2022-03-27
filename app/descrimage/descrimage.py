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


@descrimage_bp.route("/", methods=["GET", "POST"])
def homepage():
    """
    Interactive interface.
    """
    if "token" in request.form:
        token = request.form['token']

        return receiver(token)

    else:
        return render_template("home.html")

@descrimage_bp.route("/<token>", methods=["GET"])
def candidate_page(token):
    return giver(token)


#@descrimage_bp.route('/receiver', methods=['GET'])
def receiver(token):
    with open(f"app/descrimage/data/{token}.pckl", "rb") as infile:
        data = pickle.load(infile)

    states = [i for i in range(len(data["states"]))]
    room_manager.add_room(token, data["config"])

    # to_replace = list(data["states"][0]["grippers"].keys())[0]
    # data["states"][0]["grippers"]["init"] = data["states"][0]["grippers"][to_replace]
    # data["states"][0]["grippers"]["init"]["id_n"] = "init"
    # del data["states"][0]["grippers"][to_replace]

    for o in data["states"][0]["objs"].values():
        if o["gripped"] is True:
            print(o)
    room_manager.get_model_of_room(token).set_state(data["states"][0])
    return render_template("receiver.html", token=token, STATES=states)


#@descrimage_bp.route('/giver', methods=['GET'])
def giver(token):
    return render_template("giver.html", token=token)


# SOCKETIO EVENTS
@socketio.on("descrimage_description")
def on_mouseclick(description):

    # do something with description?
    print(description)

    # send to other view the description
    socketio.emit("description_from_server", description)


@socketio.on("descrimage_bad_description")
def on_mouseclick():

    # do something with description?
    print("BAD DESCRIPTION")

    # send to other view the description
    socketio.emit("descrimage_bad_description")


@socketio.on("load_file")
def on_mouseclick(files):
    import pickle
    to_open = pickle.loads(files["0"])
    print(to_open)


@socketio.on("test_person_connected")
def test_person_connected():
    socketio.emit("incoming connection")
