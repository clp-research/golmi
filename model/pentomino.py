import copy
import logging
from enum import Enum, IntEnum
import random
from typing import List, Set, Dict, Tuple

from collections import defaultdict

from .grid import Grid
from .obj import Obj

import numpy as np


class ShapesMatrix(Enum):
    F = [
        [0, 0, 0, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 0, 1, 1, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0]
    ]
    I = [
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0]
    ]
    L = [
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 0, 0, 0, 0]
    ]
    N = [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0],
        [0, 0, 1, 1, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0]
    ]
    P = [
        [0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 0, 0, 0, 0]
    ]
    T = [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0]
    ]
    U = [
        [0, 0, 0, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 1, 0, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 0, 0, 0, 0]
    ]
    V = [
        [0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0],
        [0, 1, 0, 0, 0],
        [0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0]
    ]
    W = [
        [0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 0, 1, 1, 0],
        [0, 0, 0, 0, 0]
    ]
    X = [
        [0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0]
    ]
    Y = [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [1, 1, 1, 1, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0]
    ]
    Z = [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0],
        [0, 1, 1, 1, 0],
        [0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0]
    ]


class Shapes(Enum):
    F = "F"
    I = "I"
    L = "L"
    N = "N"
    P = "P"
    T = "T"
    U = "U"
    V = "V"
    W = "W"
    X = "X"
    Y = "Y"
    Z = "Z"

    def __repr__(self):
        return f"{self.value}"

    def __key(self):
        return self.value

    def __hash__(self):
        return hash(self.__key())

    def __str__(self):
        return self.value

    def __lt__(self, other):
        return self.value.__lt__(other.value)

    def to_json(self):
        return self.value

    @classmethod
    def from_json(cls, value):
        return cls[value]


class Rotations(IntEnum):
    DEGREE_0 = 0
    DEGREE_90 = 90
    DEGREE_180 = 180
    DEGREE_270 = 270

    def __repr__(self):
        return f"{self.value}"

    def __key(self):
        return self.value

    def __hash__(self):
        return hash(self.__key())

    def __str__(self):
        return self.value

    def __lt__(self, other):
        return self.value.__lt__(other.value)

    def to_json(self):
        return self.value

    @classmethod
    def from_json(cls, value):
        return cls[value]


class Colors(Enum):
    RED = ("red", "#ff0000", [255, 0, 0])
    ORANGE = ("orange", "#ffa500", [255, 165, 0])
    YELLOW = ("yellow", "#ffff00", [255, 255, 0])
    GREEN = ("green", "#008000", [0, 128, 0])
    BLUE = ("blue", "#0000ff", [0, 0, 255])
    CYAN = ("cyan", "#00ffff", [0, 255, 255])
    PURPLE = ("purple", "#800080", [128, 0, 128])
    BROWN = ("brown", "#8b4513", [139, 69, 19])
    GREY = ("grey", "#808080", [128, 128, 128])
    PINK = ("pink", "#ffc0cb", [255, 192, 203])
    OLIVE_GREEN = ("olive green", "#808000", [128, 128, 0])  # dark yellowish-green
    NAVY_BLUE = ("navy blue", "#000080", [0, 0, 128])  # dark blue

    def __init__(self, value_name, value_hex, value_rgb):
        self.value_name = value_name
        self.value_hex = value_hex
        self.value_rgb = value_rgb

    def __repr__(self):
        return f"{self.value_name}"

    def __key(self):
        return self.value_name

    def __hash__(self):
        return hash(self.__key())

    def __str__(self):
        return self.value_name

    def __lt__(self, other):
        return self.value_name.__lt__(other.value_name)

    def to_json(self):
        return self.value_name

    @classmethod
    def from_json(cls, value_name):
        return cls[value_name.upper().replace(" ", "_")]


