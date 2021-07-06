class ViewUpdateStorage: 
	def __init__(self):
		self.pending_updates = {"grippers": dict(), "objs": dict(), "config": None}

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
		@param update_dict	dictionary containing updates to perform: maps categories "grippers", "objs", "config" to dicts
		@return True if storing was successful
		"""
		try: 
			if "grippers" in update_dict:
				for gr_id, gr_dict in update_dict["grippers"].items():
					# old update might be overwritten here
					self.pending_updates["grippers"][gr_id] = gr_dict
			if "objs" in update_dict:
				for obj_id, obj_dict in update_dict["objs"].items():
					self.pending_updates["objs"][obj_id] = obj_dict
			if "config" in update_dict:
				self.pending_updates["config"] = update_dict["config"]
			return True
		except:
			return False
		

	def clear(self):
		"""
		Delete all stored updates.
		"""
		self.pending_updates = {"grippers": dict(), "objs": dict(), "config": False}