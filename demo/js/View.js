$(document).ready(function () {

	/**
	 *
	 */
	this.View = class View {
		constructor(viewAPI, modelAPI, controllerAPI) {
			this.viewAPI = viewAPI;
			// tie the view to some game model
			this.modelAPI = modelAPI; 
			this.controllerAPI = controllerAPI;

			// Configuration. Is assigned at startDrawing()
			this.blockSize;		// block width/height in pixels
			this.cols;			// canvas width in blocks
			this.rows;			// canvas height in blocks
			this.typeConfig;	// map: type -> block matrix

			this.loopId;		// stores timeout ID to manage the update request loop
		}

		// --- drawing functions --- //


		/**
		 * Initially draw to all layers and start checking for updates periodically.
		 */
		async startDrawing() {
			// Stop any ongoing update loop and empty the canvas
			this.stopDrawing();
			this.clear();

			// Delete any updates waiting at the view API, since 
			// we are loading a fresh state from the model next
			let deleteUpdatesReq = new Request(`http://${this.viewAPI}/updates`, {method:"DELETE"});
			await fetch(deleteUpdatesReq)
			.then(r => {
				if (!r.ok) { 
					console.log("Error: Something went wrong deleting pending updates from the view API");
				}
			});
			// Load the config from the model, wait until this step is complete.
			await this._loadConfig();
			// initially draw
			this.draw()

			// start a loop to periodially check for updates
			this.updateLoop(500);
		}

		/**
		 * Interrupt the update loop, freezing the current state.
		 */
		stopDrawing() {
			if (this.loopId) { clearTimeout(this.loopId); }
		}

		/**
		 * Remove any old drawings.
		 */
		clear() {
			console.log("clear() at View: not implemented");
		}

		/**
		 * Draw background, objects, gripper.
		 */
		draw() {
			this.drawBg();
			this.drawObj();
			this.drawGr();
		}

		/**
		 * Redraw everything. 
		 * In contrast to draw(), this function assumes the game has been drawn in the past
		 * and the old drawing needs to be removed first.
		 */
		redraw() {
			this.clear();
			this.draw();
		}

		/**
		 * Draw a background to the game.
		 */ 
		drawBg() {
			console.log("drawBg() at View: not implemented");
		}

		/**
		 * Redraw the background.
		 * In contrast to drawBg(), this function assumes the background has been drawn in the past
		 * and the old drawing needs to be removed first.
		 */ 
		redrawBg() {
			console.log("redrawBg() at View: not implemented");
		}

		/**
		 * Draw the (static) objects.
		 */
		drawObj() {
			console.log(`drawObj(${id}) at View: not implemented`);
		}

		/**
		 * Redraw the (static) objects.
		 * In contrast to drawObj(), this function assumes the objects have been drawn in the past
		 * and the old drawing needs to be removed first.
		 */
		redrawObj() {
			console.log(`redrawObj(${id}) at View: not implemented`);
		}

		/**
		 * Draw the gripper object (and, depending on the implementation, the gripped object too)
		 * The Gripper is used to navigate on the canvas and move objects.
		 */
		drawGr() {
			console.log("drawGr() at View: not implemented");
		}

		/**
		 * Redraw the gripper object (and, depending on the implementation, the gripped object too).
		 * In contrast to drawGripper(), this function assumes the gripper has been drawn in the past
		 * and the old drawing needs to be removed first.
		 */
		redrawGr() {
			console.log("redrawGr() at View: not implemented");
		}
		
		// --- Updating functions ---

		/**
		 * Repeatedly query the view API for updates. 
		 * If updates are found, process them and make another request immediately for smooth
		 * animations. Otherwise, wait $delay ms for next request.
		 * The implementation makes sets the timer AFTER fetching and processing updates to 
		 * avoid requests queueing up.
		 * @param {delay between update requests in ms} delay
		 */
		updateLoop(delay) {
			let thisInstance = this;
			// a recursive setTimeout is used instead of setInterval to assure the execution is completed
			// before the next request is due
			this.loopId = setTimeout(async function() {
		    	let refreshImmediately = true;
				let updates;
				// if there are updates, draw and check for further updates immediately
				while (refreshImmediately) {
		    		// Fetch updates that have been posted the the View API
					updates = await thisInstance._getUpdates();
					refreshImmediately = await thisInstance._processUpdates(updates);
				}
		    	// Once there are no more updates, wait before making the next request
		    	thisInstance.updateLoop(delay);
		  	}, delay);
		}

		/**
		 * Load the configuration from the model. The values are saved since the configuration is
		 * not expected to change frequently. 
		 * Implemented as an async function to make sure the configuration is complete before 
		 * subsequent steps (i.e. drawing) are made.
		 */
		async _loadConfig() {
			// get the configuration from the model
			let configReq = new Request(`http://${this.modelAPI}/config`, {method:"GET"});
			let response = await fetch(configReq);
			if (response.ok) { // Parse the response as json and save the config values
				let json_data = await response.json();
				this.blockSize = (this.canvasWidth / json_data.width);
				this.cols = json_data.width;
				this.rows = json_data.height;
				this.typeConfig = json_data.type_config;
			} else { // Something went wrong - emit an error message
				console.log("Error: Could not fetch configuration from the model API");
			}
		}

		/**
		 * Query the view API for new updates to apply to the interface.
		 * The returned object has the format {"keyword": {details}}
		 * @return object representing the received JSON data or null if no updates are available
		 */
		async _getUpdates() {
			// query the view for new updates to apply
			let updateReq = new Request(`http://${this.viewAPI}/updates`, {method:"GET"});
			let response = await fetch(updateReq);
			if (response.ok) { // Parse the response as json and save the config values
				let json_data = await response.json();
				return json_data;
			} else { // Something went wrong - emit an error message
				console.log("Error: Could not fetch updates from the view API");
				return null
			}
		}

		/**
		 * Process an update object, calling the appropriate redrawing functions.
		 * @param {object containing the keys "grippers", "objs", "config"} update_obj
		 */
		async _processUpdates(updates) {
			// keep track of whether any update was made
			let update_applied = false;
			// if the config has changed, redraw everything
			if (updates["config"]) {
				await this._loadConfig();
				this.redraw();
				update_applied = true;
			} else {
				// there is only 3 layers here and the background does not need to be updated.
				// if any object was changed, redraw the object layer
				if (updates["objs"] && updates["objs"].length > 0) {
					this.redrawObj();
					update_applied = true;
				}
				// if any gripper was changed, redraw the gripper layer
				if (updates["grippers"] && updates["grippers"].length > 0) {
					this.redrawGr();
					update_applied = true;
				}
			}
			return update_applied;
		}

	}; // class View end
}); // on document ready end