class RelPositions(Enum):
    TOP_LEFT = "top left"
    TOP_CENTER = "top center"
    TOP_RIGHT = "top right"
    CENTER_RIGHT = "right"
    BOTTOM_RIGHT = "bottom right"
    BOTTOM_CENTER = "bottom center"
    BOTTOM_LEFT = "bottom left"
    CENTER_LEFT = "left"
    CENTER = "center"

    def __repr__(self):
        return f"{self.value}"

    def __key(self):
        return self.value

    def __hash__(self):
        return hash(self.__key())

    def __str__(self):
        return self.value

    def __lt__(self, other):
        return self.value.__lt__(other.value)

    def to_json(self):
        return self.value

    @classmethod
    def from_json(cls, value):
        return cls[value.upper().replace(" ", "_")]

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

    def __repr__(self):
        return f"{self.value}"

    def __key(self):
        return self.value

    def __hash__(self):
        return hash(self.__key())

    def __str__(self):
        return self.value

    def __lt__(self, other):
        return self.value.__lt__(other.value)

    def to_json(self):
        return self.value

    @classmethod
    def from_json(cls, value):
        return PropertyNames[value.upper()]

    @classmethod
    def from_string(cls, name):
        for pn in list(cls):
            if pn.value == name:
                return pn
        return None


class PieceConfig:

    def __init__(self, color: Colors = None, shape: Shapes = None, rel_position: RelPositions = None,
                 rotation=Rotations.DEGREE_0):
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
        raise Exception(f"Cannot get {prop_name}")

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
        return f"({self.shape}, {self.color}, {self.rel_position})"

    def __str__(self):
        return f"({self.shape}, {self.color}, {self.rel_position})"

    def __key(self):
        return self.shape, self.color, self.rel_position

    def __hash__(self):
        return hash(self.__key())

    def __lt__(self, other):
        return self.__key() < other.__key()

    def __eq__(self, other):
        if isinstance(other, PieceConfig):
            return self.__key() == other.__key()
        return NotImplemented

    def copy(self):
        return PieceConfig(self.color, self.shape, self.rel_position)

    def to_json(self):
        return self.color.to_json(), self.shape.to_json(), self.rel_position.to_json(), self.rotation.to_json()

    @classmethod
    def from_json(cls, t: Tuple):
        return cls(Colors.from_json(t[0]), Shapes.from_json(t[1]), RelPositions.from_json(t[2]),
                   Rotations.from_json(t[3]))

    @classmethod
    def from_random(cls, colors, shapes, rel_positions):
        return cls(random.choice(colors), random.choice(shapes), random.choice(rel_positions))

    @staticmethod
    def create_all(num_colors: int = None, num_shapes: int = None, num_positions: int = None) -> List:
        property_values = {
            PropertyNames.COLOR: list(Colors)[:num_colors] if num_colors else list(Colors),
            PropertyNames.SHAPE: list(Shapes)[:num_shapes] if num_shapes else list(Shapes),
            PropertyNames.REL_POSITION: list(RelPositions)[:num_positions] if num_positions else list(RelPositions)
        }
        return DistractorConfigGenerator(property_values).generate_all_distractor_configs()

    @staticmethod
    def group_by_pos(pieces: List):
        pieces_by_pos = defaultdict(list)
        for piece in pieces:
            pieces_by_pos[piece.rel_position].append(piece)
        # print("pieces_by_pos", [len(pieces_by_pos[p]) for p in pieces_by_pos])
        return pieces_by_pos


class PieceConfigSet:

    def __init__(self, pieces: List[PieceConfig]):
        self.pieces = sorted(pieces)  # allow duplicates, but ignore order

    def __repr__(self):
        return f"PCS[{self.pieces}]"

    def __str__(self):
        return f"({self.pieces})"

    def __iter__(self):
        return self.pieces.__iter__()

    def __len__(self):
        return len(self.pieces)

    def __key(self):
        return tuple(self.pieces)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if isinstance(other, PieceConfigSet):
            return self.__key() == other.__key()
        return NotImplemented

    def to_json(self):
        return [p.to_json() for p in self.pieces]

    @classmethod
    def from_json(cls, pieces: List):
        return cls([PieceConfig.from_json(p) for p in pieces])


class PieceConfigSetSampler:

    def sample_set(self, set_size):
        raise NotImplementedError()


