import requests
import json

class GripperKeyController():
	def __init__(self):
		self.models = list() # contains tuples (controlled model, associated gripper)
		# assign functions to key codes: [function for keydown, args for keydown, function for keyup, args for keyup, down?] 
		self.key_assignment = {
			13: [self.grip, [], None, [], False],					# Enter
			32: [self.grip, [], None, [], False],					# Space
			37: [self.move, [-1, 0], self.stop_move, [], False],	# arrow left
			38: [self.move, [0, -1], self.stop_move, [], False],	# arrow up
			39: [self.move, [1, 0], self.stop_move, [], False],		# arrow right
			40: [self.move, [0, 1], self.stop_move, [], False],		# arrow down
			65: [self.rotate, [-1], self.stop_rotate, [], False],	# a
			68: [self.rotate, [1], self.stop_rotate, [], False],	# d
			83: [self.flip, [], None, [], False],					# s
			87: [self.flip, [], None, [], False]					# w
		}

	def attach_model(self, model, gripper):
		"""
		Adds a model to the list of controlled models. Avoids duplicate subscription.
		@param model 	str, URL of model to attach. Format: "HOST:PORT" 
		@param gripper	id of the gripper to control
		@ṛeturn bool. True if model was successfully added, False if the URL was no string.
		"""

		### Strict version: check whether model is available and has the corresponding gripper.
		### Took this out because is makes the set up more complicated
		# if type(model) != str or (model, gripper) in self.models:
		# 	return False
		# # check if the model has a gripper with the corresponding index
		# try:
		# 	gr_response = requests.get("http://{}/gripper".format(model))
		# 	if gripper not in gr_response.json():
		# 		return False
		# except:
		# 	return False 
		if type(model) != str:
			return False
		if (model, gripper) not in self.models:
			self.models.append((model, gripper))
		return True


	def detach_model(self, model, gripper=None):
		"""
		Removes a model from the list of controlled models.
		@param model 	str, URL of model to detach. Format: "HOST:PORT"
		@return bool. True if model was found and removed, False if model was not in the list.
		"""
		if gripper:
			# remember whether the pair was found - if not, return False 
			found = (model, gripper) in self.models
			if found:
				self.models.remove((model, gripper))
		else:
			found = False
			for i in range(len(self.models)):
				if self.models[i][0] == model:
					self.models.pop(i)
					found = True
		return found

	def key_pressed(self, key_code):
		"""
		Dispatches any function assigned to the given key code.
		@param key_code 	int, code of key that was pressed
		""" 
		if self._is_assigned_down(key_code):
			if not self._is_down(key_code):
				# get function and arguments to call
				fn, args, _, _, _ = self.key_assignment[key_code] 
				fn(*args)
				# set key status to down, if relevant
				self._set_down(key_code)
			return True
		else:
			return False

	def key_released(self, key_code):
		"""
		Dispatches any function assigned to releasing the given key.
		This serves for continuous actions such as moving and rotating
		@param key_code 	int, code of key that was released
		"""
		# following the internal logic, key can only be down if an up function is assigned, so
		# we can skip this check here
		if self._is_down(key_code):
			# get function and arguments to call
			_, _, fn, args, _ = self.key_assignment[key_code] 
			fn(*args)
			# set key status to up
			self._set_up(key_code)
			return True

	def grip(self):
		"""
		Notifies all subscribed models that a "grip" should be attempted.
		Makes a POST-request to the /gripper/grip endpoint.
		"""
		for (model, gripper) in self.models:
			requests.post("http://{}/gripper/grip".format(model), data=json.dumps({"id": gripper}))

	def move(self, dx, dy):
		"""
		Notifies all subscribed models to attempt moving the gripper.
		@param dx 	int or float, number of units to move in x direction. Negative values translate to leftwards movement.
		@param dy 	int or float, number of units to move in y direction. Negative values translate to upwards movement.
		"""
		for (model, gripper) in self.models:
			requests.post("http://{}/gripper/position".format(model), data=json.dumps({"id": gripper, "dx": dx, "dy": dy}))

	def stop_move(self):
		for (model, gripper) in self.models:
			requests.delete("http://{}/gripper/position".format(model), data=json.dumps({"id": gripper}))

	def rotate(self, direction):
		print("not implemented")

	def stop_rotate(self):
		print("not implemented")

	def flip(self):
		print("not implemented")

	def _is_assigned_down(self, key_code):
		"""
		Check whether a function is assigned to pressing a given key.
		@param key_code 	int, code of the key in question
		@return bool, True signifying a function is assigned to a key down event of the given key code
		"""
		return key_code in self.key_assignment and self.key_assignment[key_code][0] != None

	def _is_assigned_up(self, key_code):
		"""
		Check whether a function is assigned to releasing a given key.
		@param key_code 	int, code of the key in question
		@return bool, True signifying a function is assigned to a key up event of the given key code
		"""
		return key_code in self.key_assignment and self.key_assignment[key_code][2] != None

	def _is_down(self, key_code):
		"""
		Check whether a key is currently in "down" status, i.e. pressed.
		"""
		return key_code in self.key_assignment and self.key_assignment[key_code][4]

	def _set_down(self, key_code):
		"""
		Change the status of a key to "down".
		"""
		if self._is_assigned_up(key_code):
			self.key_assignment[key_code][4] = True

	def _set_up(self, key_code):
		"""
		Change the status of a key to "up".
		"""
		if key_code in self.key_assignment:
			self.key_assignment[key_code][4] = False