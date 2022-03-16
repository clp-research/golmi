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

@cross_origin
@descrimage_bp.route("/", methods=["GET"])
def descrimage():
    """
    Interactive interface.
    """
    return render_template("descrimage.html")

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