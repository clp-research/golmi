"""
Class to store settings such as board width, allowable actions, etc.
"""

import json


class Config:
    def __init__(
            self, type_config, width=20, height=20,
            snap_to_grid=False, prevent_overlap=True,
            actions=["move", "rotate", "flip", "grip"],
            move_step=0.5, rotation_step=90,
            action_interval=0.1, verbose=False,
            block_on_target=True,
            colors=["red", "orange", "yellow", "green",
                    "blue", "purple", "saddlebrown", "grey"]):
        """
        Constructor.
        @param type_config	    Json file name or dictionary mapping types
                                to 0/1 matrices indicating type shapes.
        @param width 	        Number of vertical 'blocks' on the board
                                e.g. for block-based rendering. default:20
        @param height	        Number of horizontal 'blocks' on the board
                                e.g. for block-based rendering. default:20
        @param snap_to_grid 	True to lock objects to the nearest block at
                                gripper release. default:False
        @param prevent_overlap 	True to prohibit any action that would lead
                                to objects overlapping. default:True
        @param actions 	        Array of strings naming allowed object
                                manipulations.
                                Default: ['move', 'rotate', "flip", "grip"]
        @param move_step	    Step size for object movement.
                                Default: 0.5 [blocks]
        @param rotation_step	Applied angle when object is rotated. Limitations
                                might exist for View implementations.
                                Default: 90
        @param action_interval	Frequency of repeating looped actions in seconds
                                Default: 0.1
        @param verbose          True to print additional (debug-) information
                                after model changes, such as the object grid.
        @param block_on_target  True to lock objects once they align on the
                                grid with a matching target object.
        @param colors           Available object colors, can be color names
                                or html color codes.
                                Default: ["red", "orange", "yellow", "green",
                                "blue", "purple", "saddlebrown", "grey"]
        """
        # make sure type_config can be parseds
        if isinstance(type_config, str):
            self.type_config = Config.types_from_json(type_config)
        elif isinstance(type_config, dict):
            self.type_config = type_config
        else:
            raise ValueError("type_config must be a json file name or dict")
        # make sure step size is allowed
        valid_step = Config.is_valid_move_step(move_step)
        if not valid_step:
            raise ValueError(
                f"Selected step size of {move_step} is not allowed\n"
                "Please select a step size that satisfies the following "
                "condition: (1/(step size % 1)) must be an integer"
            )
        self.width = width
        self.height = height
        self.snap_to_grid = snap_to_grid
        self.prevent_overlap = prevent_overlap
        self.actions = actions
        self.move_step = move_step
        self.rotation_step = rotation_step
        self.action_interval = action_interval
        self.verbose = verbose
        self.block_on_target = block_on_target
        self.colors = colors

    def __repr__(self):
        properties = ", ".join(vars(self).keys())
        return f"Config({properties})"

    @staticmethod
    def is_valid_move_step(move_step):
        """
        Method to evaluate if the move step is allowed
        move steps must:
            - be higher than 0
            - evenly divide the interval between 0 and 1
              (ex. 0.25, 0.5, 0.1 etc...)
        """
        # move step cannot be negative
        if move_step <= 0:
            return False

        # if move_step is a float it must divide
        # the interval between 0 and 1 evenly
        if isinstance(move_step, float):
            if not (1/(move_step % 1)).is_integer():
                return False
        return True

    def get_types(self):
        return self.type_config.keys()

    @staticmethod
    def types_from_json(filename):
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
        return Config.remove_json_comments(types)

    @staticmethod
    def from_json(filename):
        """
        @param filename String, name of a json file describing a Config.
            The key "type_config" mapping to a dictionary is mandatory.
        @return new Config instance with the given attributes
        """
        with open(filename, mode="r") as file:
            json_data = json.loads(file.read())
        return Config.from_dict(json_data)

    @staticmethod
    def from_dict(source_dict):
        """
        @param source_dict  Dictionary containing Config constructor
                            parameters. The key "type_config" mapping to a
                            dictionary is mandatory.
        @return new Config instance with the given attributes
        """
        if not isinstance(source_dict, dict):
            raise TypeError("source_dict must be of type dict")
        # check for mandatory parameter type_config
        if source_dict.get("type_config") is None or \
                not isinstance(source_dict["type_config"], dict):
            raise ValueError(
                "source_dict must contain key 'type_config' mapping to a dict"
            )
        types = Config.remove_json_comments(source_dict["type_config"])
        new_config = Config(types)
        # overwrite any setting given in the data, leave the rest as default
        # new keys are also allowed
        for attr_key, attr_value in source_dict.items():
            if attr_key != "type_config":
                setattr(new_config, attr_key, attr_value)
        return new_config

    def to_dict(self):
        """
        Constructs a dictionary from this instance.
        """
        return {
            "width": self.width,
            "height": self.height,
            "snap_to_grid": self.snap_to_grid,
            "prevent_overlap": self.prevent_overlap,
            "actions": self.actions,
            "move_step": self.move_step,
            "rotation_step": self.rotation_step,
            "action_interval": self.action_interval,
            "verbose": self.verbose,
            "block_on_target": self.block_on_target,
            "colors": self.colors,
            "type_config": self.type_config
        }

    @staticmethod
    def remove_json_comments(parsed_json):
        return {
            key: value for key, value in parsed_json.items()
            if not key.startswith("_")
        }