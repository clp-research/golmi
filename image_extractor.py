"""
script to create state-images from a file containing a list of states and a configuration file.

Syntax:
    python image_extractor.py file.pckl --outputdir images-output --plot objects borders --single-objects

    Args:
        - file.pckl: a pickled dictionary: 
        {
            "config": config_dict_format,
            "states": [list of states(dict) to plot]
        }

        --plot: a list of things to plot. available: objects, targets, grippers, grid, borders
        --single-objects: each object and its 5x5 square will be saved individually
        --to-numpy: instead of saving images, a dictionary containing numpy RGB arrays will be saved
            {
                "state": np.array(RGB-state),
                "object_idn": np.array(RGB-object box),
                ...
            }

    in the output folder the script will create following output:
        i.png --> entire state where i is the index of the state within the list
        i_idn.png --> a 5x5 image of the idn object from the i-th state 
                      (id numbers of objects are unique for each state)
"""


import argparse
import itertools
import math
import multiprocessing as mp
import os
import pickle
from pathlib import Path

from matplotlib import colors
import matplotlib.pyplot as plt
from matplotlib import patheffects
import numpy as np


def read_file(path):
    with open(path, "rb") as infile:
        data = pickle.load(infile)

    states = data["states"]
    config = data["config"]

    return states, config


