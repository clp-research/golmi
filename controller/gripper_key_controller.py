import requests
import json

class GripperKeyController():
	def __init__(self):
		self.models = list() # contains tuples (controlled model, associated gripper)
		# dictionary mapping key codes to a tuple (function to call, list of arguments to pass)
		self.key_assignment = {
			13: (self.grip, []),
			32: (self.grip, []),
			37: (self.move, [-1, 0]),
			38: (self.move, [0, -1]),
			39: (self.move, [1, 0]),
			40: (self.move, [0, 1])}

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
		if self._is_assigned(key_code):
			# get function and arguments to call
			fn, args = self.key_assignment[key_code] 
			fn(*args)
			return True
		else:
			return False

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
			requests.post("http://{}/gripper".format(model), data=json.dumps({"id": gripper, "x": dx, "y": dy}))

	def _is_assigned(self, key_code):
		"""
		Check whether a function is assigned to a given key code.
		@param key_code 	int, code of the key in question
		@return bool, True signifying a function is assigned to the given key code
		"""
		return key_code in self.key_assignment