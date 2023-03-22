from flask_cors import cross_origin
from flask import render_template, Blueprint, jsonify

from app.app import app, socketio, room_manager

from app import DEFAULT_CONFIG_FILE

def apply_config_to(app):
    app.config[
        DEFAULT_CONFIG_FILE
    ] = "None"


slurk = Blueprint(
    'slurk',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix="/slurk"
)


@cross_origin
@slurk.route("/", methods=["GET"])
def slurk_home():
    return "added functionalities for the integration with the slurk project"


def __translate(x, y, granularity):
    """
    convert coordinates from the frontend
    """
    return x // granularity, y // granularity


@cross_origin
@slurk.route("/remove_mouse_gripper/<room_id>", methods=["GET"])
def remove_mouse_gripper(room_id):
    model = room_manager.get_model_of_room(room_id)
    if "mouse" in model.state.grippers:
        model.remove_gr("mouse")
        for obj in model.state.objs.values():
            obj.gripped = False

    model._notify_views(
        "update_state",
        model.state.to_dict()
    )
    return dict(status="removed")


@cross_origin
@slurk.route("/grip/<room_id>/<x>/<y>/<blocksize>", methods=["GET"])
def grip_object(room_id, x, y, blocksize):
    model = room_manager.get_model_of_room(room_id)
    x, y = __translate(float(x), float(y), float(blocksize))

    if "mouse" in model.state.grippers:
        model.remove_gr("mouse")
        for obj in model.state.objs.values():
            obj.gripped = False

    model.add_gr("mouse", x, y)
    model.grip("mouse")

    grippers = model.get_gripper_dict()
    gripped = grippers["mouse"]["gripped"]

    if gripped is not None:
        return jsonify(gripped)

    return dict()


@cross_origin
@slurk.route("/<room_id>/<x>/<y>/<blocksize>", methods=["GET"])
def get_clicked_object(room_id, x, y, blocksize):
    model = room_manager.get_model_of_room(room_id)
    x, y = __translate(float(x), float(y), float(blocksize))

    tile = model.state.get_tile(x, y)
    if tile.objects:
        obj = tile.objects[-1].to_dict()
        return jsonify({
            str(obj["id_n"]): obj
        })

    return dict()


@cross_origin
@slurk.route("/<room_id>/gripped", methods=["GET"])
def get_gripped_object(room_id):
    model = room_manager.get_model_of_room(room_id)

    for idn, obj in model.get_obj_dict().items():
        if obj.get("gripped") is True:
            return jsonify({idn: obj})

    return dict()


@cross_origin
@slurk.route("/<room_id>/state", methods=["GET"])
def get_state(room_id):
    model = room_manager.get_model_of_room(room_id)
    return jsonify(model.state.to_dict())
