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
                block_matrix = State.rotate_block_matrix(block_matrix, rotation)

            if "flip" in self.config.actions:
                mirrored = bool(random.randint(0, 1))
                if mirrored:
                    # flip matrix
                    block_matrix = State.flip_block_matrix(block_matrix)

            # create target object
            target_obj = Obj(
                id_n=index,
                obj_type=piece_type,
                x=x,
                y=y,
                width=width,
                height=height,
                block_matrix=block_matrix,
                rotation=rotation,
                mirrored=mirrored,
                color=color,
                is_target=True
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
                list(self.config.type_config.keys())
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
                block_matrix = State.rotate_block_matrix(block_matrix, rotation)

            if "flip" in self.config.actions:
                mirrored = bool(random.randint(0, 1))
                if mirrored:
                    block_matrix = State.flip_block_matrix(block_matrix)

            # generate object
            obj = Obj(
                id_n=None,
                obj_type=piece_type,
                x=x,
                y=y,
                width=width,
                height=height,
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

    def generate_random_state(
            self, n_objs, n_grippers, area_block="all",
            area_target="all", create_targets=False,
            random_gr_position=False):
        # TODO There might be actually: BoardGenerator, ObjGenerator and ObjPlacer
        object_grid = Grid.create_from_config(self.config)
        target_grid = Grid.create_from_config(self.config)
        state = self._generate_random_state(object_grid, target_grid,
                                            n_objs, n_grippers, area_block,
                                            area_target, create_targets,
                                            random_gr_position)
        # TODO state should include the grids (or the other way around)
        return state, object_grid, target_grid

    def _generate_random_state(self, obj_grid: Grid, trg_grid: Grid,
                               n_objs, n_grippers, area_block="all",
                               area_target="all", create_targets=False,
                               random_gr_position=False):
        # get grippers
        grippers = self._generate_grippers(n_grippers, random_gr_position)

        # get objects
        objects, target_objs = self._generate_objects(obj_grid, trg_grid,
                                                      n_objs, area_block,
                                                      area_target, create_targets)

        # create state
        state = State()
        state.grippers = grippers
        state.objs = objects
        state.targets = target_objs

        return state
