import unittest

from model.config import Config
from model.generator import CompositionalSceneGenerator
from model.obj import Obj

BLOCK_MATRIX = [
    [0, 0, 0, 0, 0],
    [0, 0, 0, 1, 0],
    [0, 1, 1, 1, 0],
    [0, 0, 0, 1, 0],
    [0, 0, 0, 0, 0]
]


class MyTestCase(unittest.TestCase):

    def test_create_distractors(self):
        config = Config.from_json("task_generators.json")
        piece = Obj(id_n=0, obj_type="T", x=0, y=0, block_matrix=BLOCK_MATRIX)
        generator = CompositionalSceneGenerator(config)
        distractors = generator.create_distractors(piece, unique_props=["color"], num_distractors=4)
        for d in distractors:
            print(d.type, d.color)


if __name__ == '__main__':
    unittest.main()
