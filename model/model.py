from state import State
import requests
from math import floor

class Model:
	def __init__(self, config):
		self.views = list()
		self.state = State()
		self.config = config

	# --- getter --- #

	def get_objects(self):
		return self.state.get_objects()

	def get_object_ids(self):
		return self.state.get_object_ids()

	def get_obj_by_id(self, id):
		return self.state.get_obj_by_id(id)

	def get_gripper_ids(self):
		return self.state.get_gripper_ids()

	def get_gripper_by_id(self, id):
		return self.state.get_gripper_by_id(id)

	def get_gripped_obj(self, id):
		return self.state.get_gripped_obj(id)

	def get_gripper_coords(self, id):
		"""
		@return list: [x-coordinate, y-coordinate]
		"""
		return self.state.get_gripper_coords(id)


	def get_width(self):
		return self.config.width

	def get_height(self):
		return self.config.height

	def get_type_config(self):
		return self.config.type_config

	#  --- Events --- #
	# todo
	def get_gripper_updated_event(self): 
		return "gripper updated"

	def get_new_state_loaded_event(self): 
		return "new state loaded"
	
	def get_obj_updated_event(self, id): 
		return "object updated: {}".format(id)

		# --- Configuration functions --- #

	def attach_view(self, view):
		"""
		Link a new view. Each view is notified of model changes via events.
		@param view 	URL of view API
		"""
		self.views.append(view)

	def detach_view(self, view):
		"""
		Removes a view from the list of listeners.
		@param view 	registered URL of view to remove
		"""
		# use while loop to deal with possible duplicate registration
		while view in self.views:
			self.views.remove(view)

	def clear_views(self):
		"""
		Removes all view listeners.
		"""
		self.views.clear()

	def set_initial_state(self, state):
		"""
		Initialize the model's (game) state.
		@param state	State object or dict or JSON file
		"""
		if type(state) == str or type(state) == dict:
			self.state.from_JSON(state)
		else:
			self.state = state
		self._notify_views(self.get_new_state_loaded_event())

	def reset(self):
		"""
		Reset the current state.
		"""
		self.state = State()
		self._notify_views(self.get_new_state_loaded_event())

	def _notify_views(self, event):
		"""
		Notify all listening views of model events (usually data updates)
		@param event 	Event message. Sent to each of the model's views
		"""
		for view in self.views:
			requests.post("http://{}/updates".format(view), data=event)

	# --- Gripper manipulation --- #

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
			self._notify_views(self.get_obj_updated_event(old_gripped))
		else: 
			# Check if gripper hovers over some object
			new_gripped = self._get_grippable()
			# changes to object and gripper
			if new_gripped: self.state.grip(id, newGripped)
		# notify view of gripper change. A newly gripped object is implicitly updated.
		self._notify_views(self.get_gripper_updated_event())

	def move_gr(self, id, x_steps, y_steps, step_size=None):
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
		if self.get_gripped_obj(id):
			gr_obj = self.get_obj_by_id(self.get_gripped_obj(id))
			# if an object is gripped, both the gripper and the object have to stay inside the board
			if self._is_in_limits(gripper_x + dx, gripper_y + dy) and \
			   self._is_in_limits(gr_obj.get_center_x() + dx, gr_obj.get_center_y() + dy):

				self.state.move_gr(id, dx, dy)
				self.state.move_obj(self.get_gripped_obj(id), dx, dy)
				# notify the views. A gripped object is implicitly redrawn. 
				self._notify_views(self.get_gripper_updated_event())

		# if no object is gripped, only move the gripper
		elif self._is_in_limits(gripper_x + dx, gripper_y + dy):
			self.state.move_gr(id, dx, dy)
			# notify the views. A gripped object is implicitly redrawn. 
			self._notify_views(self.get_gripper_updated_event())
		
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
			# (gridX, gridY) is the position on the type grid the gripper would be on.
			# if the gripper is outside the grid (i.e. coordinate is < 0 or >= size), the if-condition
			# below evaluates to false. Thus, whether the gripper is on the grid and whether a block is
			# present at the grid position is checked at once.
			grid_x = floor(x-obj.x)
			grid_y = floor(y-obj.y)
			if self.get_type_config()[obj.type][grid_y] and self.get_type_config()[obj.type][grid_y][grid_x]: 
				return obj_id
		return None
		
	def _is_in_limits(self, x, y):
		"""
		Check whether given coordinates are within the space limits.
		@param x 	x coordinate to check
		@param y 	y coordinate to check
		"""
		return self._x_in_limits(x) and self._y_in_limits(y)
		
	def _x_in_limits(self, x):
		"""
		Check whether given x coordinate is within the space limits.
		@param x 	x coordinate to check
		"""
		return (x >= 0 and x<= self.get_width())
		
	def _y_in_limits(self, y):
		"""
		Check whether given y coordinate is within the space limits.
		@param y 	y coordinate to check
		"""
		return (y >= 0 and y <= self.get_height())

if __name__ == "__main__":
	# Unit tests
	from config import Config
	test_config = Config("../pentomino/pentomino_types.json")
	test_model = Model(test_config)
	assert len(test_model.get_objects())

	test_model.add_view("address:port")
	assert test_model.views == ["address:port"]
