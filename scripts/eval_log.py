"""File: eval_log.py
Skript to evaluate the task logs.

Author:
    Karla Friedrichs

Evaluation Skript To Bachelor Thesis:
    "Modeling collaborative reference in a Pentomino domain using the GOLMI
    framework"

Usage:
    > python3 eval_log.py
"""

import os
import json
from plot_helper import create_line

# --- globals --- #

# Variable: DATA_COLLECTION_PATH
# directory containing json files, one per participant
DATA_COLLECTION_PATH = "./app/static/resources/data_collection"
# Variable: PLOT_PATH
# directory to save created plots to
PLOT_PATH = "./resources/plots"

# Variable: N_TASKS
# number of tasks, used to evaluate all tasks with indes up to N_TASKS
N_TASKS = 12
# Variable: AMBIG_TASKS
# list of ambiguous tasks (see thesis)
AMBIG_TASKS = [1, 5, 6, 9, 10, 11]
# Variable: UNAMBIG_TASKS
# list of unambiguous tasks (see thesis)
UNAMBIG_TASKS = [0, 2, 3, 4, 7, 8]
# Variable: ALGORITHMS
# list of algorithm names
ALGORITHMS = ["IA", "RDT", "SE"]
# Variable: LINESTYLES
# dictionary mapping algorithm names to matplotlib
# linestyles to use for plots
LINESTYLES = {"IA": "-", "RDT": "dotted", "SE": "--"}
# Variable: MARKERSTYLES
# dictionary mapping algorithm names to matplotlib
# markers to use for scatter plots
MARKERSTYLES = {"IA": "s", "RDT": "*", "SE": ">"}
# Variable: COLORS
# dictionary mapping algorithm names to colors to use for scatter plots
COLORS = {"IA": "orange", "RDT": "darkblue", "SE": "mediumaquamarine"}


def eval_log():
    """Func: eval_log
    Evaluates the GOLMI logs: print statistics and creates plots
    for incorrect attempts and time needed by participants.
    """
    log = read_logs()
    eval_incorrect_attempts(log, "all_tasks")
    eval_incorrect_attempts(log, "ambig", tasks=AMBIG_TASKS)
    eval_incorrect_attempts(log, "unambig", tasks=UNAMBIG_TASKS)
    eval_time_to_solve(log, "all_tasks")
    eval_time_to_solve(log, "ambig", tasks=AMBIG_TASKS)
    eval_time_to_solve(log, "unambig", tasks=UNAMBIG_TASKS)


# --- read data --- #

def read_logs():
    """Func: read_logs
    Reads in all json files and extract task logs.

    Returns:
    _dict_ mapping algorithm to _dict_ with entries 'log',
    'target', 'incorrect attempts'
    """
    data = {alg: list() for alg in ALGORITHMS}
    # walk the directory and read in each file
    for filename in os.listdir(DATA_COLLECTION_PATH):
        if filename.endswith(".json"):
            # parse json data
            with open(os.path.join(DATA_COLLECTION_PATH, filename)) as file:
                json_data = json.load(file)
                # make sure file has "algorithm" key with valid value
                assert "algorithm" in json_data, "Error:" + \
                    " missing 'algorithm' entry in file {}".format(filename)
                alg = json_data["algorithm"]
                assert alg in ALGORITHMS, "Error:" + \
                    " invalid 'algorithm' entry in file {}".format(filename)

                data[alg].append(list())
                # read in log, target, attempts for each task
                for i in range(N_TASKS):
                    task_key = str(i)
                    # make sure all expected keys are present
                    assert task_key in json_data, "Error:" + \
                        " key {} missing in file {}".format(task_key, filename)
                    data[alg][-1].append(json_data[task_key])
    return data


# --- attempts per task --- #

def eval_incorrect_attempts(log, savename, tasks=list(range(N_TASKS))):
    """Func: eval_incorrect_attempts
    Prints out information on the attempts needed by participants
    to solve each task. One plot is created.

    Params:
    log - parsed log data
    savename - _str_, name for the plot. The plot file will be called
        'incorrect_attempts_NAME.png'.
    tasks - optional: task indexes to include
        *default*: indices 0 to <N_TASKS> -1
    """
    # relevant key in the log
    attempt_key = "incorrectAttempts"
    alg_averages = {alg: list() for alg in ALGORITHMS}
    # read in log, target, attempts for each task
    for alg in log:
        print("-" * 5 + "\t" + alg + "\t" + "-" * 5)
        # attempts among all tasks
        all_attempts = 0
        # attempts per task
        task_attempts = [0 for _ in tasks]

        for run in log[alg]:
            for i, task in enumerate(tasks):
                all_attempts += run[task][attempt_key]
                task_attempts[i] += run[task][attempt_key]

        # print the results
        n_runs = len(log[alg])
        print("Average incorrect attempts per user for all {} tasks: {}".format(
            len(tasks), all_attempts / n_runs))
        print("Average for each task:")
        for i, task in enumerate(tasks):
            average = task_attempts[i] / n_runs
            print("Task {}: {}".format(task, average))
            alg_averages[alg].append(average)
    # plot
    create_line(ALGORITHMS, alg_averages,
                title="Average number of incorrect identifications",
                savepath=os.path.join(PLOT_PATH,
                    "incorrect_attempts_{}.png".format(savename)),
                x_ticklabels=list(str(t + 1) for t in tasks),
                x_axislabel="Task No.",
                y_axislabel="Average incorrect attempts", #y_lim=(0, 1),
                markers=MARKERSTYLES, colors=COLORS)


