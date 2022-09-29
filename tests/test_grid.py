import unittest

from golmi.server.obj import Obj
from golmi.server.grid import Grid


class Test(unittest.TestCase):
    """
    Tests on Grid
    """
    def test_prevent_overlap(self):
        g = Grid(width=5, height=5, step=0.5, prevent_overlap=True)
        o1 = Obj(
            1, "L", 0, 0, 5, 5,
            block_matrix=[
                [0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0],
                [1, 1, 1, 1, 1],
                [0, 0, 0, 0, 1],
                [0, 0, 0, 0, 0]
            ]
        )

        o2 = Obj(
            2, "L", 0, 0, 5, 5,
            block_matrix=[
                [0, 0, 0, 0, 0],
                [0, 1, 0, 0, 0],
                [0, 1, 0, 0, 0],
                [0, 1, 0, 0, 0],
                [0, 1, 1, 1, 1]
            ]
        )

        # add objects
        g.add_obj(o1)

        # objects overlap, object 2 cannot be placed
        new_c = o2.occupied(o1.x, o1.y)
        self.assertFalse(g.is_legal_position(new_c, 2))

    def test_allow_overlap(self):
        g = Grid(width=5, height=5, step=0.5, prevent_overlap=False)
        o1 = Obj(
            1, "L", 0, 0, 5, 5,
            block_matrix=[
                [0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0],
                [1, 1, 1, 1, 1],
                [0, 0, 0, 0, 1],
                [0, 0, 0, 0, 0]
            ]
        )

        o2 = Obj(
            2, "L", 0, 0, 5, 5,
            block_matrix=[
                [0, 0, 0, 0, 0],
                [0, 1, 0, 0, 0],
                [0, 1, 0, 0, 0],
                [0, 1, 0, 0, 0],
                [0, 1, 1, 1, 1]
            ]
        )

        # add objects
        g.add_obj(o1)

        # objects overlap, object 2 can be placed
        new_c = o2.occupied(o1.x, o1.y)
        self.assertTrue(g.is_legal_position(new_c, 2))

    def test_add_object(self):
        g = Grid(width=5, height=5, step=0.5, prevent_overlap=False)
        o1 = Obj(
            1, "L", 0, 0, 5, 5,
            block_matrix=[
                [0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0],
                [1, 1, 1, 1, 1],
                [0, 0, 0, 0, 1],
                [0, 0, 0, 0, 0]
            ]
        )

        # add objects
        g.add_obj(o1)

        # collect all objects in grid
        objs = set()
        for row in g:
            for tile in row:
                if len(tile.objects) > 0:
                    objs.add(tile.objects[0])

        # there is only one object on the grid
        # a block with ID = 1
        self.assertTrue(objs == set([o1]))

    def test_remove_object(self):
        g = Grid(width=5, height=5, step=0.5, prevent_overlap=False)
        o1 = Obj(
            1, "L", 0, 0, 5, 5,
            block_matrix=[
                [0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0],
                [1, 1, 1, 1, 1],
                [0, 0, 0, 0, 1],
                [0, 0, 0, 0, 0]
            ]
        )

        # add object
        g.add_obj(o1)

        # remove object
        g.remove_obj(o1)

        # collect all objects in grid
        objs = set()
        for row in g:
            for tile in row:
                if len(tile.objects) > 0:
                    objs.add(tile.objects[0])

        # there are no objects on the grid
        self.assertTrue(objs == set())

    def test_gripper_on_grid(self):
        g = Grid(width=5, height=5, step=0.5, prevent_overlap=False)

        grippers = [
            {"x": 12, "y": 3},
            {"x": 5, "y": 5},
            {"x": 5, "y": 6},
            {"x": 1, "y": 1},
            {"x": 2, "y": 3},
        ]

        results = list()
        golden = [False, False, False, True, True]
        for gripper in grippers:
            results.append(g.gripper_on_grid(gripper))

        self.assertEqual(results, golden)
