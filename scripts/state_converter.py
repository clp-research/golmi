"""
this script will convert states from the old format to the new
one based on sparse grid representation.
Each state must also contain the entry 'grid_config' with a
valid grid configuration dictionary, example:

"grid_config": {
    "width": 25.0,
    "height": 25.0,
    "move_step": 0.5,
    "prevent_overlap": true
}

this script will take as input a text file where each line is
a state in json format and will print the converted state.

$ python state_converter.py < old_states.jsonl > new_states.jsonl
"""

from io import TextIOWrapper
import json
import sys

# run either from root dir or from /scripts/
sys.path.append("../golmi")
sys.path.append("golmi")

from golmi.server.state import State, Obj, GridConfig, Gripper


class StateConverter(State):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    # TODO: make sure pieces are on the board! (at least emit warning)
    def from_dict(cls, source_dict, type_config=None, grid_config=None):
        """
        @param source_dict  Dict containing State constructor parameters.
                            The keys "objs" and "grippers" are mandatory.
                            Refer to the documentation for additional format
                            instructions.
        @param type_config  dict mapping type names to block matrices
        @param grid_config dict to initialize the grids
        @return new State instance with the given attributes
        """
        if not isinstance(source_dict.get("objs"), dict) or \
                not isinstance(source_dict.get("grippers"), dict):
            raise ValueError(
                "source_dict must contain the keys 'objs' and 'grippers' "
                "mapping to dictionaries."
            )

        gc = None
        if grid_config:
            gc = grid_config
        if "grid_config" in source_dict:
            gc = GridConfig.from_dict(source_dict["grid_config"])
        if not gc:
            raise Exception(
                "Either provide grid_config as a value in "
                "'source_dict' or to 'from_dict' directly"
            )

        try:
            # construct objects
            objs = dict()
            for obj_name, obj_dict in source_dict["objs"].items():
                # get identifier or use object key (use str for consistency)
                id_n = obj_dict.get("id_n") or str(obj_name)

                new_object = Obj.from_dict(
                    id_n, obj_dict, type_config
                )
                objs[id_n] = new_object

            # construct grippers
            grippers = dict()
            for gr_name, gr_dict in source_dict["grippers"].items():
                # get identifier or use gripper key (use str for consistency)
                id_n = gr_dict.get("id_n") or str(gr_name)
                new_gr = Gripper.from_dict(id_n, gr_dict)
                grippers[id_n] = new_gr

                # Not the nicest solution: Make sure any gripped object has
                # its 'gripped' attribute set to True
                if new_gr.gripped is not None:
                    objs[new_gr.gripped].gripped = True

            # construct targets
            targets = dict()
            if "targets" in source_dict:
                for obj_name, obj_dict in source_dict["targets"].items():
                    # get identifier or use object key
                    # (use str for consistency)
                    id_n = obj_dict.get("id_n") or str(obj_name)

                    new_object = Obj.from_dict(
                        id_n, obj_dict, type_config
                    )
                    targets[id_n] = new_object

        except KeyError:
            raise KeyError(
                "Error during state initialization: JSON data "
                "does not have the right format.\n"
                "Please refer to the documentation."
            )

        state_id = source_dict.get("state_id")
        global_id = source_dict.get("global_id")

        return cls(objs, grippers, targets, gc, state_id, global_id)


def main():
    input_stream = TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
    for line in input_stream:
        state = StateConverter.from_dict(
            json.loads(line)
        )

        print(
            json.dumps(
                state.to_dict(include_grid_config=True)
            )
        )


if __name__ == "__main__":
    main()
