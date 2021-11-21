import itertools
import math

import numpy as np

from model.obj import Obj


class Tile:
    """
    class representing a tile of a grid, a tile
    knows:
        -its coordinates (x, y)
        -if it's free
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
        if self.factor == 1:
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
                yield {"x": round(new_x, 5), "y": round(new_y, 5)}


class Grid:
    """
    a grid is a 2D-Array of Tiles
    """
    def __init__(self, width, height, step, prevent_overlap):
        self.width = width
        self.heigth = height
        self.step = step
        self.prevent_overlap = prevent_overlap
        self.clear_grid()
        self.converter = Converter(step)

    def clear_grid(self):
        """
        generate an empty grid
        """
        step = min(1, self.step)

        self.grid = [
            [Tile(j, i) for j in np.arange(0, self.width, step)]
            for i in np.arange(0, self.heigth, step)
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
        """
        if isinstance(i, int) or isinstance(i, float):
            i = int(i * self.converter.multiplier)
            return self.grid[i]

        elif isinstance(i, dict):
            x = int(i["x"] * self.converter.multiplier)
            y = int(i["y"] * self.converter.multiplier)
            return self.grid[y][x]

    def __contains__(self, coordinates):
        """
        expected coordinates should be already onverted
        """
        x = coordinates["x"]
        y = coordinates["y"]

        if 0 <= x < self.width and 0 <= y < self.heigth:
            return True
        return False

    def add_obj(self, obj):  # change to coordinates
        for cell in obj.occupied():
            for new_cell in self.converter(cell):
                self[new_cell].objects.append(obj.id_n)

    def remove_obj(self, obj):  # change to coordinates
        for cell in obj.occupied():
            for new_cell in self.converter(cell):
                self[new_cell].objects.remove(obj.id_n)

    def can_move(self, coordinates, id_n):
        for cell in coordinates:
            for new_cell in self.converter(cell):
                # cell must be on grid
                if new_cell not in self:
                    return False

                if self.prevent_overlap is True:
                    # return false if cell is occupied by
                    # another object
                    if (len(self[new_cell].objects) > 0 and
                            self[new_cell].objects != [id_n]):
                        return False
        return True


if __name__ == "__main__":
    g = Grid(width=5, height=5, step=0.5, prevent_overlap=True)
    o1 = Obj(1, "L", 0, 0, 5, 5, block_matrix=[
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [1, 1, 1, 1, 1],
            [0, 0, 0, 0, 1],
            [0, 0, 0, 0, 0]
            ])

    o2 = Obj(2, "L", 3, 3, 5, 5, block_matrix=[
            [0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0]
            ])

    g.add_obj(o1)
    g.add_obj(o2)
    print(g)
    new_c = o1.occupied(o1.x, o1.y + 1)
    print(g.can_move(new_c, 1))