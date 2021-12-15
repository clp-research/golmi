"""File: plot_helper.py
Helper functions to create plots.

Author:
    Karla Friedrichs

Evaluation Skript To Bachelor Thesis:
    "Modeling collaborative reference in a Pentomino domain using the GOLMI
    framework"
"""

import matplotlib.pyplot as plt
#plt.rcParams.update({'font.size': 8})
import numpy as np

# Evaluation skript to bachelor thesis:
# "Modeling collaborative reference in a Pentomino
# domain using the GOLMI framework"
# Author: Karla Friedrichs

# Python 3
# Helper functions to create plots


def create_hist(answer_list, title=None, savepath=None, xmin=None,
                xmax=None, x_axislabel=None, y_axislabel=None):
    """Func: create_hist
    Create a histogram.

    Params:
    answer_list - _list_ of _str_. The category labels.
    title - _str_ or None. Title to display, pass None for no title.
    savepath - _str_ or None.
        If None, the plot will be shown (plt.show()), otherwise
        the figure will be saved to the specified path.
    x_min - Leftmost / lowest bin.
    x_max - Rightmost / highest bin.
    x_axislabel - _str_ or None. Label for x axis.
    y_axislabel - _str_ or None. Label for y axis.
    """
    answer_list.sort()
    if xmin is None or xmax is None:
        range = None
    else:
        range = (xmin, xmax)
    fig, ax = plt.subplots()
    ax.hist(answer_list, bins=xmax - xmin + 1, range=range, facecolor="orange")
    plt.xlabel(x_axislabel)
    plt.ylabel(y_axislabel)
    if title:
        fig.suptitle(title)
    # save or display the figure
    if savepath is not None:
        fig.savefig(savepath)
    else:
        plt.show()
    plt.close(fig)


def create_line(categories, category_counts, title=None, savepath=None,
                x_ticklabels=None, x_axislabel=None, y_axislabel=None,
                y_lim=None, linestyles=None, markers=None, colors=None):
    """Func: create_line
    Create a (standard) line plot with one line per category.

    Params:
    categories - _list_ of _str_. The category labels.
    category_counts - _dict_.
        A mapping from question labels to a list of answers per category.
        It is assumed all lists contain the same number of entries and that
        it matches the length of _categories_.
        Each list needs to have the same length!
    title - _str_ or None. Title to display, pass None for no title.
    savepath - _str_ or None
        If None, the plot will be shown (plt.show()), otherwise
        the figure will be saved to the specified path.
    x_ticklabels - iterable or None. Labels to use for x axis ticks.
    x_axislabel - _str_ or None. Label for x axis.
    y_axislabel -  _str_ or None. Label for y axis.
    y_lim - tuple or None.
        2-tuple (lower_limit, upper_limit) for y axis.
    linestyles - _dict_ or None.
        Define a matplotlib linestyle for each category. If used,
        data points will be connected.
    markers - _dict_ or None.
        Define a matplotlib marker type for each category.
    colors - _dict_ or None.
        Define a color for each category. Used for markers.
    """
    fig, ax = plt.subplots(figsize=(7, 5))
    fig.suptitle(title)
    x_pos = np.arange(len(category_counts[categories[0]]))
    for cat in categories:
        if linestyles and linestyles[cat]:
            ax.plot(x_pos, category_counts[cat], label=cat, linestyle=linestyles[cat])
        elif markers and markers[cat]:
            if colors and colors[cat]:
                ax.plot(x_pos, category_counts[cat], label=cat,
                        marker=markers[cat], markersize=13, linestyle="None",
                        c=colors[cat])
            else:
                ax.plot(x_pos, category_counts[cat], label=cat,
                        marker=markers[cat], markersize=13, linestyle="None")
        else:
            ax.plot(x_pos, category_counts[cat], label=cat)
    # display line labels
    ax.legend()
    ax.set_xlabel(x_axislabel)
    ax.set_xticks(x_pos)
    # insert line breaks for multi-word labels
    x_ticklabels = [label.replace(" ", "\n").replace("/", "/\n") for label in x_ticklabels]
    ax.set_xticklabels(x_ticklabels)
    if y_lim is not None:
        ax.set_ylim(y_lim)
    ax.set_ylabel(y_axislabel)
    # save or display the figure
    if savepath is not None:
        fig.savefig(savepath)
    else:
        plt.show()
    plt.close(fig)


