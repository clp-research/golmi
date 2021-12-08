import json

from model.obj import Obj
from model.gripper import Gripper


class State:
    def __init__(self):
        self.objs = dict()  # maps ids to Objs
        self.grippers = dict()
        self.targets = dict()

    def get_obj_dict(self):
        """
        @return Dictionary mapping object ids to object dictionaries
        """
        return {obj_id: obj.to_dict() for obj_id, obj in self.objs.items()}

    def get_target_dict(self):
        """
        @return Dictionary mapping object ids to object dictionaries
        """
        return {obj_id: obj.to_dict() for obj_id, obj in self.targets.items()}

    def get_object_ids(self):
        return self.objs.keys()

    def get_obj_by_id(self, obj_id):
        if obj_id in self.objs:
            return self.objs[obj_id]
        else:
            return None

    def get_gripper_dict(self):
        """
        In contrast to get_obj_dict, each gripper dict has
        the entry "gripped", which itself is None or a
        dictionary mapping the gripped object to an object dictionary.
        @return Dictionary mapping gripper ids to gripper dictionaries.
        """
        gr_dict = dict()
        for gr_id, gr in self.grippers.items():
            gr_dict[gr_id] = gr.to_dict()
            # if some object is gripped, add all the info on that object too
            if gr.gripped:
                gr_dict[gr_id]["gripped"] = {
                    gr.gripped: self.get_obj_by_id(gr.gripped).to_dict()
                }
            else:
                gr_dict[gr_id]["gripped"] = None
        return gr_dict

    def get_gripper_ids(self):
        return self.grippers.keys()

    def get_gripper_by_id(self, gr_id):
        if gr_id in self.grippers:
            return self.grippers[gr_id]
        else:
            return None

    def get_gripper_coords(self, gr_id):
        """
        @param gr_id 	gripper id
        """
        if gr_id in self.grippers:
            return [self.grippers[gr_id].x, self.grippers[gr_id].y]
        else:
            return list()

    def get_gripped_obj(self, gr_id):
        """
        @param gr_id 	gripper id
        @return None or the id of the gripped object
        """
        if gr_id in self.grippers:
            return self.grippers[gr_id].gripped
        else:
            return None

    def move_gr(self, gr_id, dx, dy):
        """
        Change gripper position by moving in direction (dx, dy).
        @param gr_id 	id of the gripper to move
        @param dx 	x direction
        @param dy 	y direction
        """
        self.grippers[gr_id].x += dx
        self.grippers[gr_id].y += dy

    def move_obj(self, obj_id, dx, dy):
        """
         Change an object's position by moving in direction (dx, dy).
         @param obj_id 	object id
         @param dx 	x direction
         @param dy 	y direction
        """
        self.get_obj_by_id(obj_id).x += dx
        self.get_obj_by_id(obj_id).y += dy

    def rotate_obj(self, obj_id, d_angle):
        """
        Change an object's goal_rotation by d_angle.
        @param obj_id  	object id
        @param d_angle	current angle is changed by d_angle
        """
        if d_angle != 0:
            obj = self.get_obj_by_id(obj_id)
            obj.rotate(d_angle)

    def flip_obj(self, obj_id):
        """
        Mirror an object.
        @param obj_id 	object_id
        """
        # change 'mirrored' attribute
        obj = self.get_obj_by_id(obj_id)
        obj.flip()

    def grip(self, gr_id, obj_id):
        """
        Attach a given object to the gripper.
        @param gr_id 	id of the gripper that grips obj_id
        @param obj_id 	id of object to grip, must be in objects
         """
        self.objs[obj_id].gripped = True
        self.grippers[gr_id].gripped = obj_id

    def ungrip(self, gr_id):
        """
        Detach the currently gripped object from the gripper.
        @param gr_id 	id of the gripper that ungrips
        """
        self.objs[self.grippers[gr_id].gripped].gripped = False
        self.grippers[gr_id].gripped = None

    @classmethod
    def from_json(cls, filename, type_config):
        """
        @param filename String, name of a json file describing a State.
                        The key "type_config" mapping to a dict is mandatory.
        @param type_config  dict mapping type names to block matrices
        @return new State instance with the given attributes
        """
        with open(filename, mode="r") as file:
            json_data = json.loads(file.read())
        return cls.from_dict(json_data, type_config)

    @classmethod
    # TODO: make sure pieces are on the board! (at least emit warning)
    def from_dict(cls, source_dict, type_config):
        """
        @param source_dict  Dict containing State constructor parameters.
                            The keys "objs" and "grippers" are mandatory.
                            Refer to the documentation for additional format
                            instructions.
        @param type_config  dict mapping type names to block matrices
        @return new State instance with the given attributes
        """
        if not isinstance(source_dict.get("objs"), dict) or \
                not isinstance(source_dict.get("grippers"), dict):
            raise ValueError(
                "source_dict must contain the keys 'objs' and 'grippers' "
                "mapping to dictionaries."
            )
        # initialize an empty state
        new_state = cls()
        try:
            # construct objects
            for obj_name, obj_dict in source_dict["objs"].items():
                # get identifier or use object key (use str for consistency)
                id_n = obj_dict.get("id_n") or str(obj_name)

                new_object = Obj.from_dict(id_n, obj_dict, type_config)
                new_state.objs[id_n] = new_object

            # construct grippers
            for gr_name, gr_dict in source_dict["grippers"].items():
                # get identifier or use gripper key (use str for consistency)
                id_n = gr_dict.get("id_n") or str(gr_name)
                new_gr = Gripper.from_dict(id_n, gr_dict)
                new_state.grippers[id_n] = new_gr

                # Not the nicest solution: Make sure any gripped object has
                # its 'gripped' attribute set to True
                if new_gr.gripped is not None:
                    new_state.objs[new_gr.gripped].gripped = True

        except KeyError:
            raise KeyError(
                "Error during state initialization: JSON data "
                "does not have the right format.\n"
                "Please refer to the documentation."
            )
        return new_state

    def to_dict(self):
        """
        Create a JSON-friendly representation of the current state
        @return dict containing current grippers and objects
        """
        state_dict = dict()
        state_dict["grippers"] = self.get_gripper_dict()
        state_dict["objs"] = self.get_obj_dict()
        state_dict["targets"] = self.get_target_dict()
        return state_dict
