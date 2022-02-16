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

    if "mouse" in model.state.grippers:
        model.remove_gr("mouse")
        for obj in model.state.objs.values():
            obj.gripped = False

    model.add_gr("mouse", x, y)
    model.grip("mouse")
 
    # # I should not need to know "state
    # deselect all
    # for obj in model.state.objs.values():
    #     obj.gripped = False

    # # select single piece if possible
    # odj_id = get_object_id_at_pos(model, x, y)
    # if odj_id is not None:
    #     model.state.objs[odj_id].gripped = True

    # # I should not need to "notify" via the model
    #model._notify_views("update_objs", model.get_obj_dict())


@socketio.on("dynamatt_mousemove")
def on_mousemovement(event):
    # looks like we need a "mouse"-gripper b.c. everything expects a gripper instance
    model = room_manager.get_models_of_client(request.sid)[0]
    x, y = translate(event["offset_x"], event["offset_y"], event["block_size"])
    print(x, y)

    #TODO: do something with the coordinates of the mouse (e.g. move a mouse cursor 
    # not implemented yet)
    # PROBLEM: 
    #   1) if mouse movements are too quick the server will miss some positions
    #      so that jumps (from (3, 4) to (3, 6)) are possible. 
    #   2) if an object (obj_d) is being dragged over another one (obj_b),
    #      the grid will initially prevent the block to be moved, if an empty
    #      space is however found behind the blocking object (obj_b),
    #      the system will see no problem in placing obj_d at the new position
    #      jumping over obj_b.
    #
    # a solution would be to implement BFS to find the shortest path from the
    # old position of the mouse to the new one and have the golmi apply every single
    # movement in the path individually, this would solve problem 1
    # problem 2 would still persist but instead of jumps we would have weired
    # object circumnavigations, maybe limiting the length of the path to 3 or 4 steps
    # could be an acceptable solution that still allow quick mouse movements that skip
    # one or two cell but still prevent jumps from one area of the grid to another.
    #
    # implementation:
    # import collections
    # def bfs(grid, start, goal, wall, limit):
    #     width = len(grid[0])
    #     height = len(grid)

    #     queue = collections.deque([[start]])
    #     seen = set([start])
    #     while queue:
    #         path = queue.popleft()
    #         x, y = path[-1]
    #         if len(path[1:-1]) > limit:
    #             return []
    #         if (x, y) == goal:
    #             return path[1:-1]
    #         for x2, y2 in ((x+1,y), (x-1,y), (x,y+1), (x,y-1)):
    #             if 0 <= x2 < width and 0 <= y2 < height and grid[y2][x2] != wall and (x2, y2) not in seen:
    #                 queue.append(path + [(x2, y2)])
    #                 seen.add((x2, y2))
    #
    # grid = [[0 for i in range(5)] for j in range(5) ]
    # s = (1, 0)
    # g = (4, 4)
    # print(bfs(grid=grid, start=s, goal=g, wall=1, limit=6))


def translate(x, y, granularity):
    return x // granularity, y // granularity

# not really needed anymore
def get_object_id_at_pos(model, x, y):
    tile = model.object_grid.get_single_tile({"x": x, "y": y})
    # if there is an object on tile, return last object id
    if tile.objects:
        return tile.objects[-1]
    return None
