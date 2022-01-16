"""
Class that stores
    - state generation parameters
    - roles / how many instances of each role are needed
    - rol
Roles defined here
        - IG: sees targets but not gripper
        - IF: sees gripper but not targets
        - OBSERVER: sees everything
"""

import json
from os.path import exists


class GameConfig:
    def __init__(self, n_players, n_objs, role_counts,
                 area_block="all", area_target="all",
                 create_targets=False, random_gr_position=False):
        # state generation parameters
        self.n_players = n_players
        self.n_objs = n_objs
        self.area_block = area_block
        self.area_target = area_target
        self.create_targets = create_targets
        self.random_gr_position = random_gr_position
        # roles defined and required number of instances for each role
        # TODO: define a dict for each role that declares:
        # - number of grippers
        # - which updates to receive
        self.roles = {"IG", "IF", "OBSERVER"}
        self.set_role_counts(role_counts)

    def __repr__(self):
        properties = ", ".join(vars(self).keys())
        return f"GameConfig({properties})"

    def is_valid_role(self, role):
        return role in self.roles

    def set_role_counts(self, role_counts):
        for role_name, role_count in role_counts.items():
            if not self.is_valid_role(role_name):
                raise KeyError(f"Attempting to use unknown role '{role_name}'")
        self.role_counts = role_counts

    # TODO: change to use role dict
    @staticmethod
    def get_roles_ignoring_event(event_name):
        if event_name == "update_targets":
            return ["IF"]
        elif event_name == "update_grippers":
            return list()
        else:
            return list()

    # TODO: change to use role dict
    @staticmethod
    def role_requires_gripper(role):
        return role in {"IF"}

    # TODO: read in role definitions
    @classmethod
    def from_json(cls, filename):
        """
        @param filename String, name of a json file describing a GameConfig.
        @return new GameConfig instance with the given attributes
        """
        if not isinstance(filename, str):
            raise TypeError("filename must be of type str")
        elif not exists(filename):
            raise ValueError(f"file with path {filename} not found")

        with open(filename, mode="r") as file:
            json_data = json.loads(file.read())

        # remove comments marked by underscores
        json_data = GameConfig.remove_json_comments(json_data)
        return cls.from_dict(json_data)

    # TODO: read in role definitions
    @classmethod
    def from_dict(cls, source_dict):
        """
        @param source_dict  Dictionary containing GameConfig constructor
                            parameters.
        @return new GameConfig instance with the given attributes
        """
        if not isinstance(source_dict, dict):
            raise TypeError("source_dict must be of type dict")
        # use source_dict as kwargs to construct a config object
        return cls(**source_dict)

    def to_dict(self):
        """
        Constructs a dictionary from this instance.
        """
        return {
            key: value for key, value in vars(self).items()
            if not key.startswith("_")
        }

    @staticmethod
    def remove_json_comments(parsed_json):
        return {
            key: value for key, value in parsed_json.items()
            if not key.startswith("_")
        }
