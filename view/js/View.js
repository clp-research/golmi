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
		}

		// --- drawing functions --- //

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
			for (let id of this.model.objectIds) {
				this.drawObj(id);
			}
			this.drawGripper();
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
		 * Draw a single object.
		 * @param {identifier of the object to be drawn, matches an id in the model's gameState} id
		 */
		drawObj(id) {
			console.log(`drawObj(${id}) at View: not implemented`);
		}

		/**
		 * Redraw a single object.
		 * In contrast to drawObj(), this function assumes the object has been drawn in the past
		 * and the old drawing needs to be removed first.
		 * @param {identifier of the object to be drawn, matches an id in the model's gameState} id
		 */
		redrawObj(id) {
			console.log(`redrawObj(${id}) at View: not implemented`);
		}

		/**
		 * Draw the gripper object (used to navigate on the canvas and move objects)
		 */
		drawGripper() {
			console.log("drawGripper() at View: not implemented");
		}

		/**
		 * Redraw the gripper object. 
		 * In contrast to drawGripper(), this function assumes the gripper has been drawn in the past
		 * and the old drawing needs to be removed first.
		 */
		redrawGripper() {
			console.log("redrawGripper() at View: not implemented");
		}
	}; // class View end
}); // on document ready end