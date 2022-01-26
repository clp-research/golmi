import logging
from enum import Enum
import random
from typing import List, Set, Dict

from model.grid import Grid
from model.obj import Obj

import numpy as np


class Shapes(Enum):
    F = ("F", [
        [0, 0, 0, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 0, 1, 1, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0]
    ])
    I = ("I", [
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0]
    ])
    L = ("L", [
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 0, 0, 0, 0]
    ])
    N = ("N", [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0],
        [0, 0, 1, 1, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0]
    ])
    P = ("P", [
        [0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 0, 0, 0, 0]
    ])
    T = ("T", [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0]
    ])
    U = ("U", [
        [0, 0, 0, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 1, 0, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 0, 0, 0, 0]
    ])
    V = ("V", [
        [0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0],
        [0, 1, 0, 0, 0],
        [0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0]
    ])
    W = ("W", [
        [0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 0, 1, 1, 0],
        [0, 0, 0, 0, 0]
    ])
    X = ("X", [
        [0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0]
    ])
    Y = ("Y", [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [1, 1, 1, 1, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0]
    ])
    Z = ("Z", [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0],
        [0, 1, 1, 1, 0],
        [0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0]
    ])

    def __init__(self, value_name, value_matrix):
        self.value_name = value_name
        self.value_matrix = value_matrix

    def __repr__(self):
        return f"{self.value_name}"


class Rotations(Enum):
    DEGREE_0 = 0
    DEGREE_90 = 90
    DEGREE_180 = 180
    DEGREE_270 = 270


class Colors(Enum):
    RED = ("red", "#ff0000", [255, 0, 0])
    ORANGE = ("orange", "#ffa500", [255, 165, 0])
    YELLOW = ("yellow", "#ffff00", [255, 255, 0])
    GREEN = ("green", "#008000", [0, 128, 0])
    BLUE = ("blue", "#0000ff", [0, 0, 255])
    PURPLE = ("purple", "#800080", [128, 0, 128])
    BROWN = ("brown", "#8b4513", [139, 69, 19])
    GREY = ("grey", "#808080", [128, 128, 128])

    def __init__(self, value_name, value_hex, value_rgb):
        self.value_name = value_name
        self.value_hex = value_hex
        self.value_rgb = value_rgb


class RelPositions(Enum):
    TOP_LEFT = "top left"
    TOP_CENTER = "top"
    TOP_RIGHT = "top right"
    CENTER_RIGHT = "right"
    BOTTOM_RIGHT = "bottom right"
    BOTTOM_CENTER = "bottom"
    BOTTOM_LEFT = "bottom left"
    CENTER_LEFT = "left"
    CENTER = "center"

    def to_random_coords(self, board_width, board_height):
        # the relative positions are derived from their own "grid"-like board
        # with 3,3 there are as many RelPositions as cells in the grid, but
        # we could have also "thinner" slices or put more "space" onto the edges
        # TODO there is no general case yet
        num_cols, num_rows = 3, 3
        width_step, height_step = board_width // num_cols, board_height // num_rows

        # Uff, this is a bit harsh.
        # Pieces coords is their upper-left corner!
        # They are furthermore drawn on potentially 5x5 grids.
        piece_grid_size = 5

        # So when we sample (0,0) then the piece is in the upper left corner fully fit,
        # but when we sample something at the right or bottom, then pieces cannot be fully drawn anymore
        # so the actually possible coordinate space is smaller than what is shown on the board.
        # We apply the "padding" for all max values at the end of this method.
        x_min, x_max = 0, board_width
        y_min, y_max = 0, board_height

        # This is in particular difficult, because we "see" the pieces on other coords (e.g. the center of a piece).
        # So given the coords, an algorithm must actually "imagine" where the piece is actually drawn using an offset
        # and cannot simply derive this from the coords itself
        x_left = 0, width_step
        x_right = 2 * width_step, board_width

        y_top = 0, height_step
        y_bottom = 2 * height_step, board_height

        x_center = width_step, 2 * width_step
        y_center = height_step, 2 * height_step

        if self == RelPositions.TOP_LEFT:
            x_min, x_max = x_left
            y_min, y_max = y_top
        if self == RelPositions.TOP_CENTER:
            x_min, x_max = x_center
            y_min, y_max = y_top
        if self == RelPositions.TOP_RIGHT:
            x_min, x_max = x_right
            y_min, y_max = y_top
        if self == RelPositions.CENTER_RIGHT:
            x_min, x_max = x_right
            y_min, y_max = y_center
        if self == RelPositions.BOTTOM_RIGHT:
            x_min, x_max = x_right
            y_min, y_max = y_bottom
        if self == RelPositions.BOTTOM_CENTER:
            x_min, x_max = x_center
            y_min, y_max = y_bottom
        if self == RelPositions.BOTTOM_LEFT:
            x_min, x_max = x_left
            y_min, y_max = y_bottom
        if self == RelPositions.CENTER_LEFT:
            x_min, x_max = x_left
            y_min, y_max = y_center
        if self == RelPositions.CENTER:
            x_min, x_max = x_center
            y_min, y_max = y_center
        return random.randint(x_min, x_max - piece_grid_size), random.randint(y_min, y_max - piece_grid_size)

    @staticmethod
    def from_coords(x, y, board_width, board_height):
        # the relative positions are derived from their own "grid"-like board
        # with 3,3 there are as many RelPositions as cells in the grid, but
        # we could have also "thinner" slices or put more "space" onto the edges
        # TODO there is no general case yet
        num_cols, num_rows = 3, 3
        width_step, height_step = board_width // num_cols, board_height // num_rows
        # x = obj.x + (obj.width / 2)
        # y = obj.y + (obj.height / 2)
        # TODO this actually looks wrong
        pos = None
        if y < 1 * height_step:
            pos = RelPositions.TOP_CENTER
        elif y >= 2 * height_step:
            pos = RelPositions.BOTTOM_CENTER
        if x < 1 * width_step:
            if pos == RelPositions.TOP_CENTER:
                return RelPositions.TOP_LEFT
            if pos == RelPositions.BOTTOM_CENTER:
                return RelPositions.BOTTOM_LEFT
            return RelPositions.CENTER_LEFT
        elif x >= 2 * width_step:
            if pos == RelPositions.TOP_CENTER:
                return RelPositions.TOP_RIGHT
            if pos == RelPositions.BOTTOM_CENTER:
                return RelPositions.BOTTOM_RIGHT
            return RelPositions.CENTER_RIGHT
        if pos:
            return pos
        return RelPositions.CENTER


