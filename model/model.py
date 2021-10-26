from model.state import State
from model.gripper import Gripper
from model.obj import Obj
from math import floor, ceil 
import eventlet

class Model:
	def __init__(self, config, socket, room):
		self.socket = socket # to communicate with subscribed views
		self.room = room
		self.state = State()
		self.config = config

		# Contains a dictionary for each available action. The nested dicts map
		# gripper ids to True or False, depending on whether the respective
		# action is currently running (= repeatedly executed)
		self.running_loops = {action: dict() for action in self.config.actions}

	# --- getter --- #

	def get_obj_dict(self):
		return self.state.get_obj_dict()

	def get_object_ids(self):
		return self.state.get_object_ids()

	def get_obj_by_id(self, id):
		return self.state.get_obj_by_id(id)

	def get_gripper_dict(self):
		return self.state.get_gripper_dict()

	def get_gripper_ids(self):
		return self.state.get_gripper_ids()

	def get_gripper_by_id(self, id):
		"""
		@return Gripper instance or None if id is not registered
		"""
		return self.state.get_gripper_by_id(id)

	def get_gripped_obj(self, id):
		return self.state.get_gripped_obj(id)

	def get_gripper_coords(self, id):
		"""
		@return list: [x-coordinate, y-coordinate]
		"""
		return self.state.get_gripper_coords(id)

	def get_config(self):
		return self.config.to_dict()

	def get_width(self):
		return self.config.width

	def get_height(self):
		return self.config.height

	def get_type_config(self):
		return self.config.type_config

	# --- Communicating with views --- # 

	def _notify_views(self, event_name, data):
		"""
		Notify all listening views of model events (usually data updates)
		@param event_name 	str: event type, e.g. "update_grippers"
		@param data 	serializable data to send to listeners
		"""
		self.socket.emit(event_name, data, room=self.room)

	# --- Set up and configuration --- #

	def set_state(self, state):
		"""
		Initialize the model's (game) state.
		@param state	State object or dict or JSON string
		"""
		# state is a JSON string or parsed JSON dictionary
		if type(state) == str or type(state) == dict:
			self._state_from_JSON(state)
		# state is a State instance
		else:
			self.state = state
		self._notify_views("update_state", self.state.to_dict())

	def set_config(self, config):
		"""
		Change the model's configuration. Overwrites any attributes
		passed in config and leaves the rest as before. New keys simply added.
		@param config	Config object or dict or JSON string
		"""
		# config is a JSON string or parsed JSON dictionary
		if type(config) == str or type(config) == dict:
			self._config_from_JSON(config)
		# config is a Config instance
		else:
			self.config = config
		# in case the available actions changed, reset the looped actions
		self.reset_loops()
		self._notify_views("update_config", self.config.to_dict())

	def reset(self):
		"""
		Reset the current state.
		"""
		self.state = State()
		self.reset_loops()
		self._notify_views("update_state", self.state.to_dict())

	# TODO: make sure pieces are on the board! (at least emit warning)
	def _state_from_JSON(self, json_data):
		if type(json_data) == str:
			# a JSON string
			json_data = json.loads(json_data)
		# otherwise assume json_data is a dict 
		try:
			# initialize an empty state
			self.state = State()
			# construct objects
			if "objs" in json_data and type(json_data["objs"]) == dict:
				for obj_name in json_data["objs"]:
					obj = str(obj_name) # use string identifiers only for consistency
					self.state.objs[obj] = Obj(
						json_data["objs"][obj]["type"],
						float(json_data["objs"][obj]["x"]),
						float(json_data["objs"][obj]["y"]),
						float(json_data["objs"][obj]["width"]),
						float(json_data["objs"][obj]["height"]),
						self.get_type_config()[json_data["objs"][obj]["type"]] # block matrix for given type
					)
					# process optional info
					if "rotation" in json_data["objs"][obj]:
						# rotate the object
						self.state.rotate_obj(obj, float(json_data["objs"][obj]["rotation"]))
					if "mirrored" in json_data["objs"][obj] and json_data["objs"][obj]["mirrored"]:
						# flip the object if "mirrored" is true in the JSON
						self.state.flip_obj(obj)
					if "color" in json_data["objs"][obj]:
						self.state.objs[obj].color = json_data["objs"][obj]["color"]
			# construct grippers
			if "grippers" in json_data and type(json_data["grippers"]) == dict:
				for gr_name in json_data["grippers"]:
					gr = str(gr_name) # use string identifiers only for consistency
					self.state.grippers[gr] = Gripper(
						float(json_data["grippers"][gr]["x"]),
						float(json_data["grippers"][gr]["y"]))
					# process optional info
					if "gripped" in json_data["grippers"][gr]:
						# cast object name to str, too
						gripped_id = str(json_data["grippers"][gr]["gripped"])
						self.state.grippers[gr].gripped = gripped_id
						self.state.objs[gripped_id].gripped = True
					if "width" in json_data["grippers"][gr]:
						self.state.grippers[gr].width = json_data["grippers"][gr]["width"]
					elif "height" in json_data["grippers"][gr]:
						self.state.grippers[gr].height = json_data["grippers"][gr]["height"]
					elif "color" in json_data["grippers"][gr]:
						self.state.grippers[gr].color = json_data["grippers"][gr]["color"]
		except: 
			raise SyntaxError("Error during state initialization: JSON data does not have the right format.\n" + \
				"Please refer to the documentation.")

	def _config_from_JSON(self, json_data):
		if type(json_data) == str:
			# a JSON string
			json_data = json.loads(json_data)
		# otherwise assume json_data is a dict 
		# overwrite any setting given in the data, leave the rest as before.
		# new keys are also allowed
		for attr_key, attr_value in json_data.items():
			setattr(self.config, attr_key, attr_value)

	# --- Gripper manipulation --- #

	def add_gr(self, gr_id):
		"""
		Add a new gripper to the internal state. The start position is the center. Notifies listeners.
		@param gr_id 	identifier for the new gripper
		"""
		start_x = self.get_width()/2
		start_y = self.get_height()/2
		# if a new gripper was created, notify listeners
		if gr_id not in self.state.grippers:
			self.state.grippers[gr_id] = Gripper(start_x, start_y)
			self._notify_views("update_grippers", self.get_gripper_dict())

	def remove_gr(self, gr_id):
		"""
		Delete a gripper from the internal state and notify listeners.
		@param gr_id 	identifier of the gripper to remove
		"""
		if gr_id in self.state.grippers:
			self.state.grippers.pop(gr_id)
			self._notify_views("update_grippers", self.get_gripper_dict())

	def start_gripping(self, id):
		"""
		Start calling the function grip periodically until stop_gripping is called, essentially 
		repeatedly gripping / ungripping with a specified gripper.
		@param id 	gripper id
		"""
		self.stop_gripping(id)
		self.start_loop("grip", id, self.grip, id)

	def stop_gripping(self, id):
		"""
		Stop periodically gripping.
		@param id 	gripper id
		"""
		self.stop_loop("grip", id)

	def grip(self, id):
		"""
		Attempt a grip / ungrip.
		@param id 	gripper id
		"""
		# if some object is already gripped, ungrip it
		old_gripped = self.get_gripped_obj(id)
		if old_gripped:
			# state takes care of detaching object and gripper
			self.state.ungrip(id)
			# notify view of object and gripper change
			self._notify_views("update_objs", self.get_obj_dict())
			self._notify_views("update_grippers", self.get_gripper_dict())
		else: 
			# Check if gripper hovers over some object
			new_gripped = self._get_grippable(id)
			# changes to object and gripper
			if new_gripped: 
				self.state.grip(id, new_gripped)
				# notify view of object and gripper change
				self._notify_views("update_objs", self.get_obj_dict())
				self._notify_views("update_grippers", self.get_gripper_dict())

	def start_moving(self, id, x_steps, y_steps, step_size=None):
		"""
		Start calling the function move periodically until stop_moving is called.
		@param id 	gripper id
		@param x_steps	steps to move in x direction. Step size is defined by model configuration
		@param y_steps	steps to move in y direction. Step size is defined by model configuration
		@param step_size 	Optional: size of step unit in blocks. Default: use move_step of config
		"""
		# cancel any ongoing movement
		self.stop_moving(id)
		self.start_loop("move", id, self.move, id, x_steps, y_steps, step_size)

	def stop_moving(self, id):
		"""
		Stop calling move periodically.
		@param id 	gripper id
		"""
		self.stop_loop("move", id)

	def move(self, id, x_steps, y_steps, step_size=None):
		"""
		If allowed, move the gripper x_steps steps in x direction and y_steps steps in y direction.
		Only executes if the goal position is inside the game dimensions. Notifies views of change.
		@param id 	gripper id
		@param x_steps	steps to move in x direction. Step size is defined by model configuration
		@param y_steps	steps to move in y direction. Step size is defined by model configuration
		@param step_size 	Optional: size of step unit in blocks. Default: use move_step of config
		"""
		# if no step_size was given, query the config
		if not step_size: step_size = self.config.move_step
		dx = x_steps*step_size # distance in x direction to move
		dy = y_steps*step_size # distance in y direction to move
		gripper_x, gripper_y = self.get_gripper_coords(id)
		gr_obj_id = self.get_gripped_obj(id)
		if gr_obj_id:
			gr_obj = self.get_obj_by_id(gr_obj_id)
			# if an object is gripped, three conditions have to be met:
			# 1. gripper stays on the board
			# 2. object stays on the board
			# 3. object does not overlap with another object
			if self._is_in_limits(gripper_x+dx, gripper_y+dy) and \
				self._is_in_limits(gr_obj.get_center_x()+dx, gr_obj.get_center_y()+dy) and \
				not (self.config.prevent_overlap and self._has_overlap(gr_obj_id, gr_obj.x+dx, gr_obj.y+dy, gr_obj.block_matrix)):
				
				self.state.move_gr(id, dx, dy)
				self.state.move_obj(self.get_gripped_obj(id), dx, dy)
				# notify the views. A gripped object is implicitly redrawn.
				self._notify_views("update_grippers", self.get_gripper_dict())

		# if no object is gripped, only move the gripper
		elif self._is_in_limits(gripper_x + dx, gripper_y + dy):
			self.state.move_gr(id, dx, dy)
			# notify the views. A gripped object is implicitly redrawn. 
			self._notify_views("update_grippers", self.get_gripper_dict())

	def start_rotating(self, id, direction, step_size=None):
		"""
		Start calling the function rotate periodically until stop_rotating is called.
		@param id 	id of the gripper whose gripped object should be rotated
		@param direction	-1 for leftwards rotation, 1 for rightwards rotation
		@param step_size	Optional: angle to rotate per step. Default: use rotation_step of config
		"""
		# cancel any ongoing rotation
		self.stop_rotating(id)
		self.start_loop("rotate", id, self.rotate, id, direction, step_size)

	def stop_rotating(self, id):
		"""
		Stop calling rotate periodically.
		@param id 	gripper id
		"""
		self.stop_loop("rotate", id)

	def rotate(self, id, direction, step_size=None):
		"""
		If the gripper 'id' currently grips some object, rotate this object one step.
		@param id 	id of the gripper whose gripped object should be rotated
		@param direction	-1 for leftwards rotation, 1 for rightwards rotation
		@param step_size	Optional: angle to rotate per step. Default: use rotation_step of config
		"""
		# check if an object is gripped
		gr_obj_id = self.get_gripped_obj(id) 
		if gr_obj_id:
			gr_obj = self.get_obj_by_id(gr_obj_id)
			# if not step_size was given, use the default from the configuration
			if not step_size: step_size = self.config.rotation_step
			# determine the turning angle
			d_angle = direction * step_size
			# rotate the matrix and check whether the new block positions are legal (-> no overlaps)
			rotated_matrix = self.state.rotate_block_matrix(gr_obj.block_matrix, d_angle)
			if not (self.config.prevent_overlap and self._has_overlap(gr_obj_id, gr_obj.x, gr_obj.y, rotated_matrix)):
				self.state.rotate_obj(gr_obj_id, d_angle, rotated_matrix)
				# notify the views. The gripped object is implicitly redrawn. 
				self._notify_views("update_grippers", self.get_gripper_dict())

	def start_flipping(self, id):
		"""
		Start calling the function flip periodically until stop_flipping is called.
		@param id 	id of the gripper whose gripped object should be flipped
		"""
		# cancel any ongoing flipping
		self.stop_flipping(id)
		self.start_loop("flip", id, self.flip, id)

	def stop_flipping(self, id):
		"""
		Stop calling flip periodically.
		@param id 	gripper id
		"""
		self.stop_loop("flip", id)

	def flip(self, id):
		"""
		Mirror the object currently gripped by some gripper.
		@param id 	gripper id
		"""
		# check if an object is gripped
		gr_obj_id = self.get_gripped_obj(id) 
		if gr_obj_id:
			gr_obj = self.get_obj_by_id(gr_obj_id)
			# flip the matrix, then check whether the new block positions are legal (-> no overlaps)
			flipped_matrix = self.state.flip_block_matrix(gr_obj.block_matrix)
			if not (self.config.prevent_overlap and self._has_overlap(gr_obj_id, gr_obj.x, gr_obj.y, flipped_matrix)):
				self.state.flip_obj(gr_obj_id, flipped_matrix)
				# notify the views. The gripped object is implicitly redrawn. 
				self._notify_views("update_grippers", self.get_gripper_dict())
		
	def _get_grippable(self, gr_id):
		"""
		Find an object that is in the range of the gripper.
		@param id 	gripper id 
		@return id of object to grip or None
		"""
		# Gripper position. It is just a point.
		x, y = self.get_gripper_coords(gr_id)
		for obj_id in self.get_object_ids(): 
			obj = self.get_obj_by_id(obj_id)
			# (gridX, gridY) is the position on the type grid the gripper would be on
			grid_x = floor(x-obj.x)
			grid_y = floor(y-obj.y)
			# get the object block matrix - rotation and flip are already applied to the matrix
			type_matrix = obj.block_matrix

			# check whether the gripper is on the object matrix
			if grid_x >= 0 and grid_y >= 0 and grid_y < len(type_matrix) and grid_x < len(type_matrix[0]):
				# check whether a block is present at the grid position
				if type_matrix[grid_y] and type_matrix[grid_y][grid_x]: 
					return obj_id
		return None
		
	def _is_in_limits(self, x, y):
		"""
		Check whether given coordinates are within the space limits.
		@param x 	x coordinate to check
		@param y 	y coordinate to check
		@return true if both coordinates are on the board
		"""
		return self._x_in_limits(x) and self._y_in_limits(y)
		
	def _x_in_limits(self, x):
		"""
		Check whether given x coordinate is within the space limits.
		@param x 	x coordinate to check
		@return true if the x coordinate is on the board
		"""
		return (x >= 0 and x<= self.get_width())
		
	def _y_in_limits(self, y):
		"""
		Check whether given y coordinate is within the space limits.
		@param y 	y coordinate to check
		@return true if the y coordinate is on the board
		"""
		return (y >= 0 and y <= self.get_height())

	# this function is extremely unelegant. feel free to change for a better implementation!
	def _has_overlap(self, obj_id, x, y, block_matrix):
		"""
		Check whether an object would have an overlap with another object if it were placed at (x,y).
		@param obj_id 	id of the object to check the given position for
		@param x 	x coordinate to check for the object
		@param y 	y coordinate to check for the object
		@param block_matrix 	0/1 matrix describing the shape of the object
		@return true if there is some overlap with another object
		"""
		this_height = len(block_matrix)
		if this_height == 0:
			print("Error at _has_overlap(): empty block_matrix passed!")
			return False
		this_width = len(block_matrix[0])
		# iterate through the objects:
		for other_id in self.get_object_ids():
			if other_id != obj_id:
				
				other_obj = self.get_obj_by_id(other_id)
				x_offset = x - other_obj.x # horizontal shift between matrices
				y_offset = y - other_obj.y # vertical shift between matrices

				# check whether block matrices overlap, otherwise we can skip all the for-loops
				if x_offset < other_obj.width and x_offset > (-this_width) and \
					y_offset < other_obj.height and y_offset > (-this_height):
					# check whether blocks overlap
					for row in range(this_height):
						other_row = row + y_offset # the row we need to check for blocks in other_obj (is a float!)
						if other_row >= 0 and other_row < other_obj.height:
							for col in range(this_width):
								# check whether this object has a block here
								if not block_matrix[row][col]: 
									continue
								other_col = col + x_offset # the column we need to check for blocks in other_obj (is a float!)
								
								# check whether other object overlaps here and has a block:
								# this requires a lot of conditions since blocks may not be positioned on grid borders
								# if x and y offsets are not whole numbers, we have to check a total of 4 blocks of other_obj
								if ceil(other_col) >= 0 and other_col < other_obj.width:
									if other_obj.block_matrix[floor(other_row)][floor(other_col)]:
										return True
									elif ceil(other_row) < other_obj.height and \
										other_obj.block_matrix[ceil(other_row)][floor(other_col)]:
										return True
									elif ceil(other_col) < other_obj.width and \
										other_obj.block_matrix[floor(other_row)][ceil(other_col)]:
										return True 
									elif ceil(other_row) < other_obj.height and ceil(other_col) < other_obj.width and \
										other_obj.block_matrix[ceil(other_row)][ceil(other_col)]:
										return True
		return False

	# --- Loop functionality ---

	def start_loop(self, action_type, gripper, fn, *args, **kwargs):
		"""Spawn a greenthread.GreenThread instance that executes fn until stop_loop is called.

		@param action_type	str, one of the action types defined by the config
		"""
		assert action_type in self.running_loops, \
			"Error at Model.start_loop: action {} not registered".format(action_type)
		self.running_loops[action_type][gripper] = True
		e = eventlet.spawn(self._loop, action_type, gripper, fn, *args, **kwargs)

	def _loop(self, action_type, gripper, fn, *args, **kwargs):
		while(gripper in self.running_loops[action_type] and
				self.running_loops[action_type][gripper]):
			fn(*args, *kwargs)
			eventlet.sleep(self.config.action_interval)

	def stop_loop(self, action_type, gripper):
		"""Stop a running action for a specific gripper."""
		assert action_type in self.running_loops, \
			"Error at Model.stop_loop: action {} not registered".format(action_type)
		if gripper in self.running_loops[action_type]:
			self.running_loops[action_type][gripper] = False

	def reset_loops(self):
		"""Stop all running actions."""
		self.running_loops = {action: dict() for action in self.config.actions}
