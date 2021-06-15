import requests
import json

class KeyController():
	def __init__(self):
		self.models = list() # controlled models
		# dictionary mapping key codes to a tuple (function to call, list of arguments to pass)
		self.key_assignment = {
			13: (self.grip, []),
			32: (self.grip, []),
			37: (self.move, [-1, 0]),
			38: (self.move, [0, -1]),
			39: (self.move, [1, 0]),
			40: (self.move, [0, 1])}

	def attach_model(self, model):
		"""
		Adds a model to the list of controlled models. Avoids duplicate subscription.
		@param model 	str, URL of model to attach. Format: "HOST:PORT" 
		@ṛeturn bool. True if model was successfully added, False if the URL was no string or already registered.
		"""
		if type(model) != str or model in self.models:
			return False
		self.models.append(model)
		return True


	def detach_model(self, model):
		"""
		Removes a model from the list of controlled models.
		@param model 	str, URL of model to detach. Format: "HOST:PORT"
		@return bool. True if model was found and removed, False if model was not in the list.
		"""
		if model in self.models:
			self.models.remove(model)
			return True
		else: 
			return False

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

	# TODO pass gripper id
	def grip(self):
		"""
		Notifies all subscribed models that a "grip" should be attempted.
		Makes a POST-request to the /gripper/grip endpoint.
		"""
		for model in self.models:
			requests.post("http://{}/gripper/grip".format(model))

	# TODO pass gripper id
	def move(self, dx, dy):
		"""
		Notifies all subscribed models to attempt moving the gripper.
		@param dx 	int or float, number of units to move in x direction. Negative values translate to leftwards movement.
		@param dy 	int or float, number of units to move in y direction. Negative values translate to upwards movement.
		"""
		for model in self.models:
			requests.post("http://{}/gripper/position".format(model), json=json.dumps({"x": dx, "y": dy}))

	def _is_assigned(self, key_code):
		"""
		Check whether a function is assigned to a given key code.
		@param key_code 	int, code of the key in question
		@return bool, True signifying a function is assigned to the given key code
		"""
		return key_code in self.key_assignment