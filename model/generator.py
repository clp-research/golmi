"""
The Generator is a module for the model. it can generate
random states to initialize a model based on 3 parameters:
    -number of objects
    -number of gripper
    -whether the grippers should be positioned randomly
"""

import random
import math

from model.grid import Grid
from model.obj import Obj
from model.state import State
from model.gripper import Gripper
from model.config import Config


class CompositionalSceneGenerator:
    """
        Generates a scene, where objects differ on a controlled compositional basis.
        For example, the objects might differ in "color" but not in "shape".

        Note: This implementation is tightly coupled to the properties ["color", "shape", "position"] and Obj
    """

    def __init__(self, config, complexities: dict = None, ambiguities: dict = None):
        """
        :param complexities: dict of ("prop_name",int) with the number of other different values for the unique_props.
        Zero, means all available are used. Defaults to all available properties.
        :param ambiguities: dict of ("prop_name",int) applied, when there is more than 1 unique property.
        Zero, means all other pieces share a property with the piece. Defaults to all shared.
        For "position" it's always 1 (otherwise there might be too many pieces in a corner).
        """
        self.config = config
        self.board_width = config.width
        self.board_height = config.height
        self.prop_names = ["color", "shape", "position"]
        self.complexities = dict([(p, 0) for p in self.prop_names])
        if complexities:  # overwrite defaults
            for k in complexities:
                self.complexities[k] = complexities[k]
        self.ambiguities = dict([(p, 0) for p in self.prop_names])
        if ambiguities:  # overwrite defaults
            for k in ambiguities:
                self.ambiguities[k] = ambiguities[k]
        # For "position" it's always 1 (otherwise there might be too many pieces in a corner).
        self.ambiguities["position"] = 1

    def place_pieces(self, board: Grid, piece: Obj, unique_props: list[str], distractors: list[Obj]):
        ...

    def create_distractors(self, piece: Obj, unique_props: list[str], num_distractors: int = 1):
        if "position" in unique_props:
            unique_props = unique_props.copy()  # we handle position on placement (later)
            unique_props.remove("position")
        all_shapes = list(self.config.type_config.keys())
        all_colors = self.config.colors
        pools = {
            "shape": all_shapes.copy(),
            "color": all_colors.copy()
        }
        # remove uniq props from sampling distribution
        for prop_name in unique_props:
            if len(pools[prop_name]) < 2:
                raise Exception("Cannot discriminate on a property with less than 2 possible values")
            pools[prop_name].remove(self._get_prop_value(piece, prop_name))
            prop_complexity = self.complexities[prop_name]
            if prop_complexity > 0:
                pools[prop_name] = random.sample(pools[prop_name], k=prop_complexity)
        obj_configs = []
        for _ in range(num_distractors):
            obj_config = dict()
            for prop_name in ["shape", "color"]:
                obj_config[prop_name] = random.choice(pools[prop_name])
            obj_configs.append(obj_config)
        # make sure that there is at least one other piece with the piece prop value (so that 2 props are necessary)
        if len(unique_props) == 2:  # this is a quite hard assumption!
            ambiguous_prop = unique_props[0]  # we take in order
            ambiguity = self.ambiguities[ambiguous_prop]
            ambiguous_configs = obj_configs
            if ambiguity > 0:
                ambiguous_configs = random.sample(obj_configs, k=ambiguity)
            for obj_config in ambiguous_configs:
                obj_config[ambiguous_prop] = self._get_prop_value(piece, ambiguous_prop)
        # TODO we need to force that other pieces have the same prop of a kind also when uniq_props == 1
        if len(unique_props) == 1:  # this is a quite hard assumption!
            ...
        distractors = []
        for idx, obj_config in enumerate(obj_configs):
            distractors.append(Obj(idx, obj_config["shape"], x=0, y=0,
                                   color=obj_config["color"],
                                   # 'block_matrix' seems unnecessary here (but is required)!
                                   block_matrix=self.config.type_config[obj_config["shape"]]
                                   ))
        return distractors

    def generate_scene(self, board: Grid, piece: Obj, unique_props: list[str], num_distractors: int = 1):
        """
        :param board: where to establish the scene
        :param piece: based on which the scene will be generated
        :param unique_props: define the props that should uniquely identify the given piece. The order matters,
        because when there is more than one unique property, then the later ones come last. Must be either or
        a combination of ["color", "shape", "position"]
        :param num_distractors: the number of other pieces in the scene
        :return:
        """
        distractors = self.create_distractors(piece, unique_props, num_distractors)
        self.place_pieces(board, piece, unique_props, distractors)
        return board

    def _get_prop_value(self, obj: Obj, prop_name):
        if prop_name == "color":
            return obj.color
        if prop_name == "shape":
            return obj.type
        if prop_name == "position":
            return self._get_pos(obj)
        raise Exception(f"Cannot map {prop_name}. Supported are {self.prop_names}")

    def _get_pos(self, obj):
        pos = ""
        x = obj.x + (obj.width / 2)
        y = obj.y + (obj.height / 2)
        if y < 2 * self.board_height / 5:
            pos = "top"
        elif y >= 3 * self.board_height / 5:
            pos = "bottom"
        if x < 2 * self.board_width / 5:
            pos = pos + " left" if len(pos) > 0 else "left"
        elif x >= 3 * self.board_width / 5:
            pos = pos + " right" if len(pos) > 0 else "right"
        if not pos:
            pos = "center"
        return pos