class RestrictivePieceConfigSetSampler(PieceConfigSetSampler):

    def __init__(self, pieces: List[PieceConfig], pieces_per_pos: int = 2):
        self.pieces_per_pos = pieces_per_pos
        self.pieces_by_pos: Dict[RelPositions, List[PieceConfig]] = PieceConfig.group_by_pos(pieces)

    def sample_set(self, n_pieces: int):
        # hierarchical sampling:
        # 1. sample position (so we can block certain positions if drawn already twice)
        # 2. sample piece on position
        # Note: if you dont need this, simply use random.sample(n,k)
        allowed_positions = list(RelPositions)
        num_pos = len(allowed_positions)
        num_possible = self.pieces_per_pos * num_pos
        if num_possible < n_pieces:
            raise Exception(f"with pieces_per_pos={self.pieces_per_pos} and num_pos={num_pos} "
                            f"there can be maximal n_pieces={num_possible} in the set")
        pos_counts = dict([(pos, 0) for pos in allowed_positions])
        piece_set = []
        for _ in range(n_pieces):
            pos = random.choice(allowed_positions)
            piece = random.choice(self.pieces_by_pos[pos])
            piece_set.append(piece)
            pos_counts[piece.rel_position] += 1
            for pos, counts in pos_counts.items():
                if counts >= 2:
                    if pos in allowed_positions:
                        allowed_positions.remove(pos)
        return PieceConfigSet(piece_set)


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


def exclude_property_values(piece_config: PieceConfig, unique_props: Set[PropertyNames],
                            property_values: Dict[PropertyNames, List], varieties: Dict = None):
    """ Remove uniq prop atom from the given atoms. This is basically a set operation. """
    # defensive copy (otherwise property_values may shrink on repeated calls)
    reduced_values = copy.deepcopy(property_values)
    for prop_name in unique_props:
        if prop_name not in reduced_values:
            raise Exception(f"Cannot discriminate on a property that does not exist. "
                            f"{prop_name} not in {reduced_values.keys()}")
        if len(reduced_values[prop_name]) < 2:
            raise Exception("Cannot discriminate on a property with less than 2 possible values")
        piece_property_value = piece_config[prop_name]
        if piece_property_value in reduced_values[prop_name]:
            reduced_values[prop_name].remove(piece_property_value)
        if varieties and prop_name in varieties:
            prop_variety = varieties[prop_name]
            if prop_variety > 0:
                reduced_values[prop_name] = random.sample(reduced_values[prop_name], k=prop_variety)
    return reduced_values