class PropertyNames(Enum):
    COLOR = "color"
    SHAPE = "shape"
    REL_POSITION = "rel_position"
    ROTATION = "rotation"

    @classmethod
    def from_string(cls, name):
        for pn in list(cls):
            if pn.value == name:
                return pn
        return None


class PieceConfig:

    def __init__(self, color: Colors, shape: Shapes, rel_position: RelPositions, rotation=Rotations.DEGREE_0):
        self.color = color
        self.shape = shape
        self.rel_position = rel_position
        self.rotation = rotation

    def __getitem__(self, prop_name: PropertyNames):
        if prop_name == PropertyNames.COLOR:
            return self.color
        if prop_name == PropertyNames.SHAPE:
            return self.shape
        if prop_name == PropertyNames.REL_POSITION:
            return self.rel_position
        if prop_name == PropertyNames.ROTATION:
            return self.rotation
        raise Exception(f"Cannot get {prop_name}.")

    def __setitem__(self, prop_name: PropertyNames, value):
        if prop_name == PropertyNames.COLOR:
            self.color = value
            return
        if prop_name == PropertyNames.SHAPE:
            self.shape = value
            return
        if prop_name == PropertyNames.REL_POSITION:
            self.rel_position = value
            return
        if prop_name == PropertyNames.ROTATION:
            self.rotation = value
            return
        raise Exception(f"Cannot set {prop_name}.")

    def __repr__(self):
        return f"{self.shape}, {self.color}, {self.rel_position}"

    def copy(self):
        return PieceConfig(self.color, self.shape, self.rel_position)

    @classmethod
    def from_random(cls, colors, shapes, rel_positions):
        return cls(random.choice(colors), random.choice(shapes), random.choice(rel_positions))


class Piece:

    def __init__(self, piece_id: int, piece_config: PieceConfig, piece_obj: Obj):
        self.piece_obj = piece_obj
        self.piece_config = piece_config
        self.piece_id = piece_id

    @classmethod
    def from_config(cls, piece_id, piece_config, board_width, board_height):
        x, y = piece_config.rel_position.to_random_coords(board_width, board_height)
        piece_obj = Obj(piece_id,
                        obj_type=piece_config.shape.value_name,
                        x=x, y=y,
                        block_matrix=piece_config.shape.value_matrix,
                        color=piece_config.color.value_name)
        if piece_config.rotation:
            piece_obj.rotate(piece_config.rotation.value)
        return cls(piece_id, piece_config, piece_obj)


