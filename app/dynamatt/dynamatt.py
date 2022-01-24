from flask_cors import cross_origin
from flask import render_template, Blueprint, request
from app import DEFAULT_CONFIG_FILE
from app.app import socketio, room_manager

DATA_COLLECTION = "matthew_DATA_COLLECTION"
TASKS = "matthew_TASKS"
AUDIO = "matthew_AUDIO"


def apply_config_to(app):
    """ define global config parameters """
    app.config[DEFAULT_CONFIG_FILE] = "app/dynamatt/static/resources/config/pentomino_config.json"
    app.config[DATA_COLLECTION] = "app/dynamatt/static/resources/data_collection"
    app.config[AUDIO] = "app/dynamatt/static/resources/audio"


dynamatt_bp = Blueprint('dynamatt_bp', __name__,
                        template_folder='templates',
                        static_folder='static',
                        url_prefix="/dynamatt")


@cross_origin
@dynamatt_bp.route("/", methods=["GET"])
def dynamatt():
    return render_template("dynamatt.html")


@socketio.on("dynamatt_mouseclick")
def on_mouseclick(event):
    # looks like we need a "mouse"-gripper b.c. everything expects a gripper instance
    model = room_manager.get_models_of_client(request.sid)[0]
    x, y = translate(event["offset_x"], event["offset_y"], event["block_size"])

    # I should not need to know "state
    # deselect all
    for obj in model.state.objs.values():
        obj.gripped = False

    # select single piece if possible
    odj_id = get_object_id_at_pos(model, x, y)
    if odj_id is not None:
        model.state.objs[odj_id].gripped = True

    # I should not need to "notify" via the model
    model._notify_views("update_objs", model.get_obj_dict())


def translate(x, y, granularity):
    return x // granularity, y // granularity


def get_object_id_at_pos(model, x, y):
    tile = model.object_grid.get_single_tile({"x": x, "y": y})
    # if there is an object on tile, return last object id
    if tile.objects:
        return tile.objects[-1]
    return None
