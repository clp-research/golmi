class Obj:
	def __init__(self, obj_type, x, y, width, height, block_matrix, rotation=0, mirrored=False, color="blue"): 
		self.type			= obj_type
		self.x				= x
		self.y				= y
		self.width			= width
		self.height			= height
		self.rotation		= rotation
		self.mirrored		= mirrored
		self.color			= color
		self.block_matrix 	= block_matrix

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
		Constructs a dictionary from this instance.
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
			"block_matrix": self.block_matrix
			}