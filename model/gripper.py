from obj import Obj

class Gripper(Obj):
	def __init__(self, x, y, gripped=None, width=1, height=1, color="blue"):
		Obj.__init__(self, "gripper", x, y, width, height, [[1]], rotation=0, mirrored=False, color=color)
		self.gripped 	= gripped # None or id of gripped object