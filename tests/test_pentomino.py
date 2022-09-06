import unittest
from contrib.pentomino.pentomino import PieceConfig, RelPositions, Colors, Shapes, \
    PropertyNames, UtteranceTypeOrientedDistractorSetSampler, Board
import itertools

TARGET = PieceConfig(Colors.BLUE, Shapes.T, RelPositions.CENTER)
ALL_PIECES = [PieceConfig(color, shape, pos)
              for (color, shape, pos) in itertools.product(list(Colors), list(Shapes), list(RelPositions))]


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


class UtteranceTypeOrientedDistractorSetSamplerTestCase(unittest.TestCase):

    def test_with_num_distractors_returns_num_distractor_configs(self):
        sampler = UtteranceTypeOrientedDistractorSetSampler(ALL_PIECES, TARGET)
        distractors = sampler.create_distractor_configs_csp(unique_props={PropertyNames.REL_POSITION},
                                                            num_distractors=4)
        self.assertEqual(len(distractors), 4)

    def test_with_pos_returns_unique_pos_but_same_color_and_shape(self):
        """ Color: same, Shape: same, Position: differ """
        sampler = UtteranceTypeOrientedDistractorSetSampler(ALL_PIECES, TARGET)
        distractors = sampler.create_distractor_configs_csp(
            unique_props={PropertyNames.REL_POSITION},
            num_distractors=4)
        for distractor in distractors:
            self.assertEqual(distractor.color, TARGET.color)
            self.assertEqual(distractor.shape, TARGET.shape)
            self.assertNotEqual(distractor.rel_position, TARGET.rel_position)

    def test_with_shape_returns_unique_shape_but_same_color(self):
        """ Color: same, Shape: differ, Position: any """
        sampler = UtteranceTypeOrientedDistractorSetSampler(ALL_PIECES, TARGET)
        distractors = sampler.create_distractor_configs_csp(
            unique_props={PropertyNames.SHAPE},
            num_distractors=4)
        for distractor in distractors:
            self.assertEqual(distractor.color, TARGET.color)
            self.assertNotEqual(distractor.shape, TARGET.shape)

    def test_with_color_returns_unique_color(self):
        """ Color: same, Shape: any, Position: any """
        sampler = UtteranceTypeOrientedDistractorSetSampler(ALL_PIECES, TARGET)
        distractors = sampler.create_distractor_configs_csp(
            unique_props={PropertyNames.COLOR},
            num_distractors=4)
        for distractor in distractors:
            self.assertNotEqual(distractor.color, TARGET.color)


if __name__ == "__main__":
    unittest.main()
