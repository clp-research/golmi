from model.obj import Obj


class Gripper(Obj):
    def __init__(
            self, id_n, x, y, gripped=None, width=1, height=1, color="blue"):
        # note: "gripped" is polymorphic here.
        # For Obj, it is a Boolean signifying whether the object is gripped.
        # For Gripper, it maps to None or the id of the Obj
        # instance that is currently gripped
        super().__init__(
            id_n, "gripper", x, y, width, height, [[1]],
            rotation=0, mirrored=False, color=color, gripped=gripped
        )

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
