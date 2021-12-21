from enum import Enum, auto
import random

from model.obj import Obj


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
    TOP = "top"
    TOP_RIGHT = "top right"
    RIGHT = "right"
    BOTTOM_RIGHT = "bottom right"
    BOTTOM = "bottom"
    BOTTOM_LEFT = "bottom left"
    LEFT = "left"
    CENTER = "center"

    @staticmethod
    def from_coords(x, y, board_width, board_height):
        # x = obj.x + (obj.width / 2)
        # y = obj.y + (obj.height / 2)
        pos = None
        if y < 2 * board_height / 5:
            pos = RelPositions.TOP
        elif y >= 3 * board_height / 5:
            pos = RelPositions.BOTTOM
        if x < 2 * board_width / 5:
            if pos == RelPositions.TOP:
                return RelPositions.TOP_LEFT
            if pos == RelPositions.BOTTOM:
                return RelPositions.BOTTOM_LEFT
            return RelPositions.LEFT
        elif x >= 3 * board_width / 5:
            if pos == RelPositions.TOP:
                return RelPositions.TOP_RIGHT
            if pos == RelPositions.BOTTOM:
                return RelPositions.BOTTOM_RIGHT
            return RelPositions.RIGHT
        return RelPositions.CENTER


class PropertyNames(Enum):
    COLOR = auto()
    SHAPE = auto()
    REL_POSITION = auto()


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


class Piece(Obj):

    def __init__(self, id_n, obj_type, x, y, block_matrix, color):
        super().__init__(id_n, obj_type, x, y, block_matrix=block_matrix, color=color)


class PieceGenerator:
    """
        Creates pieces randomly or based on a piece config.

        Note: Positions are generated in disregard of other pieces.
    """

    def __init__(self, config):
        self.config = config

    def create_piece(self, piece_config: PieceConfig):
        ...


class Board:
    ...


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


class CompositionalSceneGenerator:
    """
        Generates a scene, where objects differ on a controlled compositional basis.
        For example, the objects might differ in "color" but not in "shape".
    """

    def __init__(self, config, varieties: dict = None, ambiguities: dict = None):
        """
        :param varieties: dict of ("prop_name",int) with the number of other different values for the unique_props.
        Zero, means all available are used. Defaults to all available properties.
        :param ambiguities: dict of ("prop_name",int) applied, when there is more than 1 unique property.
        Zero, means all other pieces share a property with the piece. Defaults to all shared.
        For "position" it's always 1 (otherwise there might be too many pieces in a corner).
        """
        self.config = config
        self.board_width = config.width
        self.board_height = config.height
        self.varieties = dict([(p, 0) for p in PropertyNames])
        if varieties:  # overwrite defaults
            for k in varieties:
                self.varieties[k] = varieties[k]
        self.ambiguities = dict([(p, 0) for p in PropertyNames])
        if ambiguities:  # overwrite defaults
            for k in ambiguities:
                self.ambiguities[k] = ambiguities[k]
        # For "position" it's always 1 (otherwise there might be too many pieces in a corner).
        self.ambiguities["position"] = 1

    def place_pieces(self, board: Board, piece: Obj, unique_props: list[str], distractors: list[Obj]):
        ...

    def generate_scene(self, board: Board, piece: Obj, unique_props: list[str], num_distractors: int = 1):
        """
        :param board: where to establish the scene
        :param piece: based on which the scene will be generated
        :param unique_props: define the props that should uniquely identify the given piece. The order matters,
        because when there is more than one unique property, then the later ones come last. Must be either or
        a combination of ["color", "shape", "position"]
        :param num_distractors: the number of other pieces in the scene
        :return:
        """
        distractors = self.create_distractors(piece, unique_props, num_distractors)
        self.place_pieces(board, piece, unique_props, distractors)
        return board
