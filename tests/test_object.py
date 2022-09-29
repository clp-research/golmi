import unittest

from golmi.server.obj import Obj


class Test(unittest.TestCase):
    """
    Tests on Object
    """
    def test_rotate(self):
        o = Obj(
            1, "L", 0, 0, 5, 5,
            block_matrix=[
                [0, 1, 0, 0, 0],
                [0, 1, 0, 0, 0],
                [0, 1, 1, 1, 1],
                [0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0]
            ]
        )

        target = [
           # 90 degrees
           [[0, 0, 0, 0, 0],
            [0, 0, 1, 1, 1],
            [0, 0, 1, 0, 0],
            [0, 0, 1, 0, 0],
            [0, 0, 1, 0, 0]],
           # 180 degrees
           [[0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [1, 1, 1, 1, 0],
            [0, 0, 0, 1, 0],
            [0, 0, 0, 1, 0]],
           # 270 degrees
           [[0, 0, 1, 0, 0],
            [0, 0, 1, 0, 0],
            [0, 0, 1, 0, 0],
            [1, 1, 1, 0, 0],
            [0, 0, 0, 0, 0]]
        ]

        rotated = list()
        for angle in [90, 180, 270]:
            rot = Obj.rotate_block_matrix(o.block_matrix, angle)
            rotated.append(rot)

        self.assertEqual(rotated, target)

    def test_flip(self):
        o = Obj(
            1, "L", 0, 0, 5, 5,
            block_matrix=[
                [0, 1, 0, 0, 0],
                [0, 1, 0, 0, 0],
                [0, 1, 1, 1, 1],
                [0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0]
            ]
        )

        target = [
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 1, 1, 1, 1],
            [0, 1, 0, 0, 0],
            [0, 1, 0, 0, 0]
        ]

        rotated = Obj.flip_block_matrix(o.block_matrix)
        self.assertEqual(rotated, target)

    def test_occupied(self):
        o = Obj(
            1, "L", 0, 0, 5, 5,
            block_matrix=[
                [0, 1, 0, 0, 0],
                [0, 1, 0, 0, 0],
                [0, 1, 1, 1, 1],
                [0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0]
            ]
        )

        target = [
            {"x": 1, "y": 0},
            {"x": 1, "y": 1},
            {"x": 1, "y": 2},
            {"x": 2, "y": 2},
            {"x": 3, "y": 2},
            {"x": 4, "y": 2},
        ]

        occupied = o.occupied()
        self.assertEqual(target, occupied)
