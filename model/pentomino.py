import copy
from enum import Enum, IntEnum
import random
from typing import List, Set, Dict, Tuple

from collections import defaultdict

from grid import Grid, GridConfig
from obj import Obj

import numpy as np
from matplotlib import pyplot as plt
from matplotlib import colors as plt_colors

from state import State


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

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.value == other.value
        return False

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
        return str(self.value)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.value == other.value
        return False

    def __lt__(self, other):
        return self.value.__lt__(other.value)

    def to_json(self):
        return self.value

    @classmethod
    def from_random(cls):
        possible_rotations = list(cls)
        return random.choice(possible_rotations)

    @classmethod
    def from_json(cls, value):
        return cls[f"DEGREE_{value}"]


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

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.value_name == other.value_name
        return False

    def __lt__(self, other):
        return self.value_name.__lt__(other.value_name)

    def to_tuple(self):
        return tuple(self.value)

    @classmethod
    def from_tuple(cls, t):
        return cls.from_json(t[0])

    def to_json(self):
        return self.value_name

    @classmethod
    def from_json(cls, value_name):
        return cls[value_name.upper().replace(" ", "_")]


class RelPositions(Enum):
    TOP_LEFT = "top left"
    TOP_CENTER = "top center"
    TOP_RIGHT = "top right"
    RIGHT_CENTER = "right center"
    BOTTOM_RIGHT = "bottom right"
    BOTTOM_CENTER = "bottom center"
    BOTTOM_LEFT = "bottom left"
    LEFT_CENTER = "left center"
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

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.value == other.value
        return False

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
        if self == RelPositions.RIGHT_CENTER:
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
        if self == RelPositions.LEFT_CENTER:
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
            return RelPositions.LEFT_CENTER
        elif x >= 2 * width_step:
            if pos == RelPositions.TOP_CENTER:
                return RelPositions.TOP_RIGHT
            if pos == RelPositions.BOTTOM_CENTER:
                return RelPositions.BOTTOM_RIGHT
            return RelPositions.RIGHT_CENTER
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

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.value == other.value
        return False

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
        raise ValueError(f"Other is not {self.__class__} but {other.__class__}")

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
        groups = defaultdict(list)
        for piece in pieces:
            groups[piece.rel_position].append(piece)
        # print("group_by_pos", [len(groups[p]) for p in groups])
        return groups

    @staticmethod
    def group_by_color(pieces: List):
        groups = defaultdict(list)
        for piece in pieces:
            groups[piece.color].append(piece)
        # print("group_by_color", [len(groups[p]) for p in groups])
        return groups

    @staticmethod
    def group_by_shape(pieces: List):
        groups = defaultdict(list)
        for piece in pieces:
            groups[piece.shape].append(piece)
        # print("group_by_shape", [len(groups[p]) for p in groups])
        return groups


class PieceConfigGroup:

    def __init__(self, pieces: List[PieceConfig]):
        self.pieces = pieces  # allow duplicates and preserve order

    def __getitem__(self, item):
        return self.pieces[item]

    def __repr__(self):
        return f"PCG{self.pieces}"

    def __str__(self):
        return f"({self.pieces})"

    def __iter__(self):
        return self.pieces.__iter__()

    def __len__(self):
        return len(self.pieces)

    def __key(self):
        return tuple(sorted(self.pieces))  # we ignore order for comparison

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if isinstance(other, PieceConfigGroup):
            return self.__key() == other.__key()
        raise ValueError(f"Other is not {self.__class__} but {other.__class__}")

    def to_json(self):
        return [p.to_json() for p in self.pieces]

    @classmethod
    def from_json(cls, pieces: List):
        return cls([PieceConfig.from_json(p) for p in pieces])


