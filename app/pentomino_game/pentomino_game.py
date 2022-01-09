import json
import os
from time import time_ns

from flask import Blueprint, render_template, request, abort
from flask_cors import cross_origin

from app import DEFAULT_CONFIG_FILE
from app.app import socketio, check_parameters, room_manager, app
from app.pentomino_game import DEFAULT_GAME_CONFIG_FILE
from model.config import Config
from model.game_config import GameConfig


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


# TODO: make Config + GameConfig updatable
@socketio.on("add_game_room")
def add_game_room(params):
    """
    Room is only added if it does not exist yet.
    """
    good_params = check_parameters(params, None, ["room_id"])
    if good_params:
        room_id = params["room_id"]
        if not room_manager.has_room(room_id):
            default_config = Config.from_json(app.config[DEFAULT_CONFIG_FILE])
            default_game_config = GameConfig.from_json(app.config[DEFAULT_GAME_CONFIG_FILE])
            room_manager.add_game_room(room_id, default_config, default_game_config)

# role is needed if the client wants to join a game
    room_manager.add_client_to_room(request.sid, room_id, params.get("role"))


@socketio.on("join_game")
def join_game(params):
    # Assign a (new) room with the given id
    room_id = params["room_id"] or request.sid + "_room"

    if not room_manager.has_room(room_id):
        # create a new default room
        default_config = Config.from_json(app.config[DEFAULT_CONFIG_FILE])
        default_game_config = GameConfig.from_json(app.config[DEFAULT_GAME_CONFIG_FILE])
        room_manager.add_game_room(room_id, default_config, default_game_config)

    role = params.get("role") or "random"
    try:
        room_manager.add_client_to_room(request.sid, room_id, role)
    # TODO: better error handling here
    except RuntimeError as e:
        print(e)
        print("Client attempted to connected to game with no roles remaining")