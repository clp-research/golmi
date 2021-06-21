class ViewUpdateStorage: 
	def __init__(self):
		self.pending_updates = {"grippers": list(), "objs": list(), "config":False}

	def get_updates(self):
		"""
		Getter for the stored updates.
		@return Dictionary of pending updates
		"""
		return self.pending_updates

	def store_update(self, update_dict):
		"""
		Store a posted update into the internal data structures. 
		Unknown keys are silently ignored.
		@param update_dict	dictionary containing updates to perform: maps categories "grippers", "objs" to lists containing ids 
		@return True if storing was successful
		"""
		if "grippers" in update_dict:
			for gripper in update_dict["grippers"]:
				if gripper not in self.pending_updates["grippers"]:
					self.pending_updates["grippers"].append(gripper)
		if "objs" in update_dict:
			for obj in update_dict["objs"]:
				if obj not in self.pending_updates["objs"]:
					self.pending_updates["objs"].append(obj)
		if "config" in update_dict:
			# changed configuration is indicated by the presence of the config key
			self.pending_updates["config"] = True
		return True
		

	def clear(self):
		"""
		Delete all stored updates.
		"""
		self.pending_updates = {"grippers": list(), "objs": list(), "config": False}