class RestrictivePieceConfigGroupSampler:

    def __init__(self, pieces: List[PieceConfig], pieces_per_pos: int = 2):
        """

        :param pieces: without the target_piece
        """
        self.pieces_per_pos = pieces_per_pos
        self.pieces_by_color: Dict[Colors, List[PieceConfig]] = PieceConfig.group_by_color(pieces)
        self.pieces_by_shape: Dict[Shapes, List[PieceConfig]] = PieceConfig.group_by_shape(pieces)
        self.pieces_by_pos: Dict[RelPositions, List[PieceConfig]] = PieceConfig.group_by_pos(pieces)
        self.meta = {
            PropertyNames.COLOR: self.pieces_by_color,
            PropertyNames.SHAPE: self.pieces_by_shape,
            PropertyNames.REL_POSITION: self.pieces_by_pos,
        }

    def __check_allowed_positions(self, allowed_positions, n_pieces):
        num_pos = len(allowed_positions)
        num_possible = self.pieces_per_pos * num_pos
        if num_possible < n_pieces:
            raise Exception(f"with pieces_per_pos={self.pieces_per_pos} and num_pos={num_pos} "
                            f"there can be maximal n_pieces={num_possible} in the set")

    def __check_and_get_allowed_positions(self, n_pieces):
        allowed_positions = list(self.pieces_by_pos.keys())  # all positions, where there are pieces for
        self.__check_allowed_positions(allowed_positions, n_pieces)
        return allowed_positions

    def __check_and_reduce(self, allowed_positions, pos_counts):
        for pos, counts in pos_counts.items():
            if counts >= self.pieces_per_pos:
                if pos in allowed_positions:
                    allowed_positions.remove(pos)

    def sample_special(self, target_piece: PieceConfig, n_pieces: int):
        """
        color,shape,position:
                    1 x Share(color), 1 Share(shape), Diff(pos)
                    1 x Share(color), 1 Diff(shape), Diff(pos),
                 others Any(color), Any(shape), Any(pos)
        """
        # hierarchical sampling:
        # 1. sample position (so we can block certain positions if drawn already twice)
        # 2. sample piece on position
        if n_pieces < 3:
            print(f"Warn: (color,shape,position) requires at least 3 distractors, but only {n_pieces} given. "
                  "Otherwise it will reduce to (shape,position).")

        allowed_positions = self.__check_and_get_allowed_positions(n_pieces)
        pos_counts = dict([(pos, 0) for pos in allowed_positions])

        piece_set = []

        # one dist must share color and shape, otherwise IA stops already
        possible_pieces = self.pieces_by_color[target_piece.color]
        possible_pieces = [p for p in possible_pieces if p.shape == target_piece.shape]
        possible_pieces = [p for p in possible_pieces if p.rel_position != target_piece.rel_position]
        piece = random.choice(possible_pieces)
        pos_counts[piece.rel_position] += 1
        piece_set.append(piece)

        # one dist must share color, but not shape, so that shape must be mentioned
        possible_pieces = self.pieces_by_color[target_piece.color]
        possible_pieces = [p for p in possible_pieces if p.shape != target_piece.shape]
        possible_pieces = [p for p in possible_pieces if p.rel_position != target_piece.rel_position]
        piece = random.choice(possible_pieces)
        pos_counts[piece.rel_position] += 1
        piece_set.append(piece)

        if n_pieces <= 2:  # we are already finished (this is only (shape,position) though)
            return PieceConfigGroup(piece_set)

        # remove already, if we have reached the limit at a pos
        self.__check_and_reduce(allowed_positions, pos_counts)

        # other piece have any shape and position, but not color, so that color must be mentioned
        # Note: target piece is not in pieces already
        for _ in range(n_pieces - 2):
            pos = random.choice(allowed_positions)
            possible_pieces = self.pieces_by_pos[pos]
            possible_pieces = [p for p in possible_pieces if p.color != target_piece.color]
            piece = random.choice(possible_pieces)
            piece_set.append(piece)
            pos_counts[piece.rel_position] += 1
            self.__check_and_reduce(allowed_positions, pos_counts)
        return PieceConfigGroup(piece_set)

    def sample_some_with_prop1_and_position(self, target_piece: PieceConfig, prop1: PropertyNames, n_pieces: int):
        # hierarchical sampling:
        # 1. sample position (so we can block certain positions if drawn already twice)
        # 2. sample piece on position
        # Note: if you dont need this, simply use random.sample(n,k)
        piece_set = []

        # exactly on with the same position, but different prop
        possible_pieces = self.pieces_by_pos[target_piece.rel_position]
        possible_pieces = [p for p in possible_pieces if p[prop1] != target_piece[prop1]]
        piece1 = random.choice(possible_pieces)
        piece_set.append(piece1)

        # others with same prop, but different position
        possible_pieces = self.meta[prop1][target_piece[prop1]]
        possible_pieces = [p for p in possible_pieces if p.rel_position != target_piece.rel_position]
        possible_pieces_by_pos = PieceConfig.group_by_pos(possible_pieces)

        # positions are defined by the other possible pieces that do not share the target piece position
        allowed_positions = [p.rel_position for p in possible_pieces]
        pos_counts = dict([(pos, 0) for pos in allowed_positions])

        for _ in range(n_pieces - 1):
            pos = random.choice(allowed_positions)
            piece = random.choice(possible_pieces_by_pos[pos])
            piece_set.append(piece)
            pos_counts[piece.rel_position] += 1
            self.__check_and_reduce(allowed_positions, pos_counts)
        return PieceConfigGroup(piece_set)

    def __get_same_but_diff(self, target_piece: PieceConfig,
                            same_prop: PropertyNames, diff_prop: PropertyNames, pos):
        possible_pieces = self.meta[same_prop][target_piece[same_prop]]
        possible_pieces = [p for p in possible_pieces if p[diff_prop] != target_piece[diff_prop]]
        possible_pieces = [p for p in possible_pieces if p.rel_position == pos]
        if not possible_pieces:
            print("target_piece:", target_piece)
            print("same_prop:", same_prop)
            print("diff_prop:", diff_prop)
            print("pos:", pos)
            print(self.meta[same_prop][target_piece[same_prop]])
        return possible_pieces

    def sample_some_with_prop1_and_prop2(self, target_piece: PieceConfig, prop1: PropertyNames, prop2: PropertyNames,
                                         n_pieces: int):
        # hierarchical sampling:
        # 1. sample position (so we can block certain positions if drawn already twice)
        # 2. sample piece on position
        # Note: if you dont need this, simply use random.sample(n,k)
        allowed_positions = self.__check_and_get_allowed_positions(n_pieces)
        pos_counts = dict([(pos, 0) for pos in allowed_positions])
        piece_set = []
        # select at least one, but never all for the first property
        split_size = random.randint(1, n_pieces - 1)
        for _ in range(split_size):
            pos = random.choice(allowed_positions)
            possible_pieces = self.__get_same_but_diff(target_piece, prop1, prop2, pos)
            piece = random.choice(possible_pieces)
            piece_set.append(piece)
            pos_counts[piece.rel_position] += 1
            self.__check_and_reduce(allowed_positions, pos_counts)
        # select the remaining ones for the second property
        for _ in range(n_pieces - split_size):
            pos = random.choice(allowed_positions)
            possible_pieces = self.__get_same_but_diff(target_piece, prop2, prop1, pos)
            piece = random.choice(possible_pieces)
            piece_set.append(piece)
            pos_counts[piece.rel_position] += 1
            self.__check_and_reduce(allowed_positions, pos_counts)
        return PieceConfigGroup(piece_set)

    def sample_with_position_restriction(self, n_pieces: int, disallow_pos: List[RelPositions] = None):
        # hierarchical sampling:
        # 1. sample position (so we can block certain positions if drawn already twice)
        # 2. sample piece on position
        # Note: if you dont need this, simply use random.sample(n,k)
        allowed_positions = self.__check_and_get_allowed_positions(n_pieces)
        # if we allow all positions, but there are only pieces of the same shape and color
        # then there will be no pieces available at the target piece position e.g. for position-only utterances
        for pos in disallow_pos:
            if pos in allowed_positions:
                allowed_positions.remove(pos)
        pos_counts = dict([(pos, 0) for pos in allowed_positions])
        piece_set = []
        for _ in range(n_pieces):
            pos = random.choice(allowed_positions)
            possible_pieces = self.pieces_by_pos[pos]
            piece = random.choice(possible_pieces)
            piece_set.append(piece)
            pos_counts[piece.rel_position] += 1
            self.__check_and_reduce(allowed_positions, pos_counts)
        return PieceConfigGroup(piece_set)


