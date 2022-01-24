"""
Class defining roles for a dialogue game in the Pentomino domain:
    - IG: sees everything but has no gripper
    - IF: does not see targets, has one gripper
"""
from enum import Enum

class PentominoRoles(Enum):
    IG = (0, set())
    IF = (1, {"update_targets"})

    def __init__(self, n_grippers, ignore_events):
        self.n_grippers = n_grippers
        self.ignore_events = ignore_events