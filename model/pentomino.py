from enum import Enum, auto
import random

from model.grid import Grid
from model.obj import Obj


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


class Colors(Enum):
    RED = ("red", "#ff0000")
    ORANGE = ("orange", "#ffa500")
    YELLOW = ("yellow", "#ffff00")
    GREEN = ("green", "#008000")
    BLUE = ("blue", "#0000ff")
    PURPLE = ("purple", "#800080")
    BROWN = ("brown", "#8b4513")
    GREY = ("grey", "#808080")

    def __init__(self, value_name, value_hex):
        self.value_name = value_name
        self.value_hex = value_hex


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

    def to_coords(self, board_width, board_height):
        width_splits, height_splits = board_width / 5, board_height / 5
        x_min, x_max = 0, board_width
        y_min, y_max = 0, board_height
        if self == RelPositions.TOP_LEFT:
            x_max = 2 * width_splits  # left
            y_max = 2 * height_splits  # top
        if self == RelPositions.TOP_CENTER:
            x_min = 2 * width_splits  # center width
            x_max = 3 * width_splits  # center width
            y_max = 2 * height_splits  # top
        if self == RelPositions.TOP_RIGHT:
            x_min = 3 * width_splits  # right
            y_max = 2 * height_splits  # top
        if self == RelPositions.CENTER_RIGHT:
            x_min = 3 * width_splits  # right
            y_min = 2 * height_splits  # center height
            y_max = 3 * height_splits  # center height
        if self == RelPositions.BOTTOM_RIGHT:
            x_min = 3 * width_splits  # right
            y_min = 3 * height_splits  # bottom
        if self == RelPositions.BOTTOM_CENTER:
            x_min = 2 * width_splits  # center width
            x_max = 3 * width_splits  # center width
            y_min = 3 * height_splits  # bottom
        if self == RelPositions.BOTTOM_LEFT:
            x_max = 2 * width_splits  # left
            y_min = 3 * height_splits  # bottom
        if self == RelPositions.CENTER_LEFT:
            x_max = 2 * width_splits  # left
            y_min = 2 * height_splits  # center height
            y_max = 3 * height_splits  # center height
        if self == RelPositions.CENTER:
            x_min = 2 * width_splits  # center width
            x_max = 3 * width_splits  # center width
            y_min = 2 * height_splits  # center height
            y_max = 3 * height_splits  # center height
        return random.randint(x_min, x_max), random.randint(y_min, y_max)

    @staticmethod
    def from_coords(x, y, board_width, board_height):
        width_splits, height_splits = board_width / 5, board_height / 5
        # x = obj.x + (obj.width / 2)
        # y = obj.y + (obj.height / 2)
        # TODO this actually looks wrong
        pos = None
        if y < 2 * height_splits:
            pos = RelPositions.TOP_CENTER
        elif y >= 3 * height_splits:
            pos = RelPositions.BOTTOM_CENTER
        if x < 2 * width_splits:
            if pos == RelPositions.TOP_CENTER:
                return RelPositions.TOP_LEFT
            if pos == RelPositions.BOTTOM_CENTER:
                return RelPositions.BOTTOM_LEFT
            return RelPositions.CENTER_LEFT
        elif x >= 3 * width_splits:
            if pos == RelPositions.TOP_CENTER:
                return RelPositions.TOP_RIGHT
            if pos == RelPositions.BOTTOM_CENTER:
                return RelPositions.BOTTOM_RIGHT
            return RelPositions.CENTER_RIGHT
        return RelPositions.CENTER


class PropertyNames(Enum):
    COLOR = "color"
    SHAPE = "shape"
    REL_POSITION = "rel_position"

    @classmethod
    def from_string(cls, name):
        for pn in list(cls):
            if pn.value == name:
                return pn
        return None


class PieceConfig:

    def __init__(self, color: Colors, shape: Shapes, rel_position: RelPositions):
        self.color = color
        self.shape = shape
        self.rel_position = rel_position

    def __getitem__(self, prop_name: PropertyNames):
        if prop_name == PropertyNames.COLOR:
            return self.color
        if prop_name == PropertyNames.SHAPE:
            return self.shape
        if prop_name == PropertyNames.REL_POSITION:
            return self.rel_position
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
        x, y = piece_config.rel_position.to_coords(board_width, board_height)
        piece_obj = Obj(piece_id,
                        obj_type=piece_config.shape.value_name,
                        x=x, y=y,
                        block_matrix=piece_config.shape.value_matrix,
                        color=piece_config.color.value_name)
        return cls(piece_id, piece_config, piece_obj)


