from flask_cors import cross_origin
from flask import render_template, Blueprint, request
from app import DEFAULT_CONFIG_FILE
from app.app import socketio, client_models
from app.neureg import tasks
from model.pentomino import Board, PieceConfig, Colors, Shapes, RelPositions, PropertyNames
from model.state import State


def apply_config_to(app):
    """ define global config parameters """
    app.config[DEFAULT_CONFIG_FILE] = "app/compreg/static/resources/config/pentomino_config.json"


compreg_bp = Blueprint("compreg_bp", __name__,
                       template_folder='templates',
                       static_folder='static',
                       url_prefix="/compreg")


@cross_origin
@compreg_bp.route("/", methods=["GET"])
def compreg():
    return render_template("compreg.html")


@socketio.on("new_comp_scene")
def on_new_comp_scene(event):
    controls = event["controls"]
    property_name = PropertyNames.from_string(controls["property_name"])

    model = client_models[request.sid]
    target = PieceConfig(Colors.BLUE, Shapes.T, RelPositions.CENTER)
    board = Board.create_compositional(board_width=model.config.width,
                                       board_height=model.config.height,
                                       piece_config=target,
                                       unique_props={property_name},
                                       num_distractors=4)
    # uff this is ugly
    state = State()
    state.objs = dict([(piece.piece_id, piece.piece_obj) for piece in board.pieces])
    model.set_state(state)


@socketio.on("mouseclick")
def on_mouseclick(event):
    # looks like we need a "mouse"-gripper b.c. everything expects a gripper instance
    model = client_models[request.sid]
    x, y = translate(event["offset_x"], event["offset_y"], event["block_size"])

    # deselect all
    pieces = model.state.objs.values()
    for obj in pieces:
        obj.gripped = False

    # select single piece if possible
    odj_id = get_object_id_at_pos(model, x, y)
    if odj_id is not None:
        selected = model.state.objs[odj_id]
        selected.gripped = True

    # redraw highlighting
    model._notify_views("update_objs", model.get_obj_dict())


def translate(x, y, granularity):
    return x // granularity, y // granularity


def get_object_id_at_pos(model, x, y):
    tile = model.object_grid.get_single_tile({"x": x, "y": y})
    # if there is an object on tile, return last object id
    if tile.objects:
        return tile.objects[-1]
    return None