def create_distractor_configs(piece_config: PieceConfig,
                              unique_props: Set[PropertyNames],
                              num_distractors: int = 1,
                              varieties: Dict[PropertyNames, int] = None,
                              ambiguities: Dict[PropertyNames, int] = None):
    """
    :param piece_config:
    :param unique_props:
    :param num_distractors:
    :param varieties: this is basically an "amount-based" white list for property values. Zero, means that all available
            values are possible to choose from. Otherwise, the possible property values are reduced to the given number.
            Defaults to use all available property values.
    :param ambiguities: We allow a more fine-grained control on how many distractors share exactly the same "non-unique"
            properties as the target piece (at least one piece must be still identical in "non-unique" props).
            When not given (default), then all distractors share the same values with the target piece
            (maximal ambiguity) except for the unique properties.
    :return:
    """
    if num_distractors < 1:
        raise Exception(f"There must be at least one distractor, but num_distractors is {num_distractors}")
    # initialize all possible values
    property_values = {
        PropertyNames.SHAPE: list(Shapes),
        PropertyNames.COLOR: list(Colors),
        PropertyNames.REL_POSITION: list(RelPositions),
        PropertyNames.ROTATION: list(Rotations)
    }
    # initialize all looking the same
    distractor_configs = [piece_config.copy() for _ in range(num_distractors)]
    # When we have a single uniq prop, then all other pieces are disallowed to have that prop
    if len(unique_props) == 1:
        non_unique_props = set(PropertyNames)
        atoms_reduced_unique = exclude_property_values(piece_config, unique_props, property_values, varieties)
        for unique_prop in unique_props:
            non_unique_props.remove(unique_prop)
            for distractor_config in distractor_configs:
                # We choose from a variable number of atoms for the prop to differ ("variety")
                distractor_config[unique_prop] = random.choice(atoms_reduced_unique[unique_prop])
        if ambiguities and num_distractors > 1:
            # We allow a more fine-grained control on how many distractors share exactly the same "non-unique"
            # properties as the target piece (at least one piece must be still identical in "non-unique" props)
            differ_piece_configs = random.sample(distractor_configs, k=num_distractors - 1)
            atoms_reduced_non_unique = exclude_property_values(piece_config, non_unique_props,
                                                               property_values, varieties)
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
    # When we have a two uniq prop (which is a weird wording as we need two props to uniquely identify a piece),
    # then all other pieces are disallowed to have that prop,
    # but there is at least one piece that shares one uniq prop and one non-uniq prop, but not the other uniq prop
    # (a) to rule out the non-uniq property to be mentioned
    # (b) to force that two properties must be mentioned
    # for example:
    # - RED F CENTER with COLOR, SHAPE (RED, F)      requires BLUE F CENTER (shares u-SHAPE, n-POSIT)
    # - RED F CENTER with COLOR, SHAPE (RED, F)      requires RED T CENTER  (shares u-COLOR, n-POSIT)
    # - RED F CENTER with SHAPE, POSIT (F, CENTER)   requires RED F LEFT    (shares n-COLOR, u-SHAPE)
    # - RED F CENTER with SHAPE, POSIT (F, CENTER)   requires RED T CENTER  (shares n-COLOR, u-POSIT)
    # - RED F CENTER with COLOR, POSIT (RED, CENTER) requires BLUE F CENTER (shares n-SHAPE, u-POSIT)
    # - RED F CENTER with COLOR, POSIT (RED, CENTER) requires RED F LEFT    (shares n-SHAPE, u-COLOR)
    if len(unique_props) == 2:
        unique_props = list(unique_props)
        non_unique_props = list(PropertyNames)
        for unique_prop in unique_props:
            non_unique_props.remove(unique_prop)
        # here, make sure all pieces look different first
        atoms_reduced = exclude_property_values(piece_config, set(PropertyNames), property_values, varieties)
        for prop in list(PropertyNames):
            for distractor_config in distractor_configs:
                # We choose from a variable number of atoms for the prop to differ ("variety")
                distractor_config[prop] = random.choice(atoms_reduced[prop])
        # then make sure that there are two pieces that share one of the uniq props and the non-uniq prop
        ambiguous_piece_configs = random.sample(distractor_configs, k=2)
        for idx, ambiguous_piece_config in enumerate(ambiguous_piece_configs):
            non_unique_prop = non_unique_props[0]
            ambiguous_piece_config[non_unique_prop] = piece_config[non_unique_prop]
            shared_unique_prop = unique_props[idx]  # one share the first uniq prop, one the second uniq prop
            ambiguous_piece_config[shared_unique_prop] = piece_config[shared_unique_prop]
    # When we have a three uniq prop (which is a weird wording as we need three props to uniquely identify a piece),
    # then all other pieces are disallowed to have that prop,
    # but there is are three pieces that share two uniq props, but not the other uniq prop
    # (a) there are no non-uniq probs to be ruled out
    # (b) to force that three properties must be mentioned
    if len(unique_props) == 3:
        unique_props = list(unique_props)
        # here, make sure all pieces look different first
        atoms_reduced = exclude_property_values(piece_config, set(PropertyNames), property_values, varieties)
        for prop in list(PropertyNames):
            for distractor_config in distractor_configs:
                # We choose from a variable number of atoms for the prop to differ ("variety")
                distractor_config[prop] = random.choice(atoms_reduced[prop])
        # then make sure that there is at least one piece that shares two of the uniq props
        ambiguous_piece_configs = random.sample(distractor_configs, k=3)
        for piece_idx, ambiguous_piece_config in enumerate(ambiguous_piece_configs):
            for idx, uniq_prop in enumerate(unique_props):
                if idx == (piece_idx % 3):
                    pass  # not share this, but the other two
                else:
                    ambiguous_piece_config[uniq_prop] = piece_config[uniq_prop]
    return distractor_configs


