import json
import os
from time import time_ns

from flask import Blueprint, render_template, request, abort
from flask_cors import cross_origin

from app import DEFAULT_CONFIG_FILE
from app.pentomino_game import DEFAULT_GAME_CONFIG_FILE


def apply_config_to(app):
    app.config[DEFAULT_CONFIG_FILE] = "app/pentomino/static/resources/config/pentomino_config.json"
    app.config[DEFAULT_GAME_CONFIG_FILE] = "app/pentomino_game/static/resources/game_config/pentomino_game_config.json"


pentomino_game_bp = Blueprint('pentomino_game_bp', __name__,
                         template_folder='templates',
                         static_folder='static',
                         url_prefix="/pentomino_game")

@cross_origin
@pentomino_game_bp.route("/", methods=["GET"])
def pentomino():
    """
    Interactive interface.
    """
    return render_template("pentomino_game.html")


@cross_origin
@pentomino_game_bp.route("/save_log", methods=["POST"])
def save_log():
    if not request.data or not request.is_json:
        abort(400)
    json_data = request.json
    # as a filename that
    # (1) can not be manipulated by a client
    # (2) has a negligible chance of collision
    # a simple timestamp is used
    filename = str(time_ns() / 100) + ".json"
    # check if "data_collection" directory exists, create if necessary
    save_path = "app/pentomino_game/static/resources/data_collection"
    if not os.path.exists(save_path):
        os.mkdir(save_path)
    with open(os.path.join(save_path, filename), encoding="utf-8", mode="w") as f:
        f.write(json.dumps(json_data, indent=2))
    return "0", 200

