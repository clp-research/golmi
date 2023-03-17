from socket import SocketIO

import eventlet
import math

from golmi.server.generator import Generator
from golmi.server.config import Config
from golmi.server.grid import Grid
from golmi.server.gripper import Gripper
from golmi.server.state import State
from golmi.server.mover import Mover


class Model:
    def __init__(self, config, sio: SocketIO = None, room_id: int = None):
        self.sio = sio  # to communicate with subscribed views
        self.room_id = room_id
        self.state = State.empty_state(config)
        self.config = config
        self.mover = Mover()

        # Contains a dictionary for each available action. The nested dicts map
        # gripper ids to an eventlet greenthread instance if the respective
        # action is currently running (= repeatedly executed), else to None
        self.running_loops = {action: dict() for action in self.config.actions}

    def __repr__(self):
        return f"Model(room: {self.room_id})"

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

    def get_gripped_obj(self, gr_id):
        return self.state.get_gripped_obj(gr_id)

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
        if self.sio is not None:
            self.sio.emit(event_name, data, room=self.room_id)

    # --- Set up and configuration --- #

    def set_random_state(self, n_objs, n_grippers, obj_area="all",
                         target_area="all", random_gr_position=False):
        # we could possibly hold a generator instance as well
        generator = Generator(self.config)

        # generate state and grids
        new_state = generator.generate_random_state(
             n_objs, n_grippers, obj_area, target_area, random_gr_position)

        self.set_state(new_state)

    def set_state(self, state):
        """
        Initialize the model's (game) state.
        @param state	json file name or dict (e.g., parsed json)
                        or State instance
        """
        if isinstance(state, str):
            self.state = State.from_json(
                state, self.get_type_config(), self.config
            )
        elif isinstance(state, dict):
            if isinstance(state["objs"], list):
                self.state = State.from_array_dict(
                    state, self.get_type_config(), self.config
                )
            else:
                self.state = State.from_dict(
                    state, self.get_type_config(), self.config
                )
        elif isinstance(state, State):
            self.state = state
            # replot objects and targets, just to be sure
            self.state.plot_objects_targets()
        else:
            raise TypeError("Parameter state must be a json file name, "
                            "dict, or State instance.")

        # update views
        self._notify_views("update_state", self.state.to_array_state())

    def set_config(self, config):
        """
        Change the model's configuration. Overwrites any attributes
        passed in config and leaves the rest as before. New keys simply added.
        @param config	json file name or dict (e.g., parsed json)
                        or Config instance
        """
        # config is a JSON string or parsed JSON dictionary
        if isinstance(config, str):
            self.config = Config.from_json(config)
        elif isinstance(config, dict):
            self.config = Config.from_dict(config)
        elif isinstance(config, Config):
            self.config = config
        else:
            raise TypeError("Parameter config must be a json file name, "
                            "dict, or Config instance")

        # create grids
        self.object_grid = Grid.create_from_config(self.config)
        self.target_grid = Grid.create_from_config(self.config)

        # in case the available actions changed, reset the looped actions
        self.reset_loops()
        self._notify_views("update_config", self.config.to_dict())

    def reset(self):
        """
        Reset the current state.
        """
        self.state = State.empty_state(self.config)
        self.reset_loops()
        self._notify_views("update_state", self.state.to_array_state())

    # --- Gripper manipulation --- #
    def add_gr(self, gr_id, start_x: int = None, start_y: int = None):
        """
        Add a new gripper to the internal state.
        The start position is the center. Notifies listeners.
        @param gr_id 	identifier for the new gripper
        @param start_x  starting x coord
        @param start_y  starting y coord
        """
        if start_x is None:
            start_x = self.get_width()/2
        if start_y is None:
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

    def can_ungrip(self, obj_id):
        """
        This function decides wether a block can be ungripped
        if snap_to_grid is on and the object lies between
        lines (coordinates are float), it will automatically
        try to find a free spot and place the object there
        """
        # without snap to grid a gripper can always ungrip
        if self.config.snap_to_grid is False:
            return True

        obj = self.state.get_obj_by_id(obj_id)

        # integer positions are always plotted on the grid
        if float(obj.x).is_integer() and float(obj.y).is_integer():
            return True
        else:
            # x or y not on grid
            possible_positions = [
                (math.ceil(obj.x), math.ceil(obj.y)),
                (math.ceil(obj.x), math.floor(obj.y)),
                (math.floor(obj.x), math.ceil(obj.y)),
                (math.floor(obj.x), math.floor(obj.y))
            ]

            for new_x, new_y in possible_positions:
                occupied = obj.occupied(new_x, new_y)
                if self.mover._is_legal_move(
                        occupied,
                        obj,
                        self.state,
                        self.config):
                    # move object

                    # 1 - remove obj from state
                    self.state.remove_object(obj)

                    # 2 - change x and y in object
                    obj.x = new_x
                    obj.y = new_y

                    # 3 - add object to state
                    self.state.add_object(obj)
                    return True

            # if no nearby position if free, cannot place it
            return False

    def grip(self, gr_id):
        """
        Attempt a grip / ungrip.
        @param gr_id 	gripper id
        """
        # if some object is already gripped, ungrip it
        old_gripped = self.get_gripped_obj(gr_id)
        if old_gripped:
            allowed = self.can_ungrip(old_gripped)
            if allowed:
                # state takes care of detaching object and gripper
                self.state.ungrip(gr_id)
                # notify view of object and gripper change
                self._notify_views("update_objs", self.state.object_grid.to_list())
                self._notify_views("update_grippers", self.get_gripper_dict())
        else:
            # Check if gripper hovers over some object
            new_gripped = self._get_grippable(gr_id)
            # changes to object and gripper
            if new_gripped is not None:
                self.state.grip(gr_id, new_gripped)

                # notify view of object and gripper change
                self._notify_views("update_objs", self.state.object_grid.to_list())
                self._notify_views("update_grippers", self.get_gripper_dict())

    def start_moving(self, gr_id, x_steps, y_steps):
        """
        Start calling the function move periodically
        until stop_moving is called.
        @param gr_id 	    gripper id
        @param x_steps	    steps to move in x direction.
                            Step size is defined by model configuration
        @param y_steps	    steps to move in y direction.
                            Step size is defined by model configuration
        """
        # cancel any ongoing movement
        self.stop_moving(gr_id)
        self.start_loop(
            "move",
            gr_id,
            self.mover.apply_movement,
            self,
            "move",
            gr_id,
            x_steps=x_steps,
            y_steps=y_steps
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
            self,
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
            self,
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

        tile = self.state.get_tile(x, y)
        # if there is an object on tile, return last object
        if tile.objects:
            return tile.objects[-1].id_n
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
        if args[1] == "move":
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
