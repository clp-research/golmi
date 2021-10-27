class Obj:
	def __init__(self, obj_type, x, y, width, height, block_matrix, 
		rotation=0, mirrored=False, color="blue", gripped=False): 
		self.type			= obj_type
		self.x				= x
		self.y				= y
		assert len(block_matrix) > 0, "Error: Empty block matrix passed to Obj constructor"
		self.width			= len(block_matrix[0])
		self.height			= len(block_matrix)
		self.rotation		= rotation
		self.mirrored		= mirrored
		self.color			= color
		self.block_matrix 	= block_matrix
		self.gripped 		= gripped

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
			"type": self.type,
			"x": self.x,
			"y": self.y,
			"width": self.width,
			"height": self.height,
			"rotation": self.rotation,
			"mirrored": self.mirrored,
			"color": self.color,
			"block_matrix": self.block_matrix,
			"gripped": self.gripped
			}
