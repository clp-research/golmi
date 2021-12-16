import abc
import itertools
import json
import os
import random
from tqdm import tqdm

from app.neureg import algos
from model import generator
from model.config import Config
from model.obj import Obj


class GenerateCallback(abc.ABC):

    def on_generate_start(self):
        pass

    def on_new_task(self, idx, sample):
        pass

    def on_generate_end(self):
        pass


def piece_to_dict(piece):
    piece_dict = piece.to_dict()
    piece_dict["posRelBoard"] = piece.posRelBoard  # we attached this manually
    return piece_dict


def task_to_dict(task, idx=None):
    task_dict = {
        "pieces": [piece_to_dict(p) for p in task["pieces"]],
        "target": piece_to_dict(task["target"]),
        "refs": task["refs"]
    }
    if idx is not None:
        task_dict["task_id"] = idx
    return task_dict


class TaskInMemorySaver(GenerateCallback):

    def __init__(self):
        self.samples = []

    def on_generate_start(self):
        self.samples = []

    def on_new_task(self, idx, task):
        self.samples.append(task_to_dict(task, idx))

    def on_generate_end(self):
        print(f"Samples: {len(self.samples)}")


class TaskStorageSaver(GenerateCallback):

    def __init__(self, output_path):
        if output_path is None:
            raise Exception("Missing 'output_path'")
        self.output_path = output_path
        self.output_dir = None

    def on_generate_start(self):
        if not os.path.exists(self.output_path):
            raise Exception("Cannot find output_path: " + self.output_path)
        output_dir = os.path.join(self.output_path, "generated")
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
            print("output_dir:", output_dir)
        self.output_dir = output_dir


class TaskSingleFileStorageSaver(TaskStorageSaver):

    def __init__(self, output_path, overwrite_output=False):
        super(TaskSingleFileStorageSaver, self).__init__(output_path)
        self.samples = []
        self.file_path = None
        self.overwrite_output = overwrite_output

    def on_generate_start(self):
        super().on_generate_start()
        self.samples = []
        self.file_path = os.path.join(self.output_dir, f"tasks.json")
        if os.path.exists(self.file_path) and not self.overwrite_output:
            raise Exception("Output file already exists. Delete manually before and try again.")

    def on_new_task(self, idx, task):
        self.samples.append(task_to_dict(task, idx))

    def on_generate_end(self):
        with open(self.file_path, "w") as f:
            json.dump(self.samples, f)


class TaskMultiFileStorageSaver(TaskStorageSaver):

    def on_new_task(self, idx, task):
        file_path = os.path.join(self.output_dir, f"task_{idx}.json")
        with open(file_path, "w") as f:
            json.dump(task_to_dict(task, idx), f)


class TaskSummarizer(GenerateCallback):

    def __init__(self, property_names):
        self.property_names = property_names
        self.summary = dict([(p, 0) for p in self.property_names])

    def on_generate_start(self):
        pass

    def on_new_task(self, idx, sample):
        for property_name in sample["props"]:
            self.summary[property_name] += 1

    def on_generate_end(self):
        pass

    def print_summary(self):
        for p, c in self.summary.items():
            print("{:>15}: {:>5d}".format(p, c))


class TaskGenerator:
    """
        The logic to produce a task (pieces, target, instruction)

        This is supposed to be called either by a flask route or directly by a script (for batch-processing).
    """

    def __init__(self, config: Config):
        self.property_names = ["color", "shape", "posRelBoard"]
        self.generator = generator.Generator(config)
        self.incremental_algorithm = algos.IncrementalAlgorithm()
        self.width = config.width
        self.height = config.height

    def list_random_samples(self, n: int, n_objects=5, shuffle=False):
        return [self.generate_random_sample(n_objects, shuffle) for _ in range(n)]

    def yield_random_samples(self, n: int):
        for _ in range(n):
            yield self.generate_random_sample()

    def generate_epoch(self, number_of_samples, callbacks: list[GenerateCallback]):
        for clb in callbacks:
            clb.on_generate_start()
        for idx, _ in enumerate(tqdm(range(number_of_samples))):
            sample = self.generate_random_sample(permute_props=True)
            for clb in callbacks:
                clb.on_new_task(idx, sample)
        for clb in callbacks:
            clb.on_generate_end()

    def _attach_prop_posRelBoard(self, obj):
        pos = ""
        x = obj.x + (obj.width / 2)
        y = obj.y + (obj.height / 2)
        if y < 2 * self.height / 5:
            pos = "top"
        elif y >= 3 * self.height / 5:
            pos = "bottom"
        if x < 2 * self.width / 5:
            pos = pos + " left" if len(pos) > 0 else "left"
        elif x >= 3 * self.width / 5:
            pos = pos + " right" if len(pos) > 0 else "right"
        if not pos:
            pos = "center"
        obj.posRelBoard = pos

    def _generate_situation(self, n_objects):
        state, _, _ = self.generator.generate_random_state(n_objects, n_grippers=0)
        pieces = list(state.objs.values())  # this is a map
        selection = random.choice(pieces)
        return pieces, selection

    def generate_random_sample(self, n_objects=5, shuffle_props=False, permute_props=False) -> dict:
        pieces, selection = self._generate_situation(n_objects)
        return self.generate_random_sample_for_scene(pieces, selection, shuffle_props, permute_props)

    def generate_random_sample_for_scene(self, pieces: list[Obj], selection: Obj,
                                         shuffle_props=False, permute_props=False):
        if shuffle_props:  # the discriminator is biased towards the first prop, thus you might want to re-shuffle
            random.shuffle(self.property_names)
        prop_seqs = [self.property_names]
        if permute_props:  # we call the algo for each combination of props
            prop_seqs = list(itertools.permutations(self.property_names))
        # add "posRelBoard" as a property of the piece
        [self._attach_prop_posRelBoard(p) for p in pieces]
        refs = []
        for prop_seq in prop_seqs:
            instruction, props = self.incremental_algorithm.generate(prop_seq, pieces, selection)
            refs.append({
                "instr": instruction,  # the referring expression
                "props": props,  # the discriminating properties
                "props_pref": prop_seq  # the preference order
            })
        return {
            "pieces": pieces,
            "target": selection,
            "refs": refs
        }

    @classmethod
    def create(cls, n_colors=None, n_types=None):
        config = Config.from_json("../app/dynamatt/static/resources/config/pentomino_config.json")
        if n_colors:
            config.colors = random.sample(config.colors, n_colors)
        if n_types:
            types = random.sample(list(config.type_config.keys()), n_types)
            config.type_config = dict([(t, config.type_config[t]) for t in types])
        return TaskGenerator(config)
