"""
Class to store settings such as board width, allowable actions, etc.
"""

import json


class Config:
    def __init__(
            self, type_config, width=20, height=20,
            snap_to_grid=False, prevent_overlap=True,
            actions=["move", "rotate", "flip", "grip"],
            move_step=0.5, rotation_step=90, action_interval=0.5):
        """
        Constructor.
        @param type_config	    json file or object mapping types
                                to 0/1 matrices indicating type shapes
        @param width 	        number of vertical 'blocks' on the board
                                e.g. for block-based rendering. default:20
        @param height	        number of horizontal 'blocks' on the board
                                e.g. for block-based rendering. default:20
        @param snap_to_grid 	True to lock objects to the nearest block at
                                gripper release. default:False
        @param prevent_overlap 	True to prohibit any action that would lead
                                to objects overlapping. default:True
        @param actions 	        array of strings naming allowed object
                                manipulations. default:['move', 'rotate']
        @param move_step	    step size for object movement. default:0.2[blocks]
        @param rotation_step	applied angle when object is rotated. Limitations
                                might exist for View implementations.
                                default:90
        @param action_interval	frequency of repeating looped actions in seconds
                                default: 0.5
        """
        # make sure step size is allowed
        if not (1/move_step).is_integer():
            raise ValueError(
                f"Selected step size of {move_step} is not allowed\n"
                "Please select a step size that satisfies the following "
                "condition: (1/step size) must be an integer"
            )
        self.width = width
        self.height = height
        self.snap_to_grid = snap_to_grid
        self.prevent_overlap = prevent_overlap
        self.actions = actions
        self.move_step = move_step
        self.rotation_step = rotation_step
        self.action_interval = action_interval

        if type(type_config) == str:
            self.type_config = self._types_from_JSON(type_config)
        else:
            self.type_config = type_config

        self.colors = [
            "red",
            "orange",
            "yellow",
            "green",
            "blue",
            "purple",
            "saddlebrown",
            "grey"
        ]

    def __repr__(self):
        properties = ", ".join(vars(self).keys())
        return f"Config({properties})"

    def get_types(self):
        return self.type_config.keys()

    def _types_from_JSON(self, filename):
        """
        Parses a JSON file containing type matrices.
        The file should map each supported object type
        to a grid filled with 0s and 1s,
        where a 1 signifies the presence of a block and
        a 0 signifies the absence.
        @param filename 	path to json file
        """
        with open(filename, "r", encoding="utf-8") as infile:
            types = json.load(infile)

        # Ignore keys with underscores (used for comments)
        return {
            key: value for key, value in types.items()
            if not key.startswith("_")
        }

    def to_dict(self):
        """
        Constructs a dictionary from this instance.
        """
        return {
            "width": self.width,
            "height": self.height,
            "actions": self.actions,
            "rotation_step": self.rotation_step,
            "type_config": self.type_config,
            "colors": self.colors
        }
