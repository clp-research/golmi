import argparse
import pickle
import os
from pathlib import Path
import multiprocessing as mp

import matplotlib.pyplot as plt
from matplotlib import colors
import numpy as np


def read_file(path):
    with open(path, "rb") as infile:
        data = pickle.load(infile)
    
    history = data["history"]
    config = data["config"]

    return history, config


def progress_bar(
        iteration, total, prefix='', suffix='', decimals=1,
        length=40, fill='#', miss=".", end="\r", stay=True,
        fixed_len=True):
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
            print(" "*len(to_print), end=end)

class Plotter:
    def __init__(self, history, config, plot_objects, plot_targets, plot_grippers):
        self.history = history
        self.config = config
        self.plot_objects = plot_objects
        self.plot_targets = plot_targets
        self.plot_grippers = plot_grippers

    def draw_obj(self, obj, data, fillvalue):
        lines = list()
        
        for y, row in enumerate(obj["block_matrix"]):
            for x, tile in enumerate(row):
                if tile == 1:
                    grid_x = int(x + obj["x"])
                    grid_y = int(y + obj["y"])
                    data[grid_y][grid_x] = fillvalue

                    # upper bound
                    if y==0 or obj["block_matrix"][y-1][x] == 0:
                        this_line = ((grid_x - 0.5, grid_x + 0.5), (grid_y - 0.5, grid_y - 0.5))
                        lines.append(this_line)
                        
                    # lower bond
                    if y==len(obj["block_matrix"]) - 1 or obj["block_matrix"][y+1][x] == 0:
                        this_line = ((grid_x - 0.5, grid_x + 0.5), (grid_y + 0.5, grid_y + 0.5))
                        lines.append(this_line)

                    # right bond
                    if x==len(obj["block_matrix"][0]) - 1 or obj["block_matrix"][y][x+1] == 0:
                        this_line = ((grid_x + 0.5, grid_x + 0.5), (grid_y - 0.5, grid_y + 0.5))
                        lines.append(this_line)

                    # left bond
                    if x==0 or obj["block_matrix"][y][x-1] == 0:
                        this_line = ((grid_x - 0.5, grid_x - 0.5), (grid_y - 0.5, grid_y + 0.5))
                        lines.append(this_line)
                        
        return lines


    def plot_state(self, state):
        x_dim = self.config["width"]
        y_dim = self.config["height"]
        
        fig, ax = plt.subplots(figsize=(20, 15))

        data = np.zeros((x_dim, y_dim))
        cols = ["white"]
        bounds = [-10, 0]

        # plot targets
        if self.plot_targets is True:
            bounds.append(1)
            cols.append("cornsilk")
            for obj in state["targets"].values():
                lines = self.draw_obj(obj, data, 0.5)
                for x, y in lines:
                    ax.plot(x, y, scaley=False, linestyle="-", linewidth=2, color="black")

        # plot objects
        if self.plot_objects is True:
            for i, obj in enumerate(state["objs"].values()):
                bounds.append(2+i)
                cols.append(obj["color"])
                lines = self.draw_obj(obj, data, i + 1.5)
                for x, y in lines:
                    ax.plot(x, y, scaley=False, linestyle="-", linewidth=2, color="black")

        # plot gripper(s)
        if self.plot_grippers is True:
            for gripper in state["grippers"].values():
                ax.plot(gripper["x"]-0.5, gripper["y"]-0.5, "x", markersize=30, color="black")

        # set background to -1 (white)
        data[data == 0] = -1
        
        # create discrete colormap
        cmap = colors.ListedColormap(cols)
        norm = colors.BoundaryNorm(bounds, cmap.N)

        # plot image
        ax.imshow(data, cmap=cmap, norm=norm)

        # draw gridlines
        ax.grid(which='major', axis='both', linestyle='-', color='black', linewidth=0.5)

        # resize gridlines and remove labels
        ax.set_xticks(np.arange(-.5, x_dim, 1));
        ax.set_yticks(np.arange(-.5, y_dim, 1));
        ax.set_yticklabels([])
        ax.set_xticklabels([])

        return fig


    def single(self, argument):
        state, output_name = argument
        fig = self.plot_state(state)
        plt.savefig(Path(output_name), dpi=80)
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
        plot_grippers=args.plot_grippers
    )

    output_dir = args.outputdir
    os.makedirs(Path(output_dir), exist_ok=True)

    mp_args = list()
    for i, state in enumerate(history):
        mp_args.append(tuple([state, Path(f"{output_dir}/{i}")]))

    with mp.Pool() as pool:
        for i, _ in enumerate(pool.imap(plotter.single, mp_args)):
            progress_bar(
                i+1, len(history),
                prefix=f"Extracting: {i+1}/{len(history)}",
                length=40
            )


if __name__ == "__main__":
    main()