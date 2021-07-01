class Obj:
	def __init__(self, obj_type, x, y, width, height, rotation=0, mirrored=False, color="blue"): 
		self.type		= obj_type
		self.x			= x
		self.y			= y
		self.width		= width
		self.height		= height
		self.rotation	= rotation
		self.mirrored	= mirrored
		self.color		= color

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