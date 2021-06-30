from gripper import Gripper
from obj import Obj
import json
class State:
	def __init__(self, json_data=None):
		self.objs = dict() # maps ids to Objs
		self.grippers = dict()
		if json_data: 
			self.from_JSON(json_data)
		
	def get_objects(self):
		return self.objs

	def get_object_ids(self): 
		return self.objs.keys()
	
	def get_obj_by_id(self, id): 
		"""
		@param id 	gripper id
		"""
		if id in self.objs:
			return self.objs[id]
		else:
			return None

	def get_gripper_ids(self):
		return self.grippers.keys()

	def get_gripper_by_id(self, id):
		if id in self.grippers:
			return self.grippers[id]
		else:
			return None
	
	def get_gripper_coords(self, id):
		"""
		@param id 	gripper id
		"""
		if id in self.grippers:
			return [self.grippers[id].x, self.grippers[id].y]
		else:
			return list()

	# returns None if no object is gripped
	def get_gripped_obj(self, id): 
		"""
		@param id 	gripper id 
		"""
		if id in self.grippers:
			return self.grippers[id].gripped
		else:
			return None
	
	def move_gr(self, id, dx, dy):
		"""
		Change gripper position by moving in direction (dx, dy).
		@param id 	id of the gripper to move
	 	@param dx 	x direction
		@param dy 	y direction 
		"""
		self.grippers[id].x += dx
		self.grippers[id].y += dy
	
	def move_obj(self, id, dx, dy):
		"""
	 	Change an object's position by moving in direction (dx, dy).
	 	@param dx 	x direction
	 	@param dy 	y direction
		"""
		self.get_obj_by_id(id).x += dx
		self.get_obj_by_id(id).y += dy
	
	def grip(self, gr_id, obj_id):
		"""
		Attach a given object to the gripper.
		@param id 	id of object to grip, must be in objects
	 	"""
		self.grippers[gr_id].gripped = obj_id
	
	def ungrip(self, id):
		"""
		Detach the currently gripped object from the gripper.
		"""
		self.grippers[id].gripped = None
	

	# TODO: make sure pieces are on the board! (at least emit warning)
	def from_JSON(self, json_data):
		if type(json_data) == str:
			# a JSON string
			json_data = json.loads(json_data)
		# otherwise assume json_data is a dict 
		try:
			# construct gripper(s)
			self.grippers = dict()
			for gr in json_data["grippers"]:
				self.grippers[gr] = Gripper(
					json_data["grippers"][gr]["x"],
					json_data["grippers"][gr]["y"])
				# process optional info
				if "gripped" in json_data["grippers"][gr]:
					self.grippers[gr].gripped = json_data["grippers"][gr]["gripped"]
				if "width" in json_data["grippers"][gr]:
					self.grippers[gr].width = json_data["grippers"][gr]["width"]
				elif "height" in json_data["grippers"][gr]:
					self.grippers[gr].height = json_data["grippers"][gr]["height"]
				elif "color" in json_data["grippers"][gr]:
					self.grippers[gr].color = json_data["grippers"][gr]["color"]
			# delete old objects
			self.objs = dict()
			# construct objects
			for obj in json_data["objs"]:
				self.objs[obj] = Obj(
					json_data["objs"][obj]["type"],
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
			raise SyntaxError("Error during state initialization: JSON data does not have the right format.\n" + \
				"Please refer to the documentation.")