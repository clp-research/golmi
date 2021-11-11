"""
The Generator is a module for the model. it can generate
random states to initialize a model based on 3 parameters:
    -number of objects
    -number of gripper
    -whether the grippers should be positioned randomly
"""


import random
import math

from model.obj import Obj
from model.state import State
from model.gripper import Gripper


class Generator:
    def __init__(self, model, attempts=100):
        self.model = model
        self.attempts = attempts

    def _generate_grippers(self, n_grippers, random_gr_position):
        grippers = dict()
        while len(grippers) < n_grippers:
            if random_gr_position:
                taken = set()
                x = random.randint(0, self.model.config.width)
                y = random.randint(0, self.model.config.height)

                # check that grippers do not overlap
                if (x, y) not in taken:
                    taken.add((x, y))
                    index = len(grippers)
                    grippers[index] = Gripper(index, x, y)
            else:
                index = len(grippers)
                x = self.model.config.width / 2
                y = self.model.config.height / 2
                grippers[index] = Gripper(index, x, y)

        return grippers

    def _generate_objects(self, n_objs):
        objects = dict()
        attempt = 0
        while len(objects) < n_objs:
            # pick a random type and its height and width
            piece_type = random.choice(
                list(self.model.config.type_config.keys())
            )
            block_matrix = self.model.config.type_config[piece_type]
            height = len(block_matrix)
            width = len(block_matrix[0])

            # generate random coordinates
            x = random.randint(0, self.model.config.width - width)
            y = random.randint(0, self.model.config.height - height)

            # generate random attributes
            color = random.choice(self.model.config.colors)
            rotation = 0
            mirrored = False

            if "rotation" in self.model.config.actions:
                random_rot = random.randint(
                    0, math.floor(360/self.model.config.rotation_step)
                )
                rotation = self.model.config.rotation_step * random_rot

            if "flip" in self.model.config.actions:
                mirrored = bool(random.randint(0, 1))

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
            if self.model.grid.can_move(obj.occupied(), None):
                index = str(len(objects))
                obj.id_n = index
                self.model.grid.add_obj(obj)
                objects[index] = obj
            else:
                if self.model.config.prevent_overlap:
                    attempt += 1
                    if attempt > self.attempts:
                        print(attempt)
                        break

        return objects

    def load_random_state(self, n_objs, n_grippers, random_gr_position=False):
        # get grippers
        grippers = self._generate_grippers(n_grippers, random_gr_position)

        # get objects
        objects = self._generate_objects(n_objs)

        # create state and load it
        state = State()
        state.grippers = grippers
        state.objs = objects
        self.model.set_state(state)
