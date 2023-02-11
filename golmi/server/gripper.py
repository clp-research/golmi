from golmi.server.obj import Obj


class Gripper(Obj):
    def __init__(
            self, id_n, x, y, gripped=None, color="blue"):
        # note: "gripped" is polymorphic here.
        # For Obj, it is a Boolean signifying whether the object is gripped.
        # For Gripper, it maps to None or the id of the Obj
        # instance that is currently gripped
        super().__init__(
            id_n, "gripper", x, y, [[1]],
            rotation=0, mirrored=False, color=color, gripped=gripped
        )

    @classmethod
    def from_dict(cls, id_n, source_dict):
        """
        Construct a new Gripper instance from a dictionary, e.g., parsed json.
        @param id_n identifier for the gripper
        @param source_dict  dict containing object attributes, keys "x"
                            and "y" are mandatory
        @param type_config  dict mapping type names to block matrices
        @return new Gripper instance with the given attributes
        """
        mandatory_key = {"x", "y"}
        if any(source_dict.get(key) is None for key in mandatory_key):
            raise KeyError(
                f"Gripper construction failed, key {mandatory_key} missing"
            )

        new_gripper = cls(
            id_n,
            float(source_dict["x"]),
            float(source_dict["y"])
        )

        # process optional info
        if "gripped" in source_dict:
            # cast object name to str too
            gripped_id = list(source_dict["gripped"].keys())[0]
            # gripped_id = str(source_dict["gripped"])
            new_gripper.gripped = str(gripped_id)

        if "width" in source_dict:
            new_gripper.width = source_dict["width"]
        if "height" in source_dict:
            new_gripper.height = source_dict["height"]
        if "color" in source_dict:
            new_gripper.color = source_dict["color"]
        return new_gripper

    def to_dict(self):
        """
        Constructs a JSON-friendly dictionary representation of this instance.
        @return dictionary containing all important properties
        """
        return {
            "id_n": self.id_n,
            "x": self.x,
            "y": self.y,
            "color": self.color
        }
