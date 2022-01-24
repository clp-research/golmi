from flask_cors import cross_origin
from flask import render_template, Blueprint, request
from app import DEFAULT_CONFIG_FILE
from app.app import socketio, room_manager
from model.pentomino import Board, PieceConfig, Colors, Shapes, RelPositions, PropertyNames, create_distractor_configs
from model.state import State
import random


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


def create_surface_structure(target: PieceConfig, properties: set[PropertyNames],
                             always_mention: list[PropertyNames] = []):
    shape = "piece"
    color = ""
    position = ""

    if PropertyNames.SHAPE in properties or PropertyNames.SHAPE in always_mention:
        shape = target[PropertyNames.SHAPE].value_name

    if PropertyNames.COLOR in properties or PropertyNames.COLOR in always_mention:
        color = target[PropertyNames.COLOR].value_name

    if PropertyNames.REL_POSITION in properties or PropertyNames.REL_POSITION in always_mention:
        position = f"in the {target[PropertyNames.REL_POSITION].value}"

    ref_exp = f"{color} {shape} {position}".strip()  # strip whitespaces if s.t. is empty
    return f"Take the {ref_exp}"


@socketio.on("compreg_new_scene")
def on_new_comp_scene(event):
    scene_config = event["scene_config"]
    unique_properties = scene_config["target_piece"]["unique_properties"]
    property_name = PropertyNames.from_string(unique_properties[0])
    if property_name is None:
        print(f"Cannot compose scene for '{property_name}'")

    distractors_config = scene_config["distractors"]
    varieties_config = scene_config["varieties"]
    ambiguity_config = scene_config["ambiguity"]

    model = room_manager.get_models_of_client(request.sid)[0]
    target_piece_color_selected = scene_config["target_piece"]["color"]
    target_piece_shape_selected = scene_config["target_piece"]["shape"]
    piece_rel_position_selected = scene_config["target_piece"]["rel_position"]

    try:
        target_piece_color = Colors[target_piece_color_selected]
    except:
        target_piece_color = random.choice(list(Colors))
    try:
        target_piece_shape = Shapes[target_piece_shape_selected]
    except:
        target_piece_shape = random.choice(list(Shapes))
    try:
        piece_rel_position = RelPositions[piece_rel_position_selected]
    except:
        piece_rel_position = random.choice(list(RelPositions))

    target = PieceConfig(target_piece_color, target_piece_shape, piece_rel_position)
    unique_props = {property_name}
    distractors = create_distractor_configs(piece_config=target, unique_props=unique_props,
                                            num_distractors=distractors_config["num_distractors"],
                                            varieties={
                                                PropertyNames.COLOR: varieties_config["num_colors"],
                                                PropertyNames.SHAPE: varieties_config["num_shapes"],
                                                PropertyNames.REL_POSITION: varieties_config["num_positions"],
                                            },
                                            ambiguities={
                                                PropertyNames.COLOR: ambiguity_config["num_colors"],
                                                PropertyNames.SHAPE: ambiguity_config["num_shapes"],
                                                PropertyNames.REL_POSITION: ambiguity_config["num_positions"],
                                            })
    instruction = create_surface_structure(target, unique_props)
    board = Board.create_compositional_from_configs(board_width=model.config.width, board_height=model.config.height,
                                                    piece_config=target, distractors=distractors)
    # uff this is ugly
    state = State()
    state.objs = dict([(piece.piece_id, piece.piece_obj) for piece in board.pieces])
    model.set_state(state)

    model._notify_views("update_instructions", instruction)


@socketio.on("compreg_mouseclick")
def on_mouseclick(event):
    # looks like we need a "mouse"-gripper b.c. everything expects a gripper instance
    model = room_manager.get_models_of_client(request.sid)[0]
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
