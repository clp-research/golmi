from app import DEFAULT_CONFIG_FILE
from flask import render_template, Blueprint, request, abort
from flask_cors import cross_origin
import json
import os
from datetime import datetime


def apply_config_to(app):
    app.config[DEFAULT_CONFIG_FILE] = (
        "app/pentomino/static/resources/config/pentomino_config.json"
    )


pentomino_bp = Blueprint('pentomino_bp', __name__,
                         template_folder='templates',
                         static_folder='static',
                         url_prefix="/pentomino")

@cross_origin
@pentomino_bp.route("/", methods=["GET"])
def pentomino():
    """
    Interactive interface.
    """
    return render_template("pentomino.html")


@cross_origin
@pentomino_bp.route("/save_log", methods=["POST"])
def save_log():
    if not request.data or not request.is_json:
        abort(400)
    json_data = request.json
    # as a filename that
    # (1) can not be manipulated by a client
    # (2) has a negligible chance of collision
    # a timestamp is used
    filename = datetime.now().strftime("%y%m%d_%H%M%S_%f") + ".json"
    # check if "data_collection" directory exists, create if necessary
    save_path = "app/pentomino/static/resources/data_collection"
    if not os.path.exists(save_path):
        os.mkdir(save_path)

    outputfile = os.path.join(save_path, filename)
    with open(outputfile, encoding="utf-8", mode="w") as f:
        f.write(json.dumps(json_data, indent=2))
    return "0", 200
