from flask_cors import cross_origin
from flask import render_template, Blueprint, request
from app import DEFAULT_CONFIG_FILE
from app.app import socketio, client_models
from app.neureg import tasks


def apply_config_to(app):
    """ define global config parameters """
    app.config[DEFAULT_CONFIG_FILE] = "app/neureg/static/resources/config/pentomino_config.json"


neureg_bp = Blueprint("neureg_bp", __name__,
                      template_folder='templates',
                      static_folder='static',
                      url_prefix="/neureg")


@cross_origin
@neureg_bp.route("/", methods=["GET"])
def neureg():
    return render_template("neureg.html")


@socketio.on("new_scene")
def on_new_scene(event):
    model = client_models[request.sid]
    model.set_random_state(n_objs=event["n_objs"], n_grippers=0)
    model._notify_views("update_instructions", [])


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
    instructions = []
    odj_id = get_object_id_at_pos(model, x, y)
    if odj_id is not None:
        selected = model.state.objs[odj_id]
        selected.gripped = True

        generator = tasks.TaskGenerator(model.config)
        task = generator.generate_random_sample_for_scene(pieces, selected, permute_props=True)
        instructions = task["refs"]

    # redraw highlighting
    model._notify_views("update_objs", model.get_obj_dict())

    # redraw instructions
    model._notify_views("update_instructions", instructions)


def translate(x, y, granularity):
    return x // granularity, y // granularity


def get_object_id_at_pos(model, x, y):
    tile = model.object_grid.get_single_tile({"x": x, "y": y})
    # if there is an object on tile, return last object id
    if tile.objects:
        return tile.objects[-1]
    return None