def eval_time_to_solve(log, savename, tasks=list(range(N_TASKS))):
    """Func: eval_time_to_solve
    Prints out information on the time participants needed
    to solve tasks as well as the number of instructions given.
    Creates two plots.

    Params:
    log - parsed log data
    savename - _str_, name for the plot. The plot files will be called
        'feedback_NAME.png' and 'time_NAME_png'.
    tasks - optional: task indexes to include.
        *default*: indices 0 to <N_TASKS> -1
    """
    log_key = "log"
    alg_feedback_averages = {alg: list() for alg in ALGORITHMS}
    alg_time_averages = {alg: list() for alg in ALGORITHMS}
    for alg in log:
        print("-" * 5 + "\t" + alg + "\t" + "-" * 5)
        alg_n_feedback = [0 for _ in tasks]
        alg_time_to_solve = [0 for _ in tasks]
        n_outliers = [0 for _ in tasks]
        for run in log[alg]:
            for i, task in enumerate(tasks):
                n_feedback = 0
                time_to_solve = 0
                instr_found = False
                last_movement = 0
                outlier = False
                # iterate through the log
                for timestamp, entry in run[task][log_key]:
                    # check how long user was idle
                    if "gripper" in entry:
                        idle_time = timestamp - last_movement
                        # user was idle for more than 20 seconds -> outlier
                        if idle_time >= 20000:
                            outlier = True
                            n_outliers[i] += 1
                            break
                        last_movement = timestamp
                    if not instr_found:
                        # find time of first instruction
                        if "type" in entry and entry["type"] == "instruction":
                            assert "duration" in entry, "Error:" + \
                                " 'duration' key missing in message entry at {}".format(timestamp)
                            # compute time needed to solve task: last timestamp - instruction end
                            # (convert milliseconds to seconds)
                            instr_end = timestamp / 1000 + entry["duration"]
                            time_to_solve += run[task][log_key][-1][0] / 1000 - instr_end
                            instr_found = True
                    else:
                        # count feedback until object was selected (=end of log)
                        if "type" in entry and entry["type"] == "feedback":
                            n_feedback += 1
                # if the run was no outlier, save the results
                if not outlier:
                    alg_time_to_solve[i] += time_to_solve
                    alg_n_feedback[i] += n_feedback

        # compute averages
        n_runs = len(log[alg])
        alg_feedback_averages[alg] = [alg_n_feedback[i] / (n_runs - n_outliers[i]) for i in range(len(tasks))]
        alg_time_averages[alg] = [alg_time_to_solve[i] / (n_runs - n_outliers[i]) for i in range(len(tasks))]
        # print results
        print("Average no. of feedback messages, all tasks: {}".format(
            sum(alg_feedback_averages[alg]) / len(tasks)))
        for i, task in enumerate(tasks):
            print("Average no. of feedback messages, task {}: {} ({} outliers)".format(
                task + 1, alg_feedback_averages[alg][i], n_outliers[i]))
        print("Average time until identification, all tasks: {}".format(
            sum(alg_time_averages[alg]) / len(tasks)))
        for i, task in enumerate(tasks):
            print("Average time until identification, task {}: {} ({} outliers)".format(
                task + 1, alg_time_averages[alg][i], n_outliers[i]))
    # plot
    create_line(ALGORITHMS, alg_feedback_averages,
                title="Average feedback messages generated",
                savepath=os.path.join(
                    PLOT_PATH, "feedback_{}.png".format(savename)),
                x_ticklabels=list(str(i + 1) for i in tasks),
                x_axislabel="Task No.",
                y_axislabel="Av. number of feedback messages",
                y_lim=(0, 8),
                markers=MARKERSTYLES, colors=COLORS)
    create_line(ALGORITHMS, alg_time_averages,
                title="Average time to identification",
                savepath=os.path.join(
                    PLOT_PATH, "time_{}.png".format(savename)),
                x_ticklabels=list(str(i + 1) for i in tasks),
                x_axislabel="Task No.",
                y_axislabel="Av. time to task completion (s)",
                y_lim=(0, 20),
                markers=MARKERSTYLES, colors=COLORS)


def main():
    eval_log()


if __name__ == "__main__":
    main()
