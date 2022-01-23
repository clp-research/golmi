import itertools
import math

import numpy as np

from model.obj import Obj


class Tile:
    """
    class representing a tile of a grid, a tile
    knows:
        -its coordinates (x, y)
        -which object(s) on it
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.objects = list()

    def __repr__(self):
        if not self.objects:
            return " "
        return "+"

    def __str__(self):
        return self.__repr__()


class Converter:
    """
    class used to convert integer coordinates x, y
    to float ones given the step size used by the model
    """
    def __init__(self, step):
        self.factor = step
        self.multiplier = max(1, math.floor(1 / step))

    def __call__(self, coordinate):
        if float(self.factor).is_integer():
            yield coordinate
        else:
            x = coordinate["x"]
            y = coordinate["y"]

            possible_x = [x]
            possible_y = [y]

            while len(possible_y) < self.multiplier:
                x += self.factor
                y += self.factor
                possible_x.append(x)
                possible_y.append(y)

            for new_x, new_y in itertools.product(possible_x, possible_y):
                yield {
                    "x": round(new_x, 5) * self.multiplier,
                    "y": round(new_y, 5) * self.multiplier
                }


class Grid:
    """
    a grid is a 2D-Array of Tiles
    """
    def __init__(self, width, height, step, prevent_overlap):
        self.width = width
        self.height = height
        # if move step is an integer, set step to 1 (smallest possible)
        if float(step).is_integer():
            self.step = 1
        else:
            # otherwise reduce it to the 0-1 interval
            self.step = step % 1
        self.prevent_overlap = prevent_overlap
        self.clear_grid()
        self.converter = Converter(self.step)

    @classmethod
    def create_from_config(cls, config):
        return cls(
            config.width,
            config.height,
            config.move_step,
            config.prevent_overlap
        )

    def clear_grid(self):
        """
        generate an empty grid
        """
        self.grid = [
            [Tile(j, i) for j in np.arange(0, self.width, self.step)]
            for i in np.arange(0, self.height, self.step)
        ]

    def __repr__(self):
        rep = ""
        for row in self.grid:
            rep += f"[{' '.join(str(i) for i in row)}]\n"
        return rep

    def __getitem__(self, i):
        """
        grid can be accessed:
            -as a normal 2D-array with int as indeces -> matrix[y][x]
            -by giving a dictionary dict = {"x": x, "y": y}

        expects converted coordinates
        """
        if isinstance(i, (int, float)):
            i = int(i)
            return self.grid[i]

        elif isinstance(i, dict):
            x = int(i["x"])
            y = int(i["y"])
            return self.grid[y][x]

    def __contains__(self, coordinates):
        """
        expects converted coordinates
        """
        x = coordinates["x"]
        y = coordinates["y"]

        width = len(self.grid[0])
        height = len(self.grid)

        if 0 <= x < width and 0 <= y < height:
            return True
        return False

    def get_single_tile(self, position):
        """
        expects non converted coordinates
        """
        x = int(position["x"] * self.converter.multiplier)
        y = int(position["y"] * self.converter.multiplier)

        return self.grid[y][x]

    def gripper_on_grid(self, position):
        x = int(position["x"] * self.converter.multiplier)
        y = int(position["y"] * self.converter.multiplier)

        return {"x": x, "y": y} in self

    def add_obj(self, obj):  # change to coordinates
        """
        expects non converted coordinates
        """
        for cell in obj.occupied():
            for new_cell in self.converter(cell):
                self[new_cell].objects.append(obj)

    def remove_obj(self, obj):  # change to coordinates
        """
        expects non converted coordinates
        """
        for cell in obj.occupied():
            for new_cell in self.converter(cell):
                self[new_cell].objects.remove(obj)

    def is_legal_position(self, coordinates, obj):
        """
        expects non converted coordinates
        --------------------------------------------
        checks if the passed coordinates are a valid
        position for the passed item
        """
        for cell in coordinates:
            for new_cell in self.converter(cell):
                # cell must be on grid
                if new_cell not in self:
                    return False

                if self.prevent_overlap is True:
                    # return false if cell is occupied by
                    # another object
                    if (len(self[new_cell].objects) > 0 and
                            self[new_cell].objects[0] != obj):
                        return False
        return True
