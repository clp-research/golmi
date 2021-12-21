import unittest
from model.pentomino import PieceConfig, RelPositions, Colors, Shapes, \
    PropertyNames, create_distractor_configs

TARGET = PieceConfig(Colors.BLUE, Shapes.T, RelPositions.CENTER)


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


if __name__ == '__main__':
    unittest.main()