class Board:

    def __init__(self, board_width, board_height):
        self.pieces = []
        self.pieces_by_id = {}
        self.grid = Grid(board_width, board_height, step=1, prevent_overlap=True)
        self.board_width = board_width
        self.board_height = board_height

    def to_rgb_array(self):
        color_grid = []
        for row in self.grid:
            color_row = []
            for tile in row:
                tile_color = [255, 255, 255]  # white
                if tile.objects:
                    piece_id = tile.objects[0]
                    tile_color = self.get_piece(piece_id).piece_config.color.value_rgb
                color_row.append(tile_color)
            color_grid.append(color_row)
        return np.array(color_grid)

    def get_piece(self, piece_id: int):
        return self.pieces_by_id[piece_id]

    def add_pieces_from_configs(self, piece_configs: List[PieceConfig], max_attempts=100):
        for piece_config in piece_configs:
            self.add_piece_from_config(piece_config, max_attempts)

    def add_piece_from_config(self, piece_config: PieceConfig, max_attempts=100):
        for attempt in range(max_attempts):  # re-create with potentially different coords
            piece = Piece.from_config(len(self.pieces), piece_config, self.board_width, self.board_height)
            if self.grid.is_legal_position(piece.piece_obj.occupied(), piece.piece_id):
                self.grid.add_obj(piece.piece_obj)
                self.pieces.append(piece)
                self.pieces_by_id[piece.piece_id] = piece
                return True
        print(f"Max attempts reached, cannot add piece {piece_config}")
        return False

    @classmethod
    def create_compositional(cls, board_width, board_height,
                             piece_config: PieceConfig,
                             unique_props: Set[PropertyNames],
                             num_distractors: int = 1,
                             varieties: Dict[PropertyNames, int] = None,
                             ambiguities: Dict[PropertyNames, int] = None):
        distractors = create_distractor_configs(piece_config, unique_props, num_distractors, varieties, ambiguities)
        return cls.create_compositional_from_configs(board_width, board_height, piece_config, distractors)

    @classmethod
    def create_compositional_from_configs(cls, board_width, board_height,
                                          piece_config: PieceConfig, distractors: List[PieceConfig]):
        board = Board(board_width, board_height)
        # TODO this is just a quick and dirty hack
        possible_rotations = list(Rotations)
        piece_config[PropertyNames.ROTATION] = random.choice(possible_rotations)
        for d in distractors:
            d[PropertyNames.ROTATION] = random.choice(possible_rotations)
        board.add_piece_from_config(piece_config)
        board.add_pieces_from_configs(distractors)
        return board


def reduce_atoms(piece_config: PieceConfig, unique_props: Set[PropertyNames], varieties: Dict = None):
    """ Remove uniq prop atom from the sampling distribution """
    atoms = {
        PropertyNames.SHAPE: list(Shapes),
        PropertyNames.COLOR: list(Colors),
        PropertyNames.REL_POSITION: list(RelPositions),
        PropertyNames.ROTATION: list(Rotations)
    }
    for prop_name in unique_props:
        if len(atoms[prop_name]) < 2:
            raise Exception("Cannot discriminate on a property with less than 2 possible values")
        atoms[prop_name].remove(piece_config[prop_name])
        if varieties and prop_name in varieties:
            prop_variety = varieties[prop_name]
            if prop_variety > 0:
                atoms[prop_name] = random.sample(atoms[prop_name], k=prop_variety)
    return atoms


def create_distractor_configs(piece_config: PieceConfig,
                              unique_props: Set[PropertyNames],
                              num_distractors: int = 1,
                              varieties: Dict[PropertyNames, int] = None,
                              ambiguities: Dict[PropertyNames, int] = None):
    """
    :param piece_config:
    :param unique_props:
    :param num_distractors:
    :param varieties: the number of other different values for the props. Zero, means all available are used.
        Defaults to all available properties.
    :param ambiguities: We allow a more fine-grained control on how many distractors share exactly the same "non-unique"
            properties as the target piece (at least one piece must be still identical in "non-unique" props).
            When not given (default), then all distractors share the same values with the target piece
            (maximal ambiguity) except for the unique properties.
    :return:
    """
    if num_distractors < 1:
        raise Exception(f"There must be at least one distractor, but num_distractors is {num_distractors}")
    # initialize all looking the same
    distractor_configs = [piece_config.copy() for _ in range(num_distractors)]
    # When we have a single uniq prop, then all other pieces look the same except in that prop
    if len(unique_props) == 1:
        non_unique_props = set(PropertyNames)
        atoms_reduced_unique = reduce_atoms(piece_config, unique_props, varieties)
        for unique_prop in unique_props:
            non_unique_props.remove(unique_prop)
            for distractor_config in distractor_configs:
                # We choose from a variable number of atoms for the prop to differ ("variety")
                distractor_config[unique_prop] = random.choice(atoms_reduced_unique[unique_prop])
        if ambiguities and num_distractors > 1:
            # We allow a more fine-grained control on how many distractors share exactly the same "non-unique"
            # properties as the target piece (at least one piece must be still identical in "non-unique" props)
            differ_piece_configs = random.sample(distractor_configs, k=num_distractors - 1)
            atoms_reduced_non_unique = reduce_atoms(piece_config, non_unique_props, varieties)
            for ambiguous_prop, ambiguous_count in ambiguities.items():
                if ambiguous_prop in unique_props:
                    logging.warning(f"Ignore unique prop {ambiguous_prop} in ambiguities {ambiguities}.")
                    continue
                if ambiguous_count <= 0 or ambiguous_count >= num_distractors:
                    continue  # all should look the same in "non-unique" props
                differ_count = len(differ_piece_configs)
                if ambiguous_count > 1:
                    differ_count = differ_count - ambiguous_count + 1  # one piece is always ambiguous
                differ_distractors = random.sample(differ_piece_configs, differ_count)
                for differ_distractor in differ_distractors:
                    differ_distractor[ambiguous_prop] = random.choice(atoms_reduced_non_unique[ambiguous_prop])
    return distractor_configs