def create_horizontal_stack(categories, category_counts, title=None,
                            savepath=None, x_ticklabels=None,
                            y_axislabel=None, y_lim=None):
    """Func: create_horizontal_stack
    Create a stack plot in horizontal orientation.

    Adapted from
    <https://matplotlib.org/stable/gallery/lines_bars_and_markers/horizontal_barchart_distribution.html#sphx-glr-gallery-lines-bars-and-markers-horizontal-barchart-distribution-py>

    Params:
    categories - _list_ of _str_. The category labels.
    category_counts - _dict_
        A mapping from question labels to a list of answers per category.
        It is assumed all lists contain the same number of entries and that
        it matches the length of *categories*.
    title - _str_ or None. Title to display, pass None for no title.
    savepath - _str_ or None.
        If None, the plot will be shown (plt.show()), otherwise
        the figure will be saved to the specified path.
    """
    labels = list(category_counts.keys())
    data = np.array(list(category_counts.values()))
    data_cum = data.cumsum(axis=1)
    category_colors = plt.get_cmap("RdYlGn")(
        np.linspace(0.15, 0.85, data.shape[1]))

    fig, ax = plt.subplots(figsize=(9, 5))
    fig.suptitle(title)
    ax.invert_yaxis()
    ax.xaxis.set_visible(False)
    ax.set_xlim(0, np.sum(data, axis=1).max())

    for i, (colname, color) in enumerate(zip(categories, category_colors)):
        widths = data[:, i]
        starts = data_cum[:, i] - widths
        rects = ax.barh(labels, widths, left=starts, height=0.8,
                        label=colname, color=color)

        r, g, b, _ = color
        text_color = "white" if r * g * b < 0.5 else "darkgrey"
        ax.bar_label(rects, label_type="center", color=text_color)
    ax.legend(ncol=len(categories), bbox_to_anchor=(0, 1),
              loc="lower left", fontsize="small")
    # save or display the figure
    if savepath is not None:
        fig.savefig(savepath)
    else:
        plt.show()
    plt.close(fig)


def create_bar(categories, category_counts, category_error=None,
            title=None, savepath=None, y_ticklabels=None,
            y_axislabel=None, y_lim=None):
    """Func: create_bar
    Create a bar plot.

    Params:
    categories - _list_ of category names, in the same order
        as _category_counts_.
    category_counts - _list_.
        Values associated to each category, in the same order as categories.
    category_error - _list_ or None.
        Error for each count, displayed as an error bar in the plot.
    title - _str_ or None. Title to display, pass None for no title.
    savepath - _str_ or None
        If None, the plot will be shown (plt.show()), otherwise
        the figure will be saved to the specified path.
    y_ticklabels - iterable or None. Labels to use for y axis ticks.
    y_axislabel - _str_ or None. Label for y axis.
    y_lim - tuple or None. 2-tuple (lower_limit, upper_limit) for y axis.
    """
    fig, ax = plt.subplots()
    fig.suptitle(title)
    x_pos = np.arange(len(categories))
    ax.bar(x_pos, category_counts, yerr=category_error, align="center")
    ax.set_xticks(x_pos)
    # insert line breaks for multi-word labels
    categories = [cat.replace(" ", "\n").replace("/", "/\n") for cat in categories]
    ax.set_xticklabels(categories)
    if y_lim is not None:
        ax.set_ylim(y_lim)
    ax.set_ylabel(y_axislabel)
    if y_ticklabels is not None:
        ax.set_yticks(np.arange(len(y_ticklabels)))
        ax.set_yticklabels(y_ticklabels)
    # save or display the figure
    if savepath is not None:
        fig.savefig(savepath)
    else:
        plt.show()
    plt.close(fig)
