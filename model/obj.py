class Obj:
    def __init__(
            self, id_n, obj_type, x, y, width, height, block_matrix,
            rotation=0, mirrored=False, color="blue", gripped=False,
            is_target=False):
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
        self.target = None

    def __repr__(self):
        return f"Object({self.type})"

    def get_center_x(self):
        return self.x + (self.width/2)

    def get_center_y(self):
        return self.y + (self.height/2)

    def get_left_edge(self):
        return self.x

    def get_right_edge(self):
        return self.x + self.width

    def get_top_edge(self):
        return self.y

    def get_bottom_edge(self):
        return self.y + self.height

    def to_dict(self):
        """
        Constructs a JSON-friendly dictionary representation of this instance.
        @return dictionary containing all important properties
        """
        return {
            "id_n":         self.id_n,
            "type":			self.type,
            "x":			self.x,
            "y":			self.y,
            "width":		self.width,
            "height":		self.height,
            "rotation":		self.rotation,
            "mirrored":		self.mirrored,
            "color":		self.color,
            "block_matrix":	self.block_matrix,
            "gripped":		self.gripped
        }

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

    def is_on_target(self):
        """
        check whether the object is on target
        """
        if self.target is not None:
            target_coordinates = self.target.occupied()
            current_coordinates = self.occupied()
            if target_coordinates == current_coordinates:
                return True

        return False