class Generator:
    def __init__(self, config: Config, attempts: int = 100):
        self.config = config
        self.attempts = attempts

    def _generate_grippers(self, n_grippers, random_gr_position):
        grippers = dict()
        while len(grippers) < n_grippers:
            if random_gr_position:
                taken = set()
                x = random.randint(0, self.config.width)
                y = random.randint(0, self.config.height)

                # check that grippers do not overlap
                if (x, y) not in taken:
                    taken.add((x, y))
                    index = len(grippers)
                    grippers[index] = Gripper(index, x, y)
            else:
                index = len(grippers)
                x = self.config.width / 2
                y = self.config.height / 2
                grippers[index] = Gripper(index, x, y)

        return grippers

    def _restricted_coordinates(self, area):
        """
        given an area restrict the possible spawning positions
        for objects and targets
        """
        possible_positions = {
            "all", "top", "bottom", "left", "right"
        }

        if area not in possible_positions:
            raise ValueError("Spawn position not valid")

        if area == "all":
            x_start = 0
            x_end = self.config.width
            y_start = 0
            y_end = self.config.height

        elif area == "bottom":
            x_start = 0
            x_end = self.config.width
            y_start = self.config.height // 2
            y_end = self.config.height

        elif area == "top":
            x_start = 0
            x_end = self.config.width
            y_start = 0
            y_end = self.config.height // 2

        elif area == "left":
            x_start = 0
            x_end = self.config.width // 2
            y_start = 0
            y_end = self.config.height

        elif area == "right":
            x_start = self.config.width // 2
            x_end = self.config.width
            y_start = 0
            y_end = self.config.height

        else:
            raise Exception("Unknown area: " + area)

        return (x_start, x_end), (y_start, y_end)

    def _generate_target(
            self, target_grid: Grid,
            index, piece_type, width, height, block_matrix, area, color):
        """
        this function generates a target block for the object maintaining:
            - index
            - piece type
            - width
            - height
            - block matrix
        parameters that will be changed:
            - x and y coordinates
            - rotation
            - if flipped
        """
        (x_start, x_end), (y_start, y_end) = self._restricted_coordinates(area)

        while True:
            # generate random coordinates
            x = random.randint(x_start, x_end - width)
            y = random.randint(y_start, y_end - height)

            # randomize rotation and mirrored
            rotation = 0
            mirrored = False
            if "rotate" in self.config.actions:
                # generate random angle for rotation
                random_rot = random.randint(
                    0, math.floor(360 / self.config.rotation_step)
                )
                rotation = self.config.rotation_step * random_rot

                # rotate matrix
                block_matrix = Obj.rotate_block_matrix(block_matrix, rotation)

            if "flip" in self.config.actions:
                mirrored = bool(random.randint(0, 1))
                if mirrored:
                    # flip matrix
                    block_matrix = Obj.flip_block_matrix(block_matrix)

            # create target object
            target_obj = Obj(
                id_n=index,
                obj_type=piece_type,
                x=x,
                y=y,
                block_matrix=block_matrix,
                rotation=rotation,
                mirrored=mirrored,
                color=color
            )

            if target_grid.is_legal_position(
                    target_obj.occupied(), index):
                target_grid.add_obj(target_obj)
                break

        return target_obj

    def _generate_objects(
            self, object_grid: Grid, target_grid: Grid,
            n_objs, area_block, area_target, create_targets):
        objects = dict()
        targets = dict()
        attempt = 0

        (x_start, x_end), (y_start, y_end) = self._restricted_coordinates(
            area_block
        )

        while len(objects) < n_objs:
            # pick a random type and its height and width
            piece_type = random.choice(
                list(self.config.get_types())
            )
            block_matrix = self.config.type_config[piece_type]
            height = len(block_matrix)
            width = len(block_matrix[0])

            # generate random coordinates
            x = random.randint(x_start, x_end - width)
            y = random.randint(y_start, y_end - height)

            # generate random attributes
            color = random.choice(self.config.colors)
            rotation = 0
            mirrored = False

            if "rotate" in self.config.actions:
                random_rot = random.randint(
                    0, math.floor(360 / self.config.rotation_step)
                )
                rotation = self.config.rotation_step * random_rot
                block_matrix = Obj.rotate_block_matrix(block_matrix, rotation)

            if "flip" in self.config.actions:
                mirrored = bool(random.randint(0, 1))
                if mirrored:
                    block_matrix = Obj.flip_block_matrix(block_matrix)

            # generate object
            obj = Obj(
                id_n=None,
                obj_type=piece_type,
                x=x,
                y=y,
                block_matrix=block_matrix,
                rotation=rotation,
                mirrored=mirrored,
                color=color
            )

            # if object does not overlap, add it
            if object_grid.is_legal_position(obj.occupied(), None):
                index = str(len(objects))
                obj.id_n = index
                object_grid.add_obj(obj)

                # create a target
                if create_targets:
                    target_obj = self._generate_target(
                        target_grid,
                        index,
                        piece_type,
                        width, height,
                        block_matrix,
                        area_target,
                        color
                    )

                    targets[index] = target_obj

                objects[index] = obj
                attempt = 0
            else:
                # object overlaps, try again until number of
                # maximum attempts is reached
                if self.config.prevent_overlap:
                    attempt += 1
                    if attempt > self.attempts:
                        break

        return objects, targets

    def _initialize_random_state(
            self, obj_grid, trg_grid, n_objs, n_grippers, area_block="all",
            area_target="all", create_targets=False, random_gr_position=False):
        # get grippers
        grippers = self._generate_grippers(n_grippers, random_gr_position)

        # get objects
        objects, target_objs = self._generate_objects(
            obj_grid, trg_grid, n_objs, area_block, area_target, create_targets
        )

        # create state
        state = State()
        state.grippers = grippers
        state.objs = objects
        state.targets = target_objs

        return state

    def generate_random_state(
            self, n_objs, n_grippers, area_block="all",
            area_target="all", create_targets=False,
            random_gr_position=False):
        # TODO There might be actually:
        #  - BoardGenerator
        #  - ObjGenerator
        #  - ObjPlacer
        object_grid = Grid.create_from_config(self.config)
        target_grid = Grid.create_from_config(self.config)

        # generate random state from parameters
        state = self._initialize_random_state(
            object_grid, target_grid, n_objs, n_grippers, area_block,
            area_target, create_targets, random_gr_position
        )
        # TODO state should include the grids (or the other way around)
        return state, object_grid, target_grid