def progress_bar(
    iteration,
    total,
    prefix="",
    suffix="",
    decimals=1,
    length=40,
    fill="#",
    miss=".",
    end="\r",
    stay=True,
    fixed_len=True,
):
    """
    Call in a loop to create terminal progress bar
    Parameters:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        miss        - Optional  : bar missing character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
        stay        - Optional  : progress bar stays on terminal
        fiexed_len  - Optional  : length includes pre- and suffix
    """
    if fixed_len:
        bar_len = length - len(prefix) - len(suffix)
    else:
        bar_len = length

    percent = f"{100*(iteration/float(total)):.{decimals}f}"
    filled_length = int(bar_len * iteration // total)
    bar = f"{fill * filled_length}{miss * (bar_len - filled_length)}"
    to_print = f"\r{prefix} [{bar}] {percent}% {suffix}"
    print(to_print, end=end)

    # print new line on complete
    if iteration >= total:
        if stay:
            print()
        else:
            # clean line given lenght of lase print
            print(" " * len(to_print), end=end)


class Converter:
    """
    class used to convert integer coordinates x, y
    to float ones given the step size used by the model
    """

    def __init__(self, step):
        self.factor = step
        self.multiplier = max(1, math.floor(1 / step))

    def __call__(self, coordinate):
        if float(self.factor).is_integer():
            yield coordinate
        else:
            x = coordinate["x"]
            y = coordinate["y"]

            possible_x = [x]
            possible_y = [y]

            while len(possible_y) < self.multiplier:
                x += self.factor
                y += self.factor
                possible_x.append(x)
                possible_y.append(y)

            for new_x, new_y in itertools.product(possible_x, possible_y):
                yield {
                    "x": round(new_x, 5) * self.multiplier,
                    "y": round(new_y, 5) * self.multiplier,
                }


class Plotter:
    def __init__(
        self,
        states,
        config,
        single_objects,
        to_numpy,
        np_dims,
        small_bb,
        matplotlib,
        plot_objects=False,
        plot_targets=False,
        plot_grippers=False,
        plot_grid=False,
        plot_borders=False,
    ):
        self.states = states
        self.config = config
        self.to_numpy = to_numpy
        self.np_dims = tuple((i / 100 for i in np_dims))
        self.small_bb = small_bb
        self.matplotlib = matplotlib
        self.single_objects = single_objects
        self.plot_objects = plot_objects
        self.plot_targets = plot_targets
        self.plot_grippers = plot_grippers
        self.plot_grid = plot_grid
        self.plot_borders = plot_borders
        self.converter = Converter(config["move_step"])

    def draw_obj(self, obj, data, fillvalue):
        """
        draw a single object on a 2D grid with a unique fillvalue
        """
        for y, row in enumerate(obj["block_matrix"]):
            for x, tile in enumerate(row):
                if tile == 1:
                    # convert coordinates with converter!
                    for new_c in self.converter({"x": x + obj["x"], "y": y + obj["y"]}):
                        this_x = new_c["x"]
                        this_y = new_c["y"]

                        grid_x = int(this_x)
                        grid_y = int(this_y)
                        data[grid_y][grid_x] = fillvalue

    def find_long(self, coord):
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

    def get_borders(self, grid, gripped):
        """
        iterate over the the 2D array (from get_matrix) and detect borders
        """
        lines = list()
        gr_lines = list()
        for y, row in enumerate(grid):
            for x, tile in enumerate(row):
                if tile != 0:
                    # if object is gripped, save id separately
                    # to later plot thicker border lines
                    if tile in gripped:
                        output_list = gr_lines
                    else:
                        output_list = lines

                    # upper bound
                    if y == 0 or grid[y - 1][x] != tile:
                        this_line = (
                            (x - 0.5, x + 0.5),
                            (y - 0.5, y - 0.5),
                        )
                        output_list.append(this_line)

                    # lower bound
                    if y == len(grid) - 1 or grid[y + 1][x] != tile:
                        this_line = (
                            (x - 0.5, x + 0.5),
                            (y + 0.5, y + 0.5),
                        )
                        output_list.append(this_line)

                    # right bound
                    if x == len(grid[0]) - 1 or grid[y][x + 1] != tile:
                        this_line = (
                            (x + 0.5, x + 0.5),
                            (y - 0.5, y + 0.5),
                        )
                        output_list.append(this_line)

                    # left bound
                    if x == 0 or grid[y][x - 1] != tile:
                        this_line = (
                            (x - 0.5, x - 0.5),
                            (y - 0.5, y + 0.5),
                        )
                        output_list.append(this_line)

        return lines, gr_lines

    def get_matrix(self, state):
        """
        given a state, a 2D numpy array is created where each object and target
        is identified by a unique number which is then used to assign
        it its colour. this is then used to generate a heatmap which represents
        the plotted state.
        """
        # import converter from grid, the same needs to be done here!!
        x_dim = self.config["width"] * self.converter.multiplier
        y_dim = self.config["height"] * self.converter.multiplier

        # initialize variables to plot the grid
        data = np.zeros((x_dim, y_dim))
        cols = ["#FFFFFF"]
        bounds = [-10, 0.5]
        col_dict = {0: "#FFFFFF"}
        gripped = set()
        val = 1

        # plot targets
        if self.plot_targets is True:
            for i, obj in enumerate(state["targets"].values()):
                val += i
                bounds.append(val + 0.5)
                cols.append("#fff8dc")
                col_dict[val] = "#fff8dc"
                self.draw_obj(obj, data, val)

        # plot objects
        if self.plot_objects is True:
            val += 1
            for i, obj in enumerate(state["objs"].values()):
                val += i
                bounds.append(val + 0.5)
                cols.append(obj["color"])
                col_dict[val] = obj["color"]
                self.draw_obj(obj, data, val)
                if obj["gripped"] is True:
                    gripped.add(val)

        return data, cols, col_dict, bounds, gripped

    def get_image_array_matplotlib(self, state, data, cols, bounds, gripped):
        """
        convert a state to an RGB numpy array
        """
        x_dim = len(data[0])
        y_dim = len(data)

        fig, ax = plt.subplots(figsize=self.np_dims, dpi=100)

        if self.plot_borders is True:
            # get borders and eliminate seams within them
            borders, grip_borders = self.get_borders(data, gripped)
            l_borders = self.find_long(borders)
            l_grip_borders = self.find_long(grip_borders)

            # plot borders of all objects
            for x, y in l_borders:
                ax.plot(x, y, scaley=False, linestyle="-", linewidth=2, color="black")

            # gripped objects have a thicker border
            for x, y in l_grip_borders:
                ax.plot(
                    x,
                    y,
                    scaley=False,
                    linestyle="-",
                    linewidth=2,
                    color="black",
                    path_effects=[patheffects.withStroke(linewidth=4)],
                )

        # plot gripper(s)
        if self.plot_grippers is True:
            for gripper in state["grippers"].values():
                if gripper["gripped"] is None:
                    size = 19
                else:
                    size = 14
                ax.plot(
                    gripper["x"] * self.converter.multiplier - 0.5,
                    gripper["y"] * self.converter.multiplier - 0.5,
                    "x",
                    markersize=size,
                    color="black",
                )

        # create discrete colormap
        cmap = colors.ListedColormap(cols)
        norm = colors.BoundaryNorm(bounds, cmap.N)

        # plot image
        ax.imshow(data, cmap=cmap, norm=norm)

        if self.plot_grid is True:
            # draw gridlines
            ax.grid(
                which="major", axis="both", linestyle="-", color="black", linewidth=0.5
            )

            # resize gridlines and remove labels
            ax.set_xticks(np.arange(-0.5, x_dim, self.converter.multiplier))
            ax.set_yticks(np.arange(-0.5, y_dim, self.converter.multiplier))

        # remove labels and ticks on edges
        ax.tick_params(
            axis="both",
            which="both",
            bottom=False,
            top=False,
            left=False,
            right=False,
            labelbottom=False,
            labelleft=False,
        )

        # if self.to_numpy is True:
        fig.tight_layout(pad=0)
        ax.figure.canvas.draw()
        # Get the RGBA buffer from the figure
        w, h = fig.canvas.get_width_height()
        buf = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8).reshape(h, w, 3)
        plt.close(fig)
        return buf

    def get_image_array(self, state, data, cols, bounds, gripped):
        colors = {
            "#FFFFFF": [255, 255, 255],  # white
            "#8b4513": [139, 69, 19],    # brown
            "#808080": [128, 128, 128],  # grey
            "#ffa500": [255, 165, 0],    # orange
            "#800080": [128, 0, 128],    # purple
            "#0000ff": [0, 0, 255],      # blue
            "#ffff00": [255, 255, 0],    # yellow
            "#ff0000": [255, 0, 0],      # red
            "#fff8dc": [255, 248, 220],  # cornsilk
            "#008000": [0, 128, 0],      # green
        }

        # obtain an index to rgb conversion dictionary and create an
        # empty array with 3 dimensions as empty canvas
        index_2_rgb = {k: np.array(colors[v]) for k, v in cols.items()}
        state_array = np.copy(data).astype(object)
        rgb_shape = tuple(np.append(data.shape, 3))
        state_array = np.empty(rgb_shape)

        # "plot" objects
        for key, rgb in index_2_rgb.items():
            state_array[data == key] = rgb

        # use kronecker product with np.ones arrays to scale up
        # image to desired output dimensions
        kron_dim = np.array(self.np_dims) * 100 / data.shape
        kron_dim = tuple(np.append(kron_dim, 1).astype(int))
        return np.kron(state_array, np.ones(kron_dim)).astype(int)

    def get_single_object(self, np_state, obj):
        """
        given the RGB np.array of the state and the object dictionary,
        slice the state to create a small image of size len(block_matrix)
        """
        x_factor = np_state.shape[1] / self.config["width"]
        y_factor = np_state.shape[0] / self.config["height"]

        if self.small_bb is True:
            min_y = len(obj["block_matrix"])
            min_x = len(obj["block_matrix"][0])
            max_y = 0
            max_x = 0

            for y, row in enumerate(obj["block_matrix"]):
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

            this_x = (obj["x"] + min_x) * x_factor
            this_y = (obj["y"] + min_y) * y_factor

            x_limit = (obj["x"] + max_x + 1) * x_factor
            y_limit = (obj["y"] + max_y + 1) * y_factor

        else:
            this_x = int(max(0, obj["x"] * x_factor))
            this_y = int(max(0, obj["y"] * y_factor))
            x_limit = int(
                min(
                    (obj["x"] * x_factor + x_factor * len(obj["block_matrix"])),
                    np_state.shape[1],
                )
            )
            y_limit = int(
                min(
                    (obj["y"] * y_factor + y_factor * len(obj["block_matrix"])),
                    np_state.shape[0],
                )
            )

            # move window if object is against borders
            if x_limit - this_x < len(obj["block_matrix"]) * x_factor:
                diff = x_limit - this_x
                to_add = x_factor * len(obj["block_matrix"]) - diff

                if this_x == 0:
                    x_limit += to_add
                else:
                    this_x -= to_add

            if y_limit - this_y < len(obj["block_matrix"]) * y_factor:
                diff = y_limit - this_y
                to_add = y_factor * len(obj["block_matrix"]) - diff

                if this_y == 0:
                    y_limit += to_add
                else:
                    this_y -= to_add

        return np_state[int(this_y) : int(y_limit), int(this_x) : int(x_limit)]

    def single(self, argument):
        """
        single threaded function to generate an image or numpy array from a state
        """
        state, output_name = argument
        data, cols, col_dict, bounds, gripped = self.get_matrix(state)
        output = dict()

        # obtain an RGB array of the entire state
        if self.matplotlib is True:
            np_state = self.get_image_array_matplotlib(
                state, data, cols, bounds, gripped
            )
        else:
            np_state = self.get_image_array(state, data, col_dict, bounds, gripped)

        output["state"] = np_state

        # slice single objects from the RGB array
        if self.single_objects is True:
            for idn, obj in state["objs"].items():
                this_obj = self.get_single_object(np_state, obj)
                output[f"object_{idn}"] = this_obj

        # save output in .npz file
        if self.to_numpy is True:
            np.savez(output_name, **output)
        else:
            # plot and save images (takes longer)
            for n, image in output.items():
                fig, ax = plt.subplots(figsize=(15, 15), dpi=100)
                ax.imshow(image)
                plt.axis("off")
                plt.savefig(
                    Path(f"{output_name}_{n}"),
                    dpi=80,
                    bbox_inches="tight",
                    pad_inches=0,
                )
                plt.close()


