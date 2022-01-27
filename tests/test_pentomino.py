import unittest

from model.pentomino import SingleUPVDistractorSetGenerator, PropertyNames, Colors, Shapes, PieceConfig, RelPositions, \
    DistractorConfigGenerator


class SingleUPVDistractorSetGeneratorTestCase(unittest.TestCase):

    def test_generate_all_distractor_configs(self):
        num_shapes = len(list(Shapes))
        num_colors = len(list(Colors))
        assert num_colors == 8
        assert num_shapes == 12

        generator = DistractorConfigGenerator({PropertyNames.COLOR: list(Colors),
                                               PropertyNames.SHAPE: list(Shapes)})
        configs = generator.generate_all_distractor_configs()
        assert len(configs) == 96

    def test_generate_all_sets_with_num_distractors_is_2(self):
        # Compositional set on "Colors"
        # All other distractors do NOT share the color, but at least one distractor shares the shape
        num_shapes = len(list(Shapes))
        num_colors = len(list(Colors))
        assert num_colors == 8
        assert num_shapes == 12

        num_distractors = 2
        target_piece = PieceConfig(color=Colors.BLUE, shape=Shapes.T, rel_position=RelPositions.CENTER)

        generator = SingleUPVDistractorSetGenerator(target_piece,
                                                    unique_prop=PropertyNames.COLOR,
                                                    num_distractors=num_distractors,
                                                    prop_values={PropertyNames.COLOR: list(Colors),
                                                                 PropertyNames.SHAPE: list(Shapes)})
        sets = generator.setup().generate_all_sets()

        num_other_looks = num_shapes * (num_colors - 1)  # unshare the color, but allow all shapes
        num_share_looks = num_colors - 1  # unshare the color, but shares the same shape as the target piece
        expected_count = num_share_looks * num_other_looks ** (num_distractors - 1)
        assert len(sets) == expected_count, f"Expected {expected_count}, but is {len(sets)}"


if __name__ == '__main__':
    unittest.main()
