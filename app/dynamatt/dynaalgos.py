import random

from model.obj import Obj


class IncrementalAlgorithm:

    def __init__(self, height: int, width: int):
        self.width = width
        self.height = height
        self.general_types = ["piece"]
        self.start_tokens = ["Take", "Select", "Get"]

    def generate(self, property_names: list[str], pieces: list[Obj], selection: Obj):
        """
            pieces: a list of pieces (incl. the selection)
            selection: a selected pieces (within pieces)
        """
        distractors = set(pieces)
        distractors.remove(selection)
        # property-value pairs are collected here
        properties = {}
        for property_name in property_names:
            property_value = self._find_value(selection, property_name)
            # check what objects would be eliminated using this prop-val pair
            excluded_distractors = self._exclude(property_name, property_value, distractors)
            if property_value and len(excluded_distractors) > 0:
                # save the property
                properties[property_name] = property_value
                # update the contrast set
                for o in excluded_distractors:
                    distractors.remove(o)
            # check if enough properties have been collected to rule all distractors
            if not len(distractors):
                return self._verbalize_properties(properties), properties
        # no expression that rules out all distractors was found
        # original algorithm declares "IA: failure", but with the task at hand
        # this case is expected. User is supported by feedback.
        return self._verbalize_properties(properties), properties

    def _verbalize_properties(self, properties):
        start_token = random.choice(self.start_tokens)
        shape = properties["shape"] if "shape" in properties else random.choice(self.general_types)
        color = properties["color"] if "color" in properties else ""
        pos = f"in the {properties['posRelBoard']}" if "posRelBoard" in properties else ""
        ref_exp = f"{color} {shape} {pos}".strip()  # strip whitespaces if s.t. is empty
        return f"{start_token} the {ref_exp}"

    def _exclude(self, property_name: str, selection_property_value, distractors: set[Obj]):
        """
         * Helper function for IA.
         * Params:
         * property_name - property name
         * selection_property_value - value the target object has assigned to the given property
         * distractors - contrast set of objects to rule out by the given properties
         * Returns:
         * array of contrast objects with a different value for prop
        """
        excluded_distractors = []
        for distractor in distractors:
            if self._find_value(distractor, property_name) != selection_property_value:
                excluded_distractors.append(distractor)
        return excluded_distractors

    def _find_value(self, obj: Obj, property_name: str):
        """
         * Determine the value an <Obj> has for a given property name.
         * Logs an error if the given property name is not implemented.
         * Params:
         * obj - IGView's representation of a GOLMI <Obj>
         * prop - _str_, property name
         * Returns: _str_, value matching _obj_
        """
        if property_name == "shape":
            return obj.type
        if property_name == "color":
            return obj.color
        if property_name == "posRelBoard":
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
            return pos
        raise Exception(f"Cannot resolve property with name: {property_name}")
