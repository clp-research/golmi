from enum import Enum
from typing import List, Dict, Tuple

import numpy as np
from matplotlib import pyplot as plt
from matplotlib import colors as plt_colors

from contrib.pentomino.symbolic.types import PieceConfig, Colors, Shapes, RelPositions, Rotations
from model.grid import GridConfig, Grid
from model.obj import Obj
from model.state import State


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


class Piece:
    """ A pentomino specific wrapper around GOLMi Obj """

    def __init__(self, piece_id: int, piece_config: PieceConfig, piece_obj: Obj):
        """ Todo: consider to loose the relation between piece_obj (realisation) and piece_config (symbol)"""
        self.piece_obj = piece_obj
        self.piece_config = piece_config
        self.piece_id = piece_id

    def __repr__(self):
        return f"{self.piece_id}, {repr(self.piece_config)}"

    def __str__(self):
        return f"{self.piece_id}, {repr(self.piece_config)}"

    @classmethod
    def from_dict(cls, obj_dict, grid_config: GridConfig = None):
        piece_obj = Obj.from_dict(obj_dict["id_n"], obj_dict)
        piece_id = piece_obj.id_n
        piece_config = None
        if grid_config:  # we can only know the position, when we know the board size
            piece_config = PieceConfig(Colors.from_tuple(piece_obj.color),
                                       Shapes.from_json(piece_obj.type),
                                       RelPositions.from_coords(piece_obj.x, piece_obj.y,
                                                                grid_config.width, grid_config.height),
                                       Rotations.from_json(int(piece_obj.rotation)))
        return cls(piece_id, piece_config, piece_obj)

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

    def add_piece(self, piece: Piece, check_position=False):
        if check_position and not self.grid.is_legal_position(piece.piece_obj.occupied(), piece.piece_id):
            print("Warning: Piece position is already occupied")
        self.grid.add_obj(piece.piece_obj)
        self.pieces.append(piece)
        self.pieces_by_id[piece.piece_id] = piece

    def add_pieces_from_configs(self, piece_configs: List[PieceConfig], max_attempts=100):
        all_success = True
        for piece_config in piece_configs:
            if not self.add_piece_from_config(piece_config, max_attempts):
                all_success = False
        return all_success

    def add_piece_from_config(self, piece_config: PieceConfig, max_attempts=100):
        for attempt in range(max_attempts):  # re-create with potentially different coords
            piece = Piece.from_config(len(self.pieces), piece_config, self.board_width, self.board_height)
            if self.grid.is_legal_position(piece.piece_obj.occupied(), piece.piece_id):
                self.add_piece(piece)
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
    def from_state_dict(cls, state_dict, grid_config: GridConfig = None, check_piece_position: bool = False):
        board_id = None
        if "state_id" in state_dict:
            board_id = state_dict["state_id"]
        if grid_config is None and "grid_config" in state_dict:
            grid_config = GridConfig.from_dict(state_dict["grid_config"])
        if grid_config is None:
            raise Exception("Provide grid_config either as argument or as state_dict entry")
        board = Board(grid_config, board_id)
        for obj in state_dict["objs"].values():  # this is weirdly enough a dict
            piece = Piece.from_dict(obj, grid_config)
            board.add_piece(piece, check_piece_position)
        return board