class UtteranceTypeOrientedDistractorSetSampler:

    def __init__(self, pieces: List[PieceConfig], target_piece: PieceConfig, n_retries=100):
        self.n_retries = n_retries
        # remove the target from the piece set
        self.pieces = list(pieces)
        self.pieces.remove(target_piece)
        # group pieces by their property values
        pieces_by_value = defaultdict(list)
        for piece in self.pieces:
            for pn in list(PropertyNames):
                pieces_by_value[piece[pn]].append(piece)
        self.pieces_by_value = pieces_by_value
        self.target_piece = target_piece

    def sample_many_distractor_groups(self, utterance_type, n_sets, pieces_per_set, verbose=False, rotate_pieces=False):
        n_min, n_max = pieces_per_set[0], pieces_per_set[1]
        distractors_sets = set()
        retries = 0
        while len(distractors_sets) < n_sets and retries < self.n_retries:
            set_size = random.randint(n_min, n_max) - 1  # already 1 reserved for target piece
            distractor_set = self.create_distractor_configs_csp(unique_props=set(utterance_type),
                                                                num_distractors=set_size)
            if rotate_pieces:
                for d in distractor_set:
                    d.rotation = Rotations.from_random()
            if distractor_set in distractors_sets:  # avoid duplicates (if sample space is small)
                retries += 1
                continue
            distractors_sets.add(distractor_set)
        if verbose and len(distractors_sets) < n_sets:
            print("Warn: Too many duplicates. Sampled sets:", len(distractors_sets))
        if verbose and retries > 0:
            print("Warn: Retries", retries)
        return distractors_sets

    def create_distractor_configs_csp(self, unique_props: Set[PropertyNames], num_distractors: int = 1):
        """
        Note: The preference order is fix [PropertyNames.COLOR, PropertyNames.SHAPE, PropertyNames.REL_POSITION]

        So, if we want to generate distractors for

            color:    any other distractor, but different colors
                        Diff(color), Any(shape), Any(pos)
            shape:    all having the same color (no exclusions), but different shapes; random positions
                        All(color), Diff(shape), Any(pos)
            position: all having the same color and shape (no exclusions), but different positions
                        All(color), All(shape), Diff(pos)

            color,shape:    at least one (and never all) distractor shares the color or the shape
                        Some(color), Some(shape), Any(pos)
            color,position: at least one (and never all) distractor shares the color or the position; all same shapes
                        Some(color), All(shape), Some(pos)
            shape,position: at least one (and never all) distractor shares the shape or the position; all same color
                        All(color), Some(shape), Some(pos)

            color,shape,position:
                        Some(color), Some(shape), Some(pos)

        :return:
        """
        if num_distractors < 1:
            raise Exception(f"There must be at least one distractor, but num_distractors is {num_distractors}")

        # When we have a single uniq prop, then all other pieces are disallowed to have that prop
        if len(unique_props) == 1:
            unique_prop = list(unique_props)[0]
            disallowed_positions = []
            """
            color:    any other distractor, but different colors
                        Diff(color), Any(shape), Any(pos)
            """
            if unique_prop == PropertyNames.COLOR:
                # all pieces which do not share the same color
                possible_distractors = [piece for piece in self.pieces if piece.color != self.target_piece.color]

            """
            shape:    all having the same color (no exclusions), but different shapes; random positions
                        All(color), Diff(shape), Any(pos)
            """
            if unique_prop == PropertyNames.SHAPE:
                possible_distractors = self.pieces_by_value[self.target_piece.color]
                possible_distractors = [piece for piece in possible_distractors
                                        if piece.shape != self.target_piece.shape]

            """
            position: all having the same color and shape (no exclusions), but different positions
                        All(color), All(shape), Diff(pos)
            """
            if unique_prop == PropertyNames.REL_POSITION:
                possible_distractors = self.pieces_by_value[self.target_piece.color]
                possible_distractors = [piece for piece in possible_distractors
                                        if piece.shape == self.target_piece.shape]
                possible_distractors = [piece for piece in possible_distractors
                                        if piece.rel_position != self.target_piece.rel_position]
                disallowed_positions.append(self.target_piece.rel_position)

            sampler = RestrictivePieceConfigGroupSampler(possible_distractors)
            return sampler.sample_with_position_restriction(num_distractors, disallow_pos=disallowed_positions)

        if len(unique_props) == 2:
            """
            color,shape:    at least one (and never all) distractor shares the color or the shape
                        Some(color), Some(shape), Any(pos)
            """
            if PropertyNames.COLOR in unique_props and PropertyNames.SHAPE in unique_props:
                sampler = RestrictivePieceConfigGroupSampler(self.pieces)
                return sampler.sample_some_with_prop1_and_prop2(self.target_piece,
                                                                PropertyNames.COLOR,
                                                                PropertyNames.SHAPE,
                                                                n_pieces=num_distractors)
            """
            color,position: at least one (and never all) distractor shares the color or the position; all same shapes
                        Some(color), All(shape), Some(pos)
            """
            if PropertyNames.COLOR in unique_props and PropertyNames.REL_POSITION in unique_props:
                possible_distractors = self.pieces_by_value[self.target_piece.shape]
                sampler = RestrictivePieceConfigGroupSampler(possible_distractors)
                return sampler.sample_some_with_prop1_and_position(self.target_piece,
                                                                   PropertyNames.COLOR,
                                                                   n_pieces=num_distractors)
            """
            shape,position: at least one (and never all) distractor shares the shape or the position; all same color
                        All(color), Some(shape), Some(pos)
            """
            if PropertyNames.SHAPE in unique_props and PropertyNames.REL_POSITION in unique_props:
                possible_distractors = self.pieces_by_value[self.target_piece.color]
                sampler = RestrictivePieceConfigGroupSampler(possible_distractors)
                return sampler.sample_some_with_prop1_and_position(self.target_piece,
                                                                   PropertyNames.SHAPE,
                                                                   n_pieces=num_distractors)

        if len(unique_props) == 3:
            """
            color,shape,position:
                        1 x Share(color), 1 Share(shape), Diff(pos)
                        1 x Share(color), 1 Diff(shape), Diff(pos), 
                     others Any(color), Any(shape), Any(pos)
            """
            sampler = RestrictivePieceConfigGroupSampler(self.pieces)
            return sampler.sample_special(self.target_piece, n_pieces=num_distractors)


