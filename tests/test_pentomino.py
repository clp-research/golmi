import unittest
from model.pentomino import PieceConfig, RelPositions, Colors, Shapes, \
    PropertyNames, create_distractor_configs, Board

TARGET = PieceConfig(Colors.BLUE, Shapes.T, RelPositions.CENTER)


class CompositionalBoardTestCase(unittest.TestCase):

    def test_manual_compositional_board(self):
        width, height = 40, 40
        board = Board.create_compositional(width, height, TARGET,
                                           unique_props={PropertyNames.COLOR},
                                           num_distractors=4,
                                           ambiguities={PropertyNames.REL_POSITION: 1})
        for piece in board.pieces:
            print(piece.piece_config)
        print(board.grid)


class RelPositionsTestCase(unittest.TestCase):

    def test_symmetric(self):
        width, height = 500, 500
        for rel_position in list(RelPositions):
            x, y = rel_position.to_random_coords(width, height)
            self.assertEqual(RelPositions.from_coords(x, y, width, height), rel_position, f"x: {x}, y: {y}")


class CreateDistractorsTestCase(unittest.TestCase):

    def test_with_num_distractors_returns_num_distractor_configs(self):
        distractors = create_distractor_configs(TARGET,
                                                unique_props={PropertyNames.REL_POSITION},
                                                num_distractors=4)
        self.assertEqual(len(distractors), 4)

    def test_with_pos_returns_unique_pos_but_same_others(self):
        distractors = create_distractor_configs(TARGET,
                                                unique_props={PropertyNames.REL_POSITION},
                                                num_distractors=4)
        for distractor in distractors:
            self.assertEqual(distractor.color, TARGET.color)
            self.assertEqual(distractor.shape, TARGET.shape)
            self.assertNotEqual(distractor.rel_position, TARGET.rel_position)

    def test_with_shape_returns_unique_shape_but_same_others(self):
        distractors = create_distractor_configs(TARGET,
                                                unique_props={PropertyNames.SHAPE},
                                                num_distractors=4)
        for distractor in distractors:
            self.assertEqual(distractor.color, TARGET.color)
            self.assertNotEqual(distractor.shape, TARGET.shape)
            self.assertEqual(distractor.rel_position, TARGET.rel_position)

    def test_with_color_returns_unique_color_but_same_others(self):
        distractors = create_distractor_configs(TARGET,
                                                unique_props={PropertyNames.COLOR},
                                                num_distractors=4)
        for distractor in distractors:
            self.assertNotEqual(distractor.color, TARGET.color)
            self.assertEqual(distractor.shape, TARGET.shape)
            self.assertEqual(distractor.rel_position, TARGET.rel_position)

    def test_with_color_with_single_ambiguity_returns_single_ambiguity(self):
        distractors = create_distractor_configs(TARGET,
                                                unique_props={PropertyNames.COLOR},
                                                num_distractors=4,
                                                ambiguities={PropertyNames.REL_POSITION: 1})
        count = sum([1 for distractor in distractors if distractor.rel_position == TARGET.rel_position])
        self.assertEqual(count, 1)

    def test_with_color_with_given_variety_and_ambiguity_returns_single_ambiguity(self):
        distractors = create_distractor_configs(TARGET,
                                                unique_props={PropertyNames.COLOR},
                                                num_distractors=4,
                                                varieties={
                                                    PropertyNames.COLOR: 0,
                                                    PropertyNames.SHAPE: 0,
                                                    PropertyNames.REL_POSITION: 0
                                                },
                                                ambiguities={
                                                    PropertyNames.COLOR: 0,
                                                    PropertyNames.SHAPE: 0,
                                                    PropertyNames.REL_POSITION: 1
                                                })
        count = sum([1 for distractor in distractors if distractor.rel_position == TARGET.rel_position])
        self.assertEqual(count, 1)

    def test_with_color_with_multi_ambiguities_returns_accordingly(self):
        distractors = create_distractor_configs(TARGET,
                                                unique_props={PropertyNames.COLOR},
                                                num_distractors=4,
                                                ambiguities={PropertyNames.REL_POSITION: 2,
                                                             PropertyNames.SHAPE: 3})
        pos_count = sum([1 for distractor in distractors if distractor.rel_position == TARGET.rel_position])
        self.assertEqual(pos_count, 2)
        shape_count = sum([1 for distractor in distractors if distractor.shape == TARGET.shape])
        self.assertEqual(shape_count, 3)

    def test_with_color_fails_when_ambiguous_color(self):
        with self.assertRaises(Exception):
            create_distractor_configs(TARGET,
                                      unique_props={PropertyNames.COLOR},
                                      num_distractors=4,
                                      ambiguities={PropertyNames.REL_POSITION: 1,
                                                   PropertyNames.COLOR: 1,
                                                   PropertyNames.SHAPE: 2})


if __name__ == "__main__":
    unittest.main()
