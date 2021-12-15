import abc
import json
import os
import random
from tqdm import tqdm

from app.dynamatt import dynaalgos, dynatypes
from model import generator
from model.config import Config


class GenerateCallback(abc.ABC):

    def on_generate_start(self):
        pass

    def on_new_task(self, idx, sample):
        pass

    def on_generate_end(self):
        pass


class TaskInMemorySaver(GenerateCallback):

    def __init__(self):
        self.samples = []

    def on_generate_start(self):
        self.samples = []

    def on_new_task(self, idx, task):
        self.samples.append({
            "task_id": idx,
            "pieces": [p.to_dict() for p in task["pieces"]],
            "target": task["target"].to_dict(),
            "instr": task["instr"],
            "props": task["props"]
        })

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
        if os.path.exists(output_dir):
            print("output_dir:", output_dir)
            try:
                os.rmdir(output_dir)
            except Exception:
                raise Exception(
                    "Output folder already exists and is not empty. Delete manually before and try again.")
        os.mkdir(output_dir)
        self.output_dir = output_dir


class TaskSingleFileStorageSaver(TaskStorageSaver):

    def __init__(self, output_path):
        super(TaskSingleFileStorageSaver, self).__init__(output_path)
        self.samples = []

    def on_generate_start(self):
        super().on_generate_start()
        self.samples = []

    def on_new_task(self, idx, task):
        self.samples.append({
            "task_id": idx,
            "pieces": [p.to_dict() for p in task["pieces"]],
            "target": task["target"].to_dict(),
            "instr": task["instr"],
            "props": task["props"]
        })

    def on_generate_end(self):
        file_path = os.path.join(self.output_dir, f"tasks.json")
        with open(file_path, "w") as f:
            json.dump(self.samples, f)


class TaskMultiFileStorageSaver(TaskStorageSaver):

    def on_new_task(self, idx, task):
        file_path = os.path.join(self.output_dir, f"task_{idx}.json")
        with open(file_path, "w") as f:
            json.dump({
                "task_id": idx,
                "pieces": [p.to_dict() for p in task["pieces"]],
                "target": task["target"].to_dict(),
                "instr": task["instr"],
                "props": task["props"]
            }, f)


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
        self.incremental_algorithm = dynaalgos.IncrementalAlgorithm(self.property_names, config.height, config.width)

    def list_random_samples(self, n: int, n_objects=5, shuffle=False):
        return [self.generate_random_sample(n_objects, shuffle) for _ in range(n)]

    def yield_random_samples(self, n: int):
        for _ in range(n):
            yield self.generate_random_sample()

    def generate_epoch(self, number_of_samples, callbacks: list[GenerateCallback]):
        for clb in callbacks:
            clb.on_generate_start()
        for idx, _ in enumerate(tqdm(range(number_of_samples))):
            sample = self.generate_random_sample()
            for clb in callbacks:
                clb.on_new_task(idx, sample)
        for clb in callbacks:
            clb.on_generate_end()

    def generate_random_sample(self, n_objects=5, shuffle_props=False) -> dict:
        if shuffle_props:  # the discriminator is biased towards the first prop, thus you might want to re-shuffle
            random.shuffle(self.property_names)
        state, _, _ = self.generator.generate_random_state(n_objects, n_grippers=0)
        pieces = list(state.objs.values())  # this is a map
        selection = random.choice(pieces)
        instruction, props = self.incremental_algorithm.generate(pieces, selection)
        return {
            "pieces": pieces,
            "target": selection,
            "instr": instruction,  # the referring expression
            "props": props  # the discriminating properties
        }

    @classmethod
    def create(cls, n_colors=None, n_types=None):
        config = Config(dynatypes.type_config)
        if n_colors:
            config.colors = random.sample(config.colors, n_colors)
        if n_types:
            types = random.sample(list(config.type_config.keys()), n_types)
            config.type_config = dict([(t, config.type_config[t]) for t in types])
        return TaskGenerator(config)