class Piece:

    def __init__(self, piece_id: int, piece_config: PieceConfig, piece_obj: Obj):
        self.piece_obj = piece_obj
        self.piece_config = piece_config
        self.piece_id = piece_id

    def __repr__(self):
        return f"{self.piece_id}, {repr(self.piece_config)}"

    def __str__(self):
        return f"{self.piece_id}, {repr(self.piece_config)}"

    @classmethod
    def from_config(cls, piece_id, piece_config, board_width, board_height):
        x, y = piece_config.rel_position.to_random_coords(board_width, board_height)
        shape_matrix = ShapesMatrix[piece_config.shape.value]
        piece_obj = Obj(piece_id,
                        obj_type=piece_config.shape.value,
                        x=x, y=y,
                        block_matrix=shape_matrix.value,
                        color=piece_config.color.to_tuple())  # (name, hex, rgb)
        if piece_config.rotation:
            piece_obj.rotate(piece_config.rotation.value)
        return cls(piece_id, piece_config, piece_obj)


class BoardPlotContext:

    def __init__(self, image_size: Tuple[int]):
        fig_size = (image_size[0] / 100, image_size[1] / 100)
        self.fig, self.ax = plt.subplots(figsize=fig_size, dpi=100)
        self.image_context = None
        self.ax.tick_params(axis="both", which="both", bottom=False, top=False, left=False, right=False,
                            labelbottom=False, labelleft=False)
        self.ax.axis('off')

    def draw_board(self, np_board, obj_colors, bounds, verbose=False):
        ax = self.ax
        if verbose:
            print("Get borders and eliminate seams within them")
        borders = self.__get_borders(np_board)
        l_borders = self.__find_long(borders)
        if verbose:
            print("Plot borders of all objects")
        for x, y in l_borders:
            ax.plot(x, y, scaley=False, linestyle="-", linewidth=.5, color="black")
        if verbose:
            print("Plot image")
        cmap = plt_colors.ListedColormap([o[1] for o in obj_colors])
        norm = plt_colors.BoundaryNorm(bounds, cmap.N)
        if self.image_context:
            self.image_context.set_data(np_board)
        else:
            # lazy init of the image_context for later re-use
            self.image_context = ax.imshow(np_board)
        self.image_context.set_cmap(cmap)
        self.image_context.set_norm(norm)
        if verbose:
            print("remove labels and ticks on edges")
        if verbose:
            print("Draw Canvas")
        # This must happen here otherwise we have color artifacts
        self.fig.tight_layout(pad=0)
        ax.figure.canvas.draw()
        if verbose:
            print("Get the RGBA buffer from the figure")
        w, h = self.fig.canvas.get_width_height()
        buf = np.frombuffer(self.fig.canvas.tostring_rgb(), dtype=np.uint8).reshape(w, h, 3)
        del cmap
        del norm
        ax.lines.clear()  # remove borders for next plot
        return buf

    def close(self):
        plt.cla()
        plt.clf()
        plt.close(self.fig)

    def __get_borders(self, np_board: np.array, to_add=0.5):
        """ iterate over the the 2D array (from get_matrix) and detect borders """
        lines = list()
        for y, row in enumerate(np_board):
            for x, tile in enumerate(row):
                if tile != 0:
                    output_list = lines
                    # upper bound
                    if y == 0 or np_board[y - 1][x] != tile:
                        this_line = (
                            (x - to_add, x + to_add),
                            (y - to_add, y - to_add),
                        )
                        output_list.append(this_line)
                    # lower bound
                    if y == len(np_board) - 1 or np_board[y + 1][x] != tile:
                        this_line = (
                            (x - to_add, x + to_add),
                            (y + to_add, y + to_add),
                        )
                        output_list.append(this_line)
                    # right bound
                    if x == len(np_board[0]) - 1 or np_board[y][x + 1] != tile:
                        this_line = (
                            (x + to_add, x + to_add),
                            (y - to_add, y + to_add),
                        )
                        output_list.append(this_line)
                    # left bound
                    if x == 0 or np_board[y][x - 1] != tile:
                        this_line = (
                            (x - to_add, x - to_add),
                            (y - to_add, y + to_add),
                        )
                        output_list.append(this_line)
        return lines

    def __find_long(self, coord):
        """
        reconstruct long borders to avoid seam lines
        in objects black borders
        """
        h_lines = dict()
        v_lines = dict()
        results = list()

        # save lines in dictionaries
        for x, y in coord:
            # vertical line
            if len(set(x)) == 1:
                if x[0] not in v_lines:
                    v_lines[x[0]] = set()
                v_lines[x[0]].add(y)

            # horizontal line
            elif len(set(y)) == 1:
                if y[0] not in h_lines:
                    h_lines[y[0]] = set()
                h_lines[y[0]].add(x)
        # reconstruct longest lines from each entry
        # in horizontal dictionary
        for y, complete_line in h_lines.items():
            complete_line = list(complete_line)
            complete_line.sort()
            begin, end = complete_line[0]
            i = 1
            if len(complete_line) == 1:
                results.append((complete_line[0], (y, y)))
            else:
                # iterate over the list and reconstruct the longest lines
                while i < len(complete_line):
                    this_b, this_e = complete_line[i]
                    if end == this_b:
                        # lines continues, update end
                        end = this_e
                        # last element, save
                        if i == len(complete_line) - 1:
                            results.append(((begin, end), (y, y)))
                    else:
                        # end of line
                        results.append(((begin, end), (y, y)))
                        begin, end = complete_line[i]
                    i += 1
        # reconstruct longest lines from each entry
        # in horizontal dictionary
        for x, complete_line in v_lines.items():
            complete_line = list(complete_line)
            complete_line.sort()
            begin, end = complete_line[0]
            i = 1
            if len(complete_line) == 1:
                results.append(((x, x), complete_line[0]))
            else:
                # iterate over the list and reconstruct the longest lines
                while i < len(complete_line):
                    this_b, this_e = complete_line[i]
                    if end == this_b:
                        # lines continues
                        end = this_e
                        # last element, save
                        if i == len(complete_line) - 1:
                            results.append(((x, x), (begin, end)))
                    else:
                        # end of line
                        results.append(((x, x), (begin, end)))
                        begin, end = complete_line[i]
                    i += 1
        return results


