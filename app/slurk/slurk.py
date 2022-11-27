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


# @socketio.on("slurk_mouseclick")
# def slurk_click(event):
#     token = event["token"]
#     model = room_manager.get_model_of_room(token)
#     x, y = __translate(event["offset_x"], event["offset_y"], event["block_size"])

#     if "mouse" in model.state.grippers:
#         model.remove_gr("mouse")
#         for obj in model.state.objs.values():
#             obj.gripped = False

#     model.add_gr("mouse", x, y)
#     model.grip("mouse")

#     grippers = model.get_gripper_dict()
#     gripped = grippers["mouse"]["gripped"]

#     print(gripped)

    # if gripped is not None:
    #     timestamp = datetime.now().isoformat()
    #     socketio.sleep(1)
    #     # user selected an item, go to next state
    #     target = model.state.to_dict()["targets"]

    #     # add gripped property to target dict
    #     for target_idn in target.keys():
    #         target[target_idn]["gripped"] = True

    #     this_state = int(event["this_state"])
    #     states_in_token = __load_states(token)
    #     state_id = str(states_in_token[this_state]["state_id"])

    #     # load log file
    #     log_file_path = __get_log_file(token)
    #     with open(log_file_path, "r") as infile:
    #         data = json.load(infile)

    #     # log selected object
    #     selected_key = set(gripped.keys()).pop()
    #     gripped_id_n = gripped[selected_key]["id_n"]
    #     data["states"][state_id]["selected_obj"] = int(gripped_id_n)
    #     data["states"][state_id]["timestamp_end"] = timestamp

    #     if target == gripped:
    #         to_add = 1
    #     else:
    #         to_add = 0

    #     # log score and outcome of state
    #     data["score"] += to_add
    #     data["states"][state_id]["outcome"] = to_add

    #     with open(log_file_path, "w") as ofile:
    #         json.dump(data, ofile)

    #     # load next state
    #     __next_state(this_state, token, to_add)

    # else:
    #     # remove the mouse gripper
    if "mouse" in model.state.grippers:
        model.remove_gr("mouse")