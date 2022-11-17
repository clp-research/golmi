import numpy as np


class Obj:
    def __init__(
            self, id_n, obj_type, x, y, block_matrix=[],
            rotation=0, mirrored=False, color="blue", gripped=False):
        self.id_n = id_n
        self.type = obj_type
        self.x = x
        self.y = y
        if not len(block_matrix) > 0:
            raise ValueError("Empty block matrix passed to Obj constructor")
        self.width = len(block_matrix[0])
        self.height = len(block_matrix)
        self.rotation = rotation
        self.mirrored = mirrored
        self.color = color
        self.block_matrix = block_matrix
        self.gripped = gripped

    def __repr__(self):
        return f"Object({self.type})"

    def get_center_x(self):
        return self.x + (self.width / 2)

    def get_center_y(self):
        return self.y + (self.height / 2)

    def get_left_edge(self):
        return self.x

    def get_right_edge(self):
        return self.x + self.width

    def get_top_edge(self):
        return self.y

    def get_bottom_edge(self):
        return self.y + self.height

    def occupied(self, x=None, y=None, matrix=None):
        """
        calculates coordinates of occupied fields based on
        the central coordinates and the block matrix
        if x and y are given, consider these as the center of
        the block matrix
        """
        obj_x = self.x
        obj_y = self.y
        block_matrix = self.block_matrix

        # overwrite parameters if they are given as arguments
        if x is not None:
            obj_x = x
        if x is not None:
            obj_y = y

        if matrix:
            block_matrix = matrix

        occupied = list()
        for y, line in enumerate(block_matrix):
            for x, cell in enumerate(line):
                if cell == 1:
                    cell_x = obj_x + x
                    cell_y = obj_y + y
                    occupied.append({"y": cell_y, "x": cell_x})
        return occupied

    def rotate(self, d_angle):
        """
        Rotate an object instance *in-place*.
        @param d_angle	current angle is changed by d_angle
        """
        # update rotation angle
        self.rotation = (self.rotation + d_angle) % 360

        # update block matrix
        self.block_matrix = Obj.rotate_block_matrix(
            self.block_matrix, d_angle
        )

    def flip(self):
        """
        Mirror an object *in-place*
        """
        # update mirrored parameter
        self.mirrored = not self.mirrored

        # update the block matrix
        self.block_matrix = Obj.flip_block_matrix(self.block_matrix)

    @staticmethod
    def rotate_block_matrix(old_matrix, d_angle):
        """
        Rearrange blocks of a 0/1 block matrix to apply some rotation.
        Rotations are applied clockwise.
        @param old_matrix 	block matrix describing the current block positions
        @param d_angle 	    float or int, angle to apply.
                            Can be negative for leftwards rotation.
        @return the new block matrix with changed block position
        """
        # normalize the angle (moves all values in the range [0-360])
        d_angle = d_angle % 360

        # can only process multiples of 90, so round to the next step here
        approx_angle = round(d_angle / 90) * 90

        # nothing to do if rotation is 0
        if approx_angle == 0:
            return old_matrix

        # otherwise compute rotation with numpy
        matrix = np.array(old_matrix)

        # choose k parameters for np.rot90
        # k = how often a COUNTERclockwise rotation will be applied
        angle_to_k = {
            90: 3,
            180: 2,
            270: 1
        }

        # apply rotation and return matrix as a python list
        k = angle_to_k[approx_angle]
        return np.rot90(matrix, k).tolist()

    @staticmethod
    def flip_block_matrix(old_matrix):
        """
        Flips blocks using a horizontal axis of reflection.
        @param old_matrix 	block matrix describing the current block positions
        @return a new block matrix with 1s in horizontally mirrored positions
        """
        matrix = np.array(old_matrix)
        return np.flip(matrix, axis=0).tolist()

    @classmethod
    def from_dict(cls, id_n, source_dict, type_config=None):
        """
        Construct a new Obj instance from a dictionary, e.g., parsed json.
        @param id_n identifier for the object
        @param source_dict  dict containing object attributes, keys "type",
                            "x", "y", "width", "height" are mandatory
        @param type_config  dict mapping type names to block matrices
        @return new Obj instance with the given attributes
        """
        # make sure mandatory keys are part of dictionary
        mandatory_key = {"type", "x", "y"}
        if any(source_dict.get(key) is None for key in mandatory_key):
            raise KeyError(
                f"Object construction failed, key {mandatory_key} missing"
            )
        bm = None
        apply_transformations = False
        if type_config:
            bm = type_config[source_dict["type"]]
            apply_transformations = True
        if "block_matrix" in source_dict:
            bm = source_dict["block_matrix"]
            apply_transformations = False
        if not bm:
            raise Exception("Either provide type_config or block_matrix")
        # create new object from the mandatory keys
        new_obj = cls(
            id_n=id_n,
            obj_type=source_dict["type"],
            x=float(source_dict["x"]),
            y=float(source_dict["y"]),
            block_matrix=bm
        )

        if apply_transformations is True:
            # process optional info
            if "rotation" in source_dict and source_dict["rotation"] != 0:
                new_obj.rotate(float(source_dict["rotation"]))

            # flip the object if "mirrored" is true in the dictionary
            if "mirrored" in source_dict and source_dict["mirrored"]:
                new_obj.flip()

        # apply color
        if "color" in source_dict:
            new_obj.color = source_dict["color"]

        # apply gripped
        if "gripped" in source_dict:
            new_obj.gripped = source_dict["gripped"]

        return new_obj

    def to_dict(self):
        """
        Constructs a JSON-friendly dictionary representation of this instance.
        @return dictionary containing all important properties
        """
        d = {
            "id_n": self.id_n,
            "type": self.type,
            "x": self.x,
            "y": self.y,
            "rotation": self.rotation,
            "color": self.color,
            "block_matrix": self.block_matrix
        }
        if self.mirrored:
            d["mirrored"] = self.mirrored
        if self.gripped:
            d["gripped"] = self.gripped
        return d