class Board:

    def __init__(self, grid_config: GridConfig, board_id=None):
        self.board_id = board_id
        self.pieces = []
        self.pieces_by_id = {}
        self.grid = Grid.create_from_config(grid_config)
        self.board_width = grid_config.width
        self.board_height = grid_config.height

    def __get_objs_by_id(self):
        return dict([(p.piece_obj.id_n, p.piece_obj) for p in self.pieces])

    def to_state(self):
        grid_config = self.grid.get_grid_config()
        objs = self.__get_objs_by_id()
        state = State(objs=objs, grippers=dict(), targets=dict(), grid_config=grid_config, state_id=self.board_id)
        return state

    def to_state_dict(self, include_grid_config=False):
        state_dict = dict()
        state_dict["state_id"] = self.board_id
        state_dict["grippers"] = {}
        state_dict["objs"] = dict([(p.piece_obj.id_n, p.piece_obj.to_dict()) for p in self.pieces])
        state_dict["targets"] = {}
        if include_grid_config:
            state_dict["grid_config"] = self.grid.get_grid_config().to_dict()
        return state_dict

    def to_rgb_array(self):
        color_grid = []
        for row in self.grid:
            color_row = []
            for tile in row:
                tile_color = [255, 255, 255]  # white
                if tile.objects:
                    obj_id = tile.objects[0].id_n
                    tile_color = self.get_piece(obj_id).piece_config.color.value_rgb
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

    def to_image_array(self, image_size, ctx: BoardPlotContext = None, verbose=False):
        """ convert a state to an RGB numpy array """
        if verbose:
            print("Get Matrix")
        np_board, obj_colors, color_dict, bounds = self.__get_matrix()
        if verbose:
            print("Create Figure")
        if ctx:
            return ctx.draw_board(np_board, obj_colors, bounds)
        ctx = BoardPlotContext(image_size)
        image = ctx.draw_board(np_board, obj_colors, bounds)
        ctx.close()
        return image

    def __get_matrix(self) -> (np.array, List, Dict, List):
        """
        given a state, a 2D numpy array is created where each object and target
        is identified by a unique number which is then used to assign
        it its colour. this is then used to generate a heatmap which represents
        the plotted state.
        """
        x_dim = self.grid.width * self.grid.converter.multiplier
        y_dim = self.grid.height * self.grid.converter.multiplier
        # initialize variables to plot the grid
        data = np.zeros((x_dim, y_dim))
        obj_colors = [("white", "#FFFFFF", [255, 255, 255])]
        bounds = [-10, 0.5]
        color_dict = {0: ("white", "#FFFFFF", [255, 255, 255])}
        val = 1
        # plot objects
        val += 1
        for i, obj in enumerate([p.piece_obj for p in self.pieces]):
            val += i
            bounds.append(val + 0.5)
            obj_colors.append(obj.color)
            color_dict[val] = obj.color
            self.__draw_obj(obj, data, val)
        return data, obj_colors, color_dict, bounds

    def __draw_obj(self, obj: Obj, data: np.array, fill_value: int):
        """
        draw a single object on a 2D grid with a unique fillvalue
        """
        for y, row in enumerate(obj.block_matrix):
            for x, tile in enumerate(row):
                if tile == 1:
                    # convert coordinates with converter!
                    for new_c in self.grid.converter({"x": x + obj.x, "y": y + obj.y}):
                        this_x = new_c["x"]
                        this_y = new_c["y"]

                        grid_x = int(this_x)
                        grid_y = int(this_y)
                        data[grid_y][grid_x] = fill_value

    def get_bbox(self, image_width: int, image_height: int, piece: Piece):
        """
        given the RGB np.array of the state and the object dictionary,
        slice the state to create a small image of size len(block_matrix)
        """
        x_factor = image_width / self.grid.width
        y_factor = image_height / self.grid.height
        obj = piece.piece_obj
        min_y = len(obj.block_matrix)
        min_x = len(obj.block_matrix[0])
        max_y = 0
        max_x = 0
        for y, row in enumerate(obj.block_matrix):
            for x, tile in enumerate(row):
                if tile == 1:
                    # update upper-left corner
                    if y < min_y:
                        min_y = y
                    if x < min_x:
                        min_x = x
                    # update upper-right corner
                    if y > max_y:
                        max_y = y
                    if x > max_x:
                        max_x = x
        this_x = (obj.x + min_x) * x_factor
        this_y = (obj.y + min_y) * y_factor
        x_limit = (obj.x + max_x + 1) * x_factor
        y_limit = (obj.y + max_y + 1) * y_factor
        return int(this_x), int(x_limit), int(this_y), int(y_limit)

    @classmethod
    def create_compositional_from_configs(cls, board_width, board_height,
                                          piece_config: PieceConfig, distractor_group: PieceConfigGroup):
        board = Board(board_width, board_height)
        # TODO this is just a quick and dirty hack
        piece_config[PropertyNames.ROTATION] = Rotations.from_random()
        for d in distractor_group:
            d[PropertyNames.ROTATION] = Rotations.from_random()
        board.add_piece_from_config(piece_config)
        board.add_pieces_from_configs(distractor_group.pieces)
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

    def generate(self, pcl: PieceConfigGroup, selection: PieceConfig, is_selection_in_pieces=False,
                 return_expression=True):
        """
            pieces: a list of pieces (incl. the selection)
            selection: a selected pieces (within pieces)
        """
        distractors = set(pcl.pieces)
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