class Board:

    def __init__(self, board_width, board_height):
        self.pieces = []
        self.grid = Grid(board_width, board_height, step=1, prevent_overlap=True)
        self.board_width = board_width
        self.board_height = board_height

    def add_pieces_from_configs(self, piece_configs: list[PieceConfig], max_attempts=100):
        for piece_config in piece_configs:
            self.add_piece_from_config(piece_config, max_attempts)

    def add_piece_from_config(self, piece_config: PieceConfig, max_attempts=100):
        for attempt in range(max_attempts):  # re-create with potentially different coords
            piece = Piece.from_config(len(self.pieces), piece_config, self.board_width, self.board_height)
            if self.grid.is_legal_position(piece.piece_obj.occupied(), piece.piece_id):
                self.grid.add_obj(piece.piece_obj)
                self.pieces.append(piece)
                return True
        print(f"Max attempts reached, cannot add piece {piece_config}")
        return False

    @classmethod
    def create_compositional(cls, board_width, board_height,
                             piece_config: PieceConfig,
                             unique_props: set[PropertyNames],
                             num_distractors: int = 1,
                             varieties: dict[PropertyNames, int] = None,
                             ambiguities: dict[PropertyNames, int] = None):
        distractors = create_distractor_configs(piece_config, unique_props, num_distractors, varieties, ambiguities)
        board = Board(board_width, board_height)
        board.add_piece_from_config(piece_config)
        board.add_pieces_from_configs(distractors)
        return board


def reduce_atoms(piece_config: PieceConfig, unique_props: set[PropertyNames], varieties: dict = None):
    """ Remove uniq prop atom from the sampling distribution """
    atoms = {
        PropertyNames.SHAPE: list(Shapes),
        PropertyNames.COLOR: list(Colors),
        PropertyNames.REL_POSITION: list(RelPositions)
    }
    for prop_name in unique_props:
        if len(atoms[prop_name]) < 2:
            raise Exception("Cannot discriminate on a property with less than 2 possible values")
        atoms[prop_name].remove(piece_config[prop_name])
        if varieties:
            prop_variety = varieties[prop_name]
            if prop_variety > 0:
                atoms[prop_name] = random.sample(atoms[prop_name], k=prop_variety)
    return atoms


def create_distractor_configs(piece_config: PieceConfig,
                              unique_props: set[PropertyNames],
                              num_distractors: int = 1,
                              varieties: dict[PropertyNames, int] = None,
                              ambiguities: dict[PropertyNames, int] = None):
    """
    :param piece_config:
    :param unique_props:
    :param num_distractors:
    :param varieties: the number of other different values for the props. Zero, means all available are used.
        Defaults to all available properties.
    :param ambiguities:
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
            for unique_prop in unique_props:
                if unique_prop in ambiguities:
                    raise Exception(f"Unique prop {unique_prop} must not be in ambiguities {ambiguities}.")
            # We allow a more fine-grained control on how many distractors share exactly the same "non-unique"
            # properties as the target piece (at least one piece must be still identical in "non-unique" props)
            differ_piece_configs = random.sample(distractor_configs, k=num_distractors - 1)
            atoms_reduced_non_unique = reduce_atoms(piece_config, non_unique_props, varieties)
            for ambiguous_prop, ambiguous_count in ambiguities.items():
                if ambiguous_count <= 0 or ambiguous_count >= num_distractors:
                    # all should look the same in "non-unique" props
                    break
                differ_count = len(differ_piece_configs)
                if ambiguous_count > 1:
                    differ_count = differ_count - ambiguous_count + 1  # one piece is always ambiguous
                differ_distractors = random.sample(differ_piece_configs, differ_count)
                for differ_distractor in differ_distractors:
                    differ_distractor[ambiguous_prop] = random.choice(atoms_reduced_non_unique[ambiguous_prop])
    return distractor_configs
