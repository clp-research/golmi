import eventlet
import json

from model.generator import Generator
from model.grid import Grid
from model.gripper import Gripper
from model.obj import Obj
from model.state import State
from model.mover import Mover


class Model:
    def __init__(self, config, socket, room):
        self.socket = socket  # to communicate with subscribed views
        self.room = room
        self.state = State()
        self.config = config
        self.generator = Generator(self)
        self.mover = Mover(self)
        self._generate_grids()

        # Contains a dictionary for each available action. The nested dicts map
        # gripper ids to an eventlet greenthread instance if the respective
        # action is currently running (= repeatedly executed), else to None
        self.running_loops = {action: dict() for action in self.config.actions}

    def _generate_grids(self):
        self.object_grid = Grid(
            self.config.width,
            self.config.height,
            self.config.move_step,
            self.config.prevent_overlap
        )
        self.target_grid = Grid(
            self.config.width,
            self.config.height,
            self.config.move_step,
            self.config.prevent_overlap
        )

    def __repr__(self):
        return f"Model(room: {self.room})"

    # --- getter --- #

    def get_obj_dict(self):
        return self.state.get_obj_dict()

    def get_object_ids(self):
        return self.state.get_object_ids()

    def get_obj_by_id(self, obj_id):
        return self.state.get_obj_by_id(obj_id)

    def get_gripper_dict(self):
        return self.state.get_gripper_dict()

    def get_gripper_ids(self):
        return self.state.get_gripper_ids()

    def get_gripper_by_id(self, gr_id):
        """
        @return Gripper instance or None if id is not registered
        """
        return self.state.get_gripper_by_id(gr_id)

    def get_gripped_obj(self, obj_id):
        return self.state.get_gripped_obj(obj_id)

    def get_gripper_coords(self, gr_id):
        """
        @return list: [x-coordinate, y-coordinate]
        """
        return self.state.get_gripper_coords(gr_id)

    def get_config(self):
        return self.config.to_dict()

    def get_width(self):
        return self.config.width

    def get_height(self):
        return self.config.height

    def get_type_config(self):
        return self.config.type_config

    # --- Communicating with views --- #

    def _notify_views(self, event_name, data):
        """
        Notify all listening views of model events (usually data updates)
        @param event_name 	event type (str), e.g. "update_grippers"
        @param data 	serializable data to send to listeners
        """
        self.socket.emit(event_name, data, room=self.room)

    # --- Set up and configuration --- #

    def set_state(self, state):
        """
        Initialize the model's (game) state.
        @param state	State object or dict or JSON string
        """
        # reset grids
        self.object_grid.clear_grid()
        self.target_grid.clear_grid()

        # state is a JSON string or parsed JSON dictionary
        if isinstance(state, (str, dict)):
            self._state_from_json(state)
        else:
            # state is a State instance
            self.state = state

        # add objects
        for obj in self.state.objs.values():
            self.object_grid.add_obj(obj)

        # add targets
        for target in self.state.targets.values():
            self.target_grid.add_obj(target)

        # update views
        self._notify_views("update_state", self.state.to_dict())

    def set_config(self, config):
        """
        Change the model's configuration. Overwrites any attributes
        passed in config and leaves the rest as before. New keys simply added.
        @param config	Config object or dict or JSON string
        """
        # config is a JSON string or parsed JSON dictionary
        if isinstance(config, (str, dict)):
            self._config_from_json(config)
        else:
            # config is a Config instance
            self.config = config

        # create grids
        self._generate_grids()

        # in case the available actions changed, reset the looped actions
        self.reset_loops()
        self._notify_views("update_config", self.config.to_dict())

    def reset(self):
        """
        Reset the current state.
        """
        self.state = State()
        self.reset_loops()
        self._notify_views("update_state", self.state.to_dict())

    # TODO: make sure pieces are on the board! (at least emit warning)
    def _state_from_json(self, json_data):
        if type(json_data) == str:
            # a JSON string
            json_data = json.loads(json_data)
        # otherwise assume json_data is a dict
        try:
            # initialize an empty state
            self.state = State()
            # construct objects
            if "objs" in json_data and type(json_data["objs"]) == dict:
                for obj_name in json_data["objs"]:
                    obj = str(obj_name)  # use string for consistency
                    type_config = self.get_type_config()

                    if "id_n" not in json_data["objs"][obj]:
                        id_n = obj
                    else:
                        id_n = json_data["objs"][obj]["id_n"]

                    # create object
                    this_obj = Obj(
                        id_n=id_n,
                        obj_type=json_data["objs"][obj]["type"],
                        x=float(json_data["objs"][obj]["x"]),
                        y=float(json_data["objs"][obj]["y"]),
                        width=float(json_data["objs"][obj]["width"]),
                        height=float(json_data["objs"][obj]["height"]),
                        block_matrix=(
                            type_config[json_data["objs"][obj]["type"]]
                        )
                    )
                    self.state.objs[obj] = this_obj
                    # process optional info
                    if "rotation" in json_data["objs"][obj]:
                        # rotate the object
                        self.state.rotate_obj(
                            obj, float(json_data["objs"][obj]["rotation"])
                        )
                    if ("mirrored" in json_data["objs"][obj]
                            and json_data["objs"][obj]["mirrored"]):
                        # flip the object if "mirrored" is true in the JSON
                        self.state.flip_obj(obj)

                    if "color" in json_data["objs"][obj]:
                        color = json_data["objs"][obj]["color"]
                        self.state.objs[obj].color = color

            # construct grippers
            if "grippers" in json_data and type(json_data["grippers"]) == dict:
                for gr_name in json_data["grippers"]:
                    gr = str(gr_name)  # use string for consistency
                    if "id_n" not in json_data["grippers"][gr]:
                        id_n = gr
                    else:
                        id_n = json_data["grippers"][gr]["id_n"]

                    self.state.grippers[gr] = Gripper(
                        gr,
                        float(json_data["grippers"][gr]["x"]),
                        float(json_data["grippers"][gr]["y"])
                    )

                    # process optional info
                    if "gripped" in json_data["grippers"][gr]:
                        # cast object name to str, too
                        gripped_id = str(json_data["grippers"][gr]["gripped"])
                        self.state.grippers[gr].gripped = gripped_id
                        self.state.objs[gripped_id].gripped = True

                    if "width" in json_data["grippers"][gr]:
                        width = json_data["grippers"][gr]["width"]
                        self.state.grippers[gr].width = width

                    elif "height" in json_data["grippers"][gr]:
                        height = json_data["grippers"][gr]["height"]
                        self.state.grippers[gr].height = height

                    elif "color" in json_data["grippers"][gr]:
                        color = json_data["grippers"][gr]["color"]
                        self.state.grippers[gr].color = color

        except KeyError:
            raise KeyError(
                "Error during state initialization: JSON data "
                "does not have the right format.\n"
                "Please refer to the documentation."
            )

    def _config_from_json(self, json_data):
        if isinstance(json_data, str):
            # a JSON string
            json_data = json.loads(json_data)
        # otherwise assume json_data is a dict
        # overwrite any setting given in the data, leave the rest as before.
        # new keys are also allowed
        for attr_key, attr_value in json_data.items():
            setattr(self.config, attr_key, attr_value)

    # --- Gripper manipulation --- #

    def add_gr(self, gr_id):
        """
        Add a new gripper to the internal state.
        The start position is the center. Notifies listeners.
        @param gr_id 	identifier for the new gripper
        """
        start_x = self.get_width()/2
        start_y = self.get_height()/2
        # if a new gripper was created, notify listeners
        if gr_id not in self.state.grippers:
            self.state.grippers[gr_id] = Gripper(gr_id, start_x, start_y)
            self._notify_views("update_grippers", self.get_gripper_dict())

    def remove_gr(self, gr_id):
        """
        Delete a gripper from the internal state and notify listeners.
        @param gr_id 	identifier of the gripper to remove
        """
        if gr_id in self.state.grippers:
            self.state.grippers.pop(gr_id)
            self._notify_views("update_grippers", self.get_gripper_dict())

    def start_gripping(self, gr_id):
        """
        Start calling the function grip periodically until stop_gripping
        is called, essentially repeatedly gripping / ungripping
        with a specified gripper.
        @param gr_id 	gripper id
        """
        self.stop_gripping(gr_id)
        self.start_loop("grip", gr_id, self.grip, gr_id)

    def stop_gripping(self, gr_id):
        """
        Stop periodically gripping.
        @param gr_id 	gripper id
        """
        self.stop_loop("grip", gr_id)

    def grip(self, gr_id):
        """
        Attempt a grip / ungrip.
        @param gr_id 	gripper id
        """
        # if some object is already gripped, ungrip it
        old_gripped = self.get_gripped_obj(gr_id)
        if old_gripped:
            # state takes care of detaching object and gripper
            self.state.ungrip(gr_id)
            # notify view of object and gripper change
            self._notify_views("update_objs", self.get_obj_dict())
            self._notify_views("update_grippers", self.get_gripper_dict())
        else:
            # Check if gripper hovers over some object
            new_gripped = self._get_grippable(gr_id)
            # changes to object and gripper
            if new_gripped is not None:
                self.state.grip(gr_id, new_gripped)

                # notify view of object and gripper change
                self._notify_views("update_objs", self.get_obj_dict())
                self._notify_views("update_grippers", self.get_gripper_dict())

    def start_moving(self, gr_id, x_steps, y_steps, step_size=None):
        """
        Start calling the function move periodically
        until stop_moving is called.
        @param gr_id 	    gripper id
        @param x_steps	    steps to move in x direction.
                            Step size is defined by model configuration
        @param y_steps	    steps to move in y direction.
                            Step size is defined by model configuration
        @param step_size 	Optional, size of step unit in blocks.
                            Default: use move_step of config
        """
        # cancel any ongoing movement
        self.stop_moving(gr_id)
        self.start_loop(
            "move",
            gr_id,
            self.mover.apply_movement,
            "move",
            gr_id,
            x_steps=x_steps,
            y_steps=y_steps,
            step_size=step_size
        )

    def stop_moving(self, gr_id):
        """
        Stop calling move periodically.
        @param gr_id 	gripper id
        """
        self.stop_loop("move", gr_id)

    def start_rotating(self, gr_id, direction, step_size=None):
        """
        Start calling the function rotate periodically
        until stop_rotating is called.
        @param gr_id 	    id of the gripper whose gripped
                            object should be rotated
        @param direction	-1 for leftwards rotation
                            1 for rightwards rotation
        @param step_size	Optional, angle to rotate per step.
                            Default: use rotation_step of config
        """
        # cancel any ongoing rotation
        self.stop_rotating(gr_id)
        self.start_loop(
            "rotate",
            gr_id,
            self.mover.apply_movement,
            "rotate",
            gr_id,
            direction=direction,
            step_size=step_size
        )

    def stop_rotating(self, gr_id):
        """
        Stop calling rotate periodically.
        @param gr_id 	gripper id
        """
        self.stop_loop("rotate", gr_id)

    def start_flipping(self, gr_id):
        """
        Start calling the function flip periodically
        until stop_flipping is called.
        @param gr_id 	id of the gripper whose gripped
                        object should be flipped
        """
        # cancel any ongoing flipping
        self.stop_flipping(gr_id)
        self.start_loop(
            "flip",
            gr_id,
            self.mover.apply_movement,
            "flip",
            gr_id
        )

    def stop_flipping(self, gr_id):
        """
        Stop calling flip periodically.
        @param gr_id 	gripper id
        """
        self.stop_loop("flip", gr_id)

    def _get_grippable(self, gr_id):
        """
        Find an object that is in the range of the gripper.
        @param id 	gripper id
        @return id of object to grip or None
        """
        # Gripper position. It is just a point.
        x, y = self.get_gripper_coords(gr_id)

        tile = self.object_grid.get_single_tile({"x": x, "y": y})
        # if there is an object on tile, return last object
        if tile.objects:
            return tile.objects[-1]
        return None

    # --- Loop functionality ---

    def start_loop(self, action_type, gripper, fn, *args, **kwargs):
        """
        Spawn a greenthread.GreenThread instance that executes
        fn until stop_loop is called.

        @param action_type	str, one of the action types defined by the config
        @param gripper      id of the gripper to perform the action with
        @param fn           function to loop
        """
        assert action_type in self.running_loops, \
            f"Error at Model.start_loop: action {action_type} not registered"
        # create a thread executing the action infinitely

        self.running_loops[action_type][gripper] = eventlet.spawn(
            self._loop, fn, *args, **kwargs
        )

    def _loop(self, fn, *args, **kwargs):
        # rotations and flips can be slow (0.5)
        # movements should be as fast as in config
        if args[0] == "move":
            action_interval = self.config.action_interval
        else:
            action_interval = 0.5

        # start loop
        while True:
            fn(*args, **kwargs)
            eventlet.sleep(action_interval)

    def stop_loop(self, action_type, gripper):
        """
        Stop a running action for a specific gripper.
        """
        assert action_type in self.running_loops, \
            f"Error at Model.stop_loop: action {action_type} not registered"

        if gripper in self.running_loops[action_type] and isinstance(
                self.running_loops[action_type][gripper],
                eventlet.greenthread.GreenThread
                ):
            self.running_loops[action_type][gripper].kill()
            self.running_loops[action_type][gripper] = None

    def reset_loops(self):
        """Stop all running actions."""
        # kill any existing thread
        for action_dict in self.running_loops.values():
            for thread in action_dict.values():
                if isinstance(thread, eventlet.greenthread.GreenThread):
                    thread.kill()
        self.running_loops = {action: dict() for action in self.config.actions}