def create_all_distractor_configs(piece_config: PieceConfig,
                                  unique_props: Set[PropertyNames],
                                  num_distractors: int = 1,
                                  prop_values: Dict[PropertyNames, List] = None
                                  ) -> List[List[PieceConfig]]:
    """
    We generate and return all possible scenes for the given pieces config and number of distractors
    based on the property values. The given piece config is always the first entry in the returned lists.

    Here "ambiguity" is not necessary, as we include all scenes (also the more or less ambiguous ones).
    Furthermore, "variety" is not necessary, as we directly give the allowed property values.

    This is a special case of 'create_distractor_configs' where we directly sample a scene. Here, we generate all
    possible scenes first. If we then choose randomly from the returned lists, then it's similar to sampling.

    :param piece_config: of the target to generate the scene for
    :param unique_props: that are necessary to identify the target
    :param num_distractors: that are within the context
    :param prop_values: that are allowed for the piece properties
    :return: all scenes configs (lists of piece configs)
    """
    if num_distractors < 1:
        raise Exception(f"There must be at least one distractor, but num_distractors is {num_distractors}")
    # When we have a single uniq prop, then all other pieces look the same except in that prop
    if len(unique_props) == 1:
        generator = SingleUPVDistractorSetGenerator(piece_config, list(unique_props)[0], num_distractors, prop_values)
        return generator.setup().generate_all_sets()
    return []


class SingleUPVDistractorSetGenerator:
    """ Single U(nique) P(roperty) V(alue) distractor set generator"""

    def __init__(self, target_piece: PieceConfig, unique_prop: PropertyNames,
                 num_distractors: int, prop_values: Dict[PropertyNames, List],
                 verbose: bool = False):
        if num_distractors < 1:
            raise Exception(f"There must be at least one distractor, but num_distractors is {num_distractors}")
        self.num_distractors = num_distractors
        self.target_piece = target_piece
        self.unique_prop = unique_prop
        self.prop_values = prop_values
        self.verbose = verbose
        self.distractor_configs = None

    def setup(self):
        if self.verbose:
            print("Setup generator")
            print("target_piece", self.target_piece)
            print("uniq_prop", self.unique_prop)
            print("prop_values", self.prop_values)
        self.prop_values = exclude_property_values(self.target_piece, {self.unique_prop}, self.prop_values)
        generator = DistractorConfigGenerator(self.prop_values)
        self.distractor_configs = generator.generate_all_distractor_configs()
        return self  # for fluent calls

    def _is_last_or_single(self, slots):
        return self.num_distractors == 1 or self.num_distractors == len(slots) + 1

    def _copy_target_config(self):
        return self.target_piece.copy()

    def generate_all_sets(self):
        if not self.distractor_configs:
            raise Exception("Call setup() first")
        return [s for s in self.yield_all_sets()]

    def yield_all_sets(self):
        if not self.distractor_configs:
            raise Exception("Call setup() first")
        yield from self._yield_distractor_config_sets([])

    def _yield_distractor_config_sets(self, slots: List):
        """
        :return: all sets of distractor piece configs (order matters)
        """
        if self._is_last_or_single(slots):  # if last or only one distractor
            # one distractor has to share all other properties, except unique one
            # for simplicity here, we choose the last distractor to do this
            unique_prop_values = self.prop_values[self.unique_prop]
            for prop_value in unique_prop_values:
                distractor_config = self._copy_target_config()
                distractor_config[self.unique_prop] = prop_value
                distractor_set = slots + [distractor_config]
                yield distractor_set
        else:
            # go through all possible property combinations
            # for this distractor at a specific slot position
            for distractor_config in self.distractor_configs:
                yield from self._yield_distractor_config_sets(slots + [distractor_config])


