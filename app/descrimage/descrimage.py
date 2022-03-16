from app import DEFAULT_CONFIG_FILE
from flask import render_template, Blueprint, request, abort
from flask_cors import cross_origin
import json
import os
from datetime import datetime


def apply_config_to(app):
    app.config[DEFAULT_CONFIG_FILE] = (
        "app/descrimage/static/resources/config/descrimage_config.json"
    )


descrimage_bp = Blueprint('descrimage_bp', __name__,
                         template_folder='templates',
                         static_folder='static',
                         url_prefix="/descrimage")

# @cross_origin
# @descrimage_bp.route("/", methods=["GET"])
# def descrimage():
#     """
#     Interactive interface.
#     """
#     return render_template("descrimage.html")


#@cross_origin
@descrimage_bp.route("/", methods=["GET"])
def homepage():
    """
    Interactive interface.
    """
    return render_template("home.html")

@cross_origin
@descrimage_bp.route('/', methods=['POST'])
def my_form_post():
    token = request.form['token']
    token, role = token.split("-")

    if role == "1":
        return receiver(token)
    elif role == "2":
        return giver(token)
    else:
        return "INVALID TOKEN"

#@descrimage_bp.route('/receiver', methods=['GET'])
def receiver(token):
    return render_template("receiver.html", token=token)

#@descrimage_bp.route('/giver', methods=['GET'])
def giver(token):
    return render_template("giver.html", token=token)


# TODO: add socketios
# @socketio.on("dynamatt_mouseclick")
# def on_mouseclick(event):
#     # looks like we need a "mouse"-gripper b.c. everything expects a gripper instance
#     model = room_manager.get_models_of_client(request.sid)[0]
#     x, y = translate(event["offset_x"], event["offset_y"], event["block_size"])

#     if "mouse" in model.state.grippers:
#         model.remove_gr("mouse")
#         for obj in model.state.objs.values():
#             obj.gripped = False

#     model.add_gr("mouse", x, y)
#     model.grip("mouse")