import json
import os
from typing import List, Tuple, Dict, Union

from model.pentomino import PropertyNames, Colors, Shapes, RelPositions, PieceConfigGroup
from model.state import State


class Reference:

    def __init__(self, user: str, utterance_type: int, utterance: str,
                 property_values: Dict[PropertyNames, Union[Colors, Shapes, RelPositions]]):
        self.property_values = property_values
        self.utterance = utterance
        self.utterance_type = utterance_type
        self.user = user

    def __str__(self):
        return self.to_json()

    def __repr__(self):
        return f"Reference({self.user}, {self.utterance})"

    def to_json(self):
        return {
            # we actually do not need to store "instr" b.c. its derivable from "props"
            # when we use a fix template anyway (and saves lot of space)
            "user": "ia",
            "instr": self.utterance,  # the referring expression
            "type": self.utterance_type,
            "props": dict([(pn.to_json(), v.to_json()) for pn, v in self.property_values.items()]),
            # Note: the preference order is fix for now
            # "props_pref": [pn.to_json() for pn in pia.preference_order],  # the preference order
        }

    @classmethod
    def __convert_json_ref_prop(cls, pn, v):
        pn = PropertyNames.from_json(pn)
        if pn == PropertyNames.COLOR:
            v = Colors.from_json(v)
        if pn == PropertyNames.SHAPE:
            v = Shapes.from_json(v)
        if pn == PropertyNames.REL_POSITION:
            v = RelPositions.from_json(v)
        return pn, v

    @classmethod
    def from_json(cls, r):
        property_values = dict([cls.__convert_json_ref_prop(pn, v) for pn, v in r["props"].items()])
        return Reference(r["user"], r["type"], r["instr"], property_values)


class Annotation:

    def __init__(self, anno_id: int, target_idx: int, group: PieceConfigGroup, refs: List[Reference],
                 bboxes: List[Tuple] = None, global_id: int = None):
        self.target_idx = target_idx
        self.refs = refs
        self.group = group
        self.anno_id = anno_id  # split-id
        self.global_id = global_id
        self.bboxes = bboxes

    def __str__(self):
        return self.to_json()

    def __repr__(self):
        if self.global_id:
            return f"Annotation(gid:{self.global_id},sid:{self.anno_id})"
        return f"Annotation(sid:{self.anno_id})"

    def to_json(self):
        d = {
            "id": self.anno_id,
            "size": len(self.group),
            "pieces": self.group.to_json(),
            "target": self.target_idx,
            "refs": [ref.to_json() for ref in self.refs]
        }
        if self.bboxes:
            d["bboxes"] = self.bboxes
        if self.global_id:
            d["global_id"] = self.global_id
        return d

    @classmethod
    def from_json(cls, json_annotation):
        refs = [Reference.from_json(r) for r in json_annotation["refs"]]
        group = PieceConfigGroup.from_json(json_annotation["pieces"])
        annos_id = json_annotation["id"]
        target_idx = json_annotation["target"]
        anno = Annotation(annos_id, target_idx, group, refs)
        if "bboxes" in json_annotation:
            anno.bboxes = json_annotation["bboxes"]
        if "global_id" in json_annotation:
            anno.global_id = json_annotation["global_id"]
        return anno


class DataCollectionState:

    def __init__(self, split_name: str, annotation: Annotation, state: State):
        assert split_name is not None
        assert annotation.anno_id == state.state_id, \
            f"Split Ids must match, but are {annotation.anno_id} != {state.state_id}"
        assert annotation.global_id is not None, f"Global Id is null for {annotation}"
        assert annotation.global_id == state.global_id, \
            f"Global Ids must match, but are {annotation.global_id} != {state.global_id}"
        self.split_name = split_name
        self.global_id = annotation.global_id
        self.state = state
        self.annotation = annotation

    def __str__(self):
        return self.to_json()

    def __repr__(self):
        return f"DataCollectionState(gid:{self.global_id})"

    def to_json(self):
        return {
            "split_name": self.split_name,
            "global_id": self.global_id,
            "annotation": self.annotation.to_json(),
            "state": self.state.to_dict()
        }

    @classmethod
    def from_json(cls, json_data):
        split_name = json_data["split_name"]
        state = State.from_dict(json_data["state"])
        annotation = Annotation.from_json(json_data["annotation"])
        return cls(split_name, annotation, state)

    @classmethod
    def load_many(cls, data_dir, file_name="data-collection", resolve=False) -> List:
        file_path = os.path.join(data_dir, f"{file_name}.states")
        with open(file_path, "r") as f:
            data = json.load(f)
            if resolve:
                states = [cls.from_json(d) for d in data]
            else:
                states = data
        print(f"Loaded {len(states)} from {file_path}")
        return states


class DataCollectionIterator:

    def __init__(self, epoch_dir: str, idx: int, file_names: List[str]):
        self.epoch_dir = epoch_dir
        self.file_names = file_names
        self.idx = idx

    def get_current_file(self):
        if self.idx >= len(self.file_names):
            raise Exception(f"DataCollectionIterator is exhausted: idx '{self.idx}' > {len(self.file_names)}")
        return self.file_names[self.idx]

    def load_current(self):
        return DataCollectionState.load_many(self.epoch_dir, self.get_current_file())

    def to_json(self):
        return {"epoch_dir": self.epoch_dir, "idx": self.idx, "files": self.file_names}

    def store(self):
        fp = os.path.join(self.epoch_dir, f"iter.json")
        with open(fp, "w") as f:
            json.dump(self.to_json(), f)

    @classmethod
    def from_json(cls, data):
        return cls(data["epoch_dir"], data["idx"], data["files"])

    @classmethod
    def load(cls, epoch_dir):
        fp = os.path.join(epoch_dir, f"iter.json")
        with open(fp, "r") as f:
            return cls.from_json(json.load(f))
