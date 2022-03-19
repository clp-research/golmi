from app import DEFAULT_CONFIG_FILE
from flask import render_template, Blueprint, request, abort
from flask_cors import cross_origin
import json
import os
from datetime import datetime
from app.app import socketio


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
        token, role = token.split("-")

        if role == "1":
            return receiver(token)
        elif role == "2":
            return giver(token)
        else:
            return "INVALID TOKEN"
    else:
        return render_template("home.html")


#@descrimage_bp.route('/receiver', methods=['GET'])
def receiver(token):
    return render_template("receiver.html", token=token)


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
def on_mouseclick(data):

    # do something with description?
    print("BAD DESCRIPTION")

    # send to other view the description
    socketio.emit("descrimage_bad_description")
