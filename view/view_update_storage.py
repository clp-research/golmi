class ViewUpdateStorage: 
	def __init__(self):
		self.pending_updates = dict()

	def get_updates(self):
		"""
		Getter for the stored updates.
		@return Dictionary of pending updates
		"""
		return self.pending_updates

	def store_update(self, event):
		"""
		Store a posted update into the internal data structures. 
		Overwrite older (now obsolete) updates.
		@param event 	event of update to perform
		"""
		pass

	def clear(self):
		"""
		Delete all stored updates.
		"""
		self.pending_updates = dict()