class DistractorConfigGenerator:

    def __init__(self, prop_values: Dict[PropertyNames, List], default_piece: PieceConfig = None):
        self.default_piece = PieceConfig()
        self.prop_values = prop_values
        if default_piece:
            self.default_piece = default_piece

    def _prop_names(self):
        return list(self.prop_values.keys())

    def _default_config(self):
        return self.default_piece.copy()

    def generate_all_distractor_configs(self):
        results = []
        self._recursive_add(self._prop_names(), self._default_config(), results)
        return results

    def _recursive_add(self, prop_names: List, piece_config: PieceConfig, results: List[PieceConfig]):
        """
        :return: all possible piece configs, given the property values
        """
        current_prop_name = prop_names[0]
        for prop_value in self.prop_values[current_prop_name]:
            piece_config[current_prop_name] = prop_value
            if len(prop_names) == 1:  # all property values are set
                results.append(piece_config.copy())  # defensive copy
            else:  # go further
                remaining_names = prop_names[1:]
                self._recursive_add(remaining_names, piece_config, results)


class PentoIncrementalAlgorithm:

    def __init__(self, preference_order: List[PropertyNames], start_tokens: List = None):
        """
        :param property_names: the order does matter! since first props rule more likely some distractors out in the
        first iteration and later props less likely rule out remaining distractors (if there are any left)
        e.g. the first prop might already rule out everything and the algorithm stops, though others would do the same
        """
        self.preference_order = preference_order
        self.general_types = ["piece"]
        self.start_tokens = ["Take", "Select", "Get"]
        if start_tokens:
            self.start_tokens = start_tokens

    def generate(self, piece_set: PieceConfigSet, selection: PieceConfig, is_selection_in_pieces=False,
                 return_expression=True):
        """
            pieces: a list of pieces (incl. the selection)
            selection: a selected pieces (within pieces)
        """
        distractors = set(piece_set.pieces)
        if is_selection_in_pieces:
            distractors.remove(selection)
        # property-value pairs are collected here
        properties = {}
        for property_name in self.preference_order:
            property_value = selection[property_name]
            # check what objects would be eliminated using this prop-val pair
            excluded_distractors = self._exclude(property_name, property_value, distractors)
            if property_value and len(excluded_distractors) > 0:
                # save the property
                properties[property_name] = property_value
                # update the contrast set
                for o in excluded_distractors:
                    distractors.remove(o)
            # check if enough properties have been collected to rule out all distractors
            if not len(distractors):
                if return_expression:
                    return self._verbalize_properties(properties), properties, True
                return properties, True
        # there might be a case where no properties have been found at all (all pieces are the same)
        # in that case we might want to mention all properties (instead of saying nothing)
        if len(properties) == 0:
            properties = dict([(pn, selection[pn]) for pn in list(PropertyNames)])
        if return_expression:
            return self._verbalize_properties(properties, False), properties, False
        return properties, False

    def _verbalize_properties(self, properties, is_discriminating=True):
        start_token = random.choice(self.start_tokens)
        shape = properties[PropertyNames.SHAPE] if PropertyNames.SHAPE in properties else random.choice(
            self.general_types)
        color = properties[PropertyNames.COLOR] if PropertyNames.COLOR in properties else ""
        pos = f"in the {properties[PropertyNames.REL_POSITION]}" if PropertyNames.REL_POSITION in properties else ""
        ref_exp = f"{color} {shape} {pos}".strip()  # strip whitespaces if s.t. is empty
        if is_discriminating:
            return f"{start_token} the {ref_exp}"
        return f"{start_token} one of the {ref_exp}"

    def _exclude(self, property_name: PropertyNames, selection_property_value, distractors: Set[PieceConfig]):
        """
         * Helper function for IA.
         * Params:
         * property_name - property name
         * selection_property_value - value the target object has assigned to the given property
         * distractors - contrast set of objects to rule out by the given properties
         * Returns:
         * array of contrast objects with a different value for prop
        """
        excluded_distractors = []
        for distractor in distractors:
            if distractor[property_name] != selection_property_value:
                excluded_distractors.append(distractor)
        return excluded_distractors
