from flask_cors import cross_origin
from flask import render_template, Blueprint

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
    static_folder='static'
)


def __translate(x, y, granularity):
    """
    convert coordinates from the frontend
    """
    return x // granularity, y // granularity


@cross_origin
@slurk.route("/<room_id>/<x>/<y>/<blocksize>", methods=["GET"])
def return_clicked_object(room_id, x, y, blocksize):
    model = room_manager.get_model_of_room(room_id)
    x, y = __translate(float(x), float(y), float(blocksize))

    print(room_manager.room_to_model)
    print(model)
    print(model.state.grippers)


    if "mouse" in model.state.grippers:
        model.remove_gr("mouse")
        for obj in model.state.objs.values():
            obj.gripped = False

    model.add_gr("mouse", x, y)
    model.grip("mouse")

    grippers = model.get_gripper_dict()
    gripped = grippers["mouse"]["gripped"]

    model.remove_gr("mouse")

    if gripped is not None:
        return gripped

    return dict()
