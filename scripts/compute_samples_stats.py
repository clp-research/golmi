import json

from app.dynamatt import dynatasks
from matplotlib import pyplot as plt
import numpy as np
import seaborn as sns

sns.set_theme()


def generate_samples_stats():
    n_samples, max_color, max_types = 100, 8, 12
    summaries = []
    for n_colors in range(max_color):
        for n_types in range(max_types):
            tasks = dynatasks.TaskGenerator.create(n_colors + 1, n_types + 1)
            tasks.get_random_samples(n_samples, shuffle=True)
            summaries.append({
                "n_colors": n_colors + 1,
                "n_types": n_types + 1,
                "counts": tasks.summary})
    with open("summaries.json", "w") as f:
        json.dump(summaries, f)


def show_samples_stats():
    # n_colors, n_types
    # samples: shape, color, pos
    with open("summaries.json") as f:
        summaries = json.load(f)
    max_colors = 8
    max_types = 12
    summaries_by_tuple = dict([((s["n_colors"], s["n_types"]), s["counts"]) for s in summaries])
    x = np.arange(1, max_colors + 1)
    y = np.arange(1, max_types + 1)
    fig, axes = plt.subplots(1, 3, figsize=(30, 10), sharey=True)
    for idx, prop in enumerate(["color", "shape", "posRelBoard"]):
        Z = np.zeros((max_colors, max_types))
        for (c, t) in summaries_by_tuple:
            Z[c - 1, t - 1] = summaries_by_tuple[(c, t)][prop]
        sns.heatmap(Z, annot=True, ax=axes[idx], fmt="g", square=True, cbar=False)
        axes[idx].set_title(prop)
    plt.savefig("summaries.png")


if __name__ == '__main__':
    generate_samples_stats()
    show_samples_stats()
