from gripper import Gripper
from obj import Obj
import json
class State:
	def __init__(self, json_data=None):
		self.objs = dict() # maps ids to Objs
		# TODO: mutliple grippers?
		self.gripper = Gripper(0,0)
		if json_data: 
			self.from_JSON(json_data)
		
	def get_objects(self):
		return self.objs.values()
	

	def get_object_ids(self): 
		return self.objs.keys()
	
	def get_obj_by_id(self, id): 
		return self.objs[id]
	
	def get_gripper_coords(self):
		return [self.gripper.x, self.gripper.y]

	# returns None if no object is gripped
	def get_gripped_obj(self): 
		return self.gripper.gripped
	
	def move_gr(self, dx, dy):
		"""
		Change gripper position by moving in direction (dx, dy).
	 	@param dx 	x direction
		@param dy 	y direction 
		"""
		self.gripper.x += dx
		self.gripper.y += dy
	
	def move_obj(self, id, dx, dy):
		"""
	 	Change an object's position by moving in direction (dx, dy).
	 	@param dx 	x direction
	 	@param dy 	y direction
		"""
		self.get_obj_by_id(id).x += dx
		self.get_obj_by_id(id).y += dy
	
	def grip(self, id):
		"""
		Attach a given object to the gripper.
		@param id 	id of object to grip, must be in objects
	 	"""
		self.gripper.gripped = id
	
	def ungrip(self):
		"""
		Detach the currently gripped object from the gripper.
		"""
		self.gripper.gripped = None
	

	# TODO: make sure pieces are on the board! (at least emit warning)
	def from_JSON(self, json_data):
		# as JSON string
		json_data = json.loads(json_data)
		try:
			# construct gripper
			self.gripper = Gripper(
				json_data["gripper"]["x"],
				json_data["gripper"]["y"])
			# process optional info
			if "gripped" in json_data["gripper"]:
				self.gripper.gripped = json_data["gripper"]["gripped"]
			if "width" in json_data["gripper"]:
				self.gripper.width = json_data["gripper"]["width"]
			elif "height" in json_data["gripper"]:
				self.gripper.height = json_data["gripper"]["height"]
			elif "color" in json_data["gripper"]:
				self.gripper.color = json_data["gripper"]["color"]
			# delete old objects
			self.objs = dict()
			# construct objects
			for obj in json_data["objs"]:
				self.objs[obj] = Obj(
					json_data["objs"][obj]["obj_type"],
					json_data["objs"][obj]["x"],
					json_data["objs"][obj]["y"],
					json_data["objs"][obj]["width"],
					json_data["objs"][obj]["height"])
				# process optional info
				if "rotation" in json_data["objs"][obj]:
					self.objs[obj].rotation = json_data["objs"][obj]["rotation"] 
				if "mirrored" in json_data["objs"][obj]: 
					self.objs[obj].mirrored = json_data["objs"][obj]["mirrored"]
				if "color" in json_data["objs"][obj]:
					self.objs[obj].color = json_data["objs"][obj]["color"]
		except: 
			print("error")
			pass
		#raise Exception!