class State:
	def __init__(self):
		self.objs = dict() # maps ids to Objs
		self.grippers = dict()
		
	def get_objects(self):
		"""
		@return Dictionary mapping object ids to object dictionaries
		"""
		return {obj_id: obj.to_dict() for obj_id, obj in self.objs.items()}

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

	def get_grippers(self):
		"""
		In contrast to get_objects, each gripper dict has the entry "gripped", which itself
		is None or a dictionary mapping the gripped object to an object dictionary.
		@return Dictionary mapping gripper ids to gripper dictionaries.
		"""
		gr_dict = dict()
		for gr_id, gr in self.grippers.items():
			gr_dict[gr_id] = gr.to_dict()
			# if some object is gripped, add all the info on that object too
			if gr.gripped:
				gr_dict[gr_id]["gripped"] = {gr.gripped: self.get_obj_by_id(gr.gripped).to_dict()}
			else:
				gr_dict[gr_id]["gripped"] = None
		return gr_dict

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
	 	@param id 	object id
	 	@param dx 	x direction
	 	@param dy 	y direction
		"""
		self.get_obj_by_id(id).x += dx
		self.get_obj_by_id(id).y += dy

	def rotate_obj(self, id, d_angle):
		"""
		Change an object's goal_rotation by d_angle.
		@param id  	object id
		@param d_angle	current angle is changed by d_angle
		"""
		if d_angle != 0:
			obj = self.get_obj_by_id(id)
			obj.rotation = (obj.rotation + d_angle) % 360
			# update block matrix
			obj.block_matrix = self._rotate_block_matrix(obj.block_matrix, d_angle)

	def flip_obj(self, id):
		"""
		Mirror an object.
		@param id 	object_id
		"""
		# change 'mirrored' attribute
		obj = self.get_obj_by_id(id)
		obj.mirrored = not obj.mirrored
		# update the block matrix (function _flip_block_matrix flips in-place)
		self._flip_block_matrix(obj.block_matrix)
	
	def grip(self, gr_id, obj_id):
		"""
		Attach a given object to the gripper.
		@param gr_id 	id of the gripper that grips obj_id
		@param obj_id 	id of object to grip, must be in objects
	 	"""
		self.grippers[gr_id].gripped = obj_id
	
	def ungrip(self, id):
		"""
		Detach the currently gripped object from the gripper.
		@param id 	id of the gripper that ungrips
		"""
		self.grippers[id].gripped = None

	def _rotate_block_matrix(self, old_matrix, d_angle):
		"""
		Rearrange blocks of a 0/1 block matrix to apply some rotation.
		@param old_matrix 	block matrix describing the current block positions
		@param d_angle 	float or int, angle to apply. Can be negative for leftwards rotation.
		@return the new block matrix with changed block position
		"""
		# normalize the angle (moves all values in the range [0-360[ )
		d_angle = d_angle % 360
		# can only process multiples of 90, so round to the next step here
		approx_angle = round(d_angle/90) * 90
		# nothing to do if rotation is 0
		if approx_angle == 0: return old_matrix
		# start building a new, rotated matrix
		new_matrix = list()
		height = len(old_matrix)
		assert height > 0, "Error: Empty block matrix passed to _rotate_block_matrix() at class State"
		width = len(old_matrix[0])
		assert width > 0, "Error: Block matrix with empty rows passed to _rotate_block_matrix() at class State"
		for row in range(height):
			# new empty row
			new_matrix.append(list())
			for col in range(width):
				# fill out the new matrix by copying values of the old matrix
				if approx_angle == 90:
					new_matrix[row].append(old_matrix[(width-1)-col][row])
				elif approx_angle == 180:
					new_matrix[row].append(old_matrix[(height-1)-row][(width-1)-col])
				elif approx_angle == 270:
					new_matrix[row].append(old_matrix[col][(height-1)-row])
				else:
					print("Error: Invalid turning angle at _rotateByRearrange(): " + approx_angle)
		return new_matrix

	def _flip_block_matrix(self, old_matrix):
		"""
		Flips blocks using a horizontal axis of reflection. *IN PLACE*
		@param old_matrix 	block matrix describing the current block positions
		"""
		# simply reverse the order of rows
		old_matrix.reverse()