def main():
    plottable = {"objects", "targets", "grippers", "grid", "borders"}
    parser = argparse.ArgumentParser()
    parser.add_argument("path", action="store", help="path to the pickle file")
    parser.add_argument(
        "--plot",
        nargs="+",
        action="store",
        help="Elements to plot: " + ", ".join(plottable),
        required=True,
    )
    parser.add_argument("--outputdir", action="store", required=True)
    parser.add_argument(
        "--single", action="store_true", help="deactivate multithreading"
    )
    parser.add_argument("--single-objects", action="store_true")
    parser.add_argument(
        "--to-numpy",
        action="store_true",
        help="save a RGB numpy vector instead of an image",
    )
    parser.add_argument(
        "--np-dim",
        action="store",
        help="pixel dimention of the state array (default: %(default)s)",
        default="600x600",
    )
    parser.add_argument(
        "--small-bb",
        action="store_true",
        help="single objects are saved with the smallest possible bounding box",
    )
    parser.add_argument(
        "--matplotlib",
        action="store_true",
        help="use matplotlib to render the RGB array of the image",
    )
    args = parser.parse_args()

    w, h = args.np_dim.split("x")
    np_dims = (int(w), int(h))

    # extract elements to plot
    pl_args = dict()
    for element in args.plot:
        if element in plottable:
            key = f"plot_{element}"
            pl_args[key] = True
        else:
            raise ValueError(
                f"unknown plottable: {element}\navailable plottables: "
                f'{", ".join(plottable)}'
            )

    # read file and create plotter
    states, config = read_file(Path(args.path))
    plotter = Plotter(
        states,
        config,
        args.single_objects,
        args.to_numpy,
        np_dims,
        args.small_bb,
        args.matplotlib,
        **pl_args,
    )

    # prepare output dirrectory
    output_dir = args.outputdir
    os.makedirs(Path(output_dir), exist_ok=True)

    # generator containing tuples (state, output/path) for multiprocessing
    mp_args = ((state, Path(f"{output_dir}/{i}")) for i, state in enumerate(states))

    if args.single:
        for i, image in enumerate(mp_args):
            plotter.single(image)
            progress_bar(
                i + 1,
                len(states),
                prefix=f"Extracting: {i+1}/{len(states)}",
                length=40,
            )

    else:
        with mp.Pool() as pool:
            for i, _ in enumerate(pool.imap(plotter.single, mp_args)):
                progress_bar(
                    i + 1,
                    len(states),
                    prefix=f"Extracting: {i+1}/{len(states)}",
                    length=40,
                )


if __name__ == "__main__":
    main()
