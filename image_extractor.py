import argparse
import itertools
import math
import multiprocessing as mp
import os
import pickle
from pathlib import Path

from matplotlib import colors
import matplotlib.pyplot as plt
import numpy as np


def read_file(path):
    with open(path, "rb") as infile:
        data = pickle.load(infile)

    history = data["history"]
    config = data["config"]

    return history, config


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
    def __init__(self, history, config, plot_objects, plot_targets, plot_grippers):
        self.history = history
        self.config = config
        self.plot_objects = plot_objects
        self.plot_targets = plot_targets
        self.plot_grippers = plot_grippers
        self.converter = Converter(config["move_step"])

    def draw_obj(self, obj, data, fillvalue):
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

    def get_borders(self, grid):
        lines = list()
        for y, row in enumerate(grid):
            for x, tile in enumerate(row):
                if tile != 0:
                    # upper bound
                    if y == 0 or grid[y - 1][x] != tile:
                        this_line = (
                            (x - 0.5, x + 0.5),
                            (y - 0.5, y - 0.5),
                        )
                        lines.append(this_line)

                    # lower bound
                    if y == len(grid) - 1 or grid[y + 1][x] != tile:
                        this_line = (
                            (x - 0.5, x + 0.5),
                            (y + 0.5, y + 0.5),
                        )
                        lines.append(this_line)

                    # right bound
                    if x == len(grid) - 1 or grid[y][x + 1] != tile:
                        this_line = (
                            (x + 0.5, x + 0.5),
                            (y - 0.5, y + 0.5),
                        )
                        lines.append(this_line)

                    # left bound
                    if x == 0 or grid[y][x - 1] != tile:
                        this_line = (
                            (x - 0.5, x - 0.5),
                            (y - 0.5, y + 0.5),
                        )
                        lines.append(this_line)

        return lines

    def plot_state(self, state):
        # import converter from grid, the same needs to be done here!!
        x_dim = self.config["width"] * self.converter.multiplier
        y_dim = self.config["height"] * self.converter.multiplier

        fig, ax = plt.subplots(figsize=(20, 15))

        data = np.zeros((x_dim, y_dim))
        cols = ["white"]
        bounds = [-10, 0]

        # plot targets
        if self.plot_targets is True:
            bounds.append(1)
            cols.append("cornsilk")
            val = 0.1
            for obj in state["targets"].values():
                self.draw_obj(obj, data, val)
                # value shoud be different, but never higher than 1
                val += 0.00001

        # plot objects
        if self.plot_objects is True:
            for i, obj in enumerate(state["objs"].values()):
                bounds.append(2 + i)
                cols.append(obj["color"])
                self.draw_obj(obj, data, i + 1.5)

        borders = self.get_borders(data)
        for x, y in borders:
            ax.plot(x, y, scaley=False, linestyle="-", linewidth=2, color="black")

        # plot gripper(s)
        if self.plot_grippers is True:
            for gripper in state["grippers"].values():
                if gripper["gripped"] is None:
                    gr_color = "black"
                else:
                    gr_color = "red"
                ax.plot(
                    gripper["x"] * self.converter.multiplier - 0.5,
                    gripper["y"] * self.converter.multiplier - 0.5,
                    "x",
                    markersize=30,
                    color=gr_color,
                )

        # set background to -1 (white)
        data[data == 0] = -1

        # create discrete colormap
        cmap = colors.ListedColormap(cols)
        norm = colors.BoundaryNorm(bounds, cmap.N)

        # plot image
        ax.imshow(data, cmap=cmap, norm=norm)

        # draw gridlines
        ax.grid(which="major", axis="both", linestyle="-", color="black", linewidth=0.5)

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

        return fig

    def single(self, argument):
        state, output_name = argument
        fig = self.plot_state(state)
        plt.savefig(Path(output_name), dpi=80, bbox_inches="tight", pad_inches=0)
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", action="store", help="path to the pickle file")
    parser.add_argument("--plot_objects", action="store_true", default=True)
    parser.add_argument("--plot_targets", action="store_true", default=True)
    parser.add_argument("--plot_grippers", action="store_true", default=True)
    parser.add_argument("--outputdir", action="store", required=True)
    args = parser.parse_args()

    history, config = read_file(Path(args.path))

    plotter = Plotter(
        history,
        config,
        plot_objects=args.plot_objects,
        plot_targets=args.plot_targets,
        plot_grippers=args.plot_grippers,
    )

    output_dir = args.outputdir
    os.makedirs(Path(output_dir), exist_ok=True)

    # generator containing tuples (state, output/path) for multiprocessing
    mp_args = ((state, Path(f"{output_dir}/{i}")) for i, state in enumerate(history))

    with mp.Pool() as pool:
        for i, _ in enumerate(pool.imap(plotter.single, mp_args)):
            progress_bar(
                i + 1,
                len(history),
                prefix=f"Extracting: {i+1}/{len(history)}",
                length=40,
            )


if __name__ == "__main__":
    main()
