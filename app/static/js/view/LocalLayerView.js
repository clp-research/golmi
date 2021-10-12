$(document).ready(function () {

	/**
	 * Same functionality as the parent LayerView, but listens to document events
	 * for updates. Does NOT listen to socket events.
	 */
	this.LocalLayerView = class LocalLayerView extends document.LayerView {
		constructor(bgCanvas, objCanvas, grCanvas, options) {
			// pass null in place of socket
			super(null, bgCanvas, objCanvas, grCanvas, options);
			this._initDocumentEvents();
			this.drawBg();
		}

		/**
		 * Override parent method so the view does not react to socket events.
		 */
		_initSocketEvents() {}

		/**
		 * Start listening to events locally dispatched to the target 'document'.
		 */
		_initDocumentEvents() {
			// new state -> redraw object and gripper layer
			document.addEventListener("update_state", (e) => {
				if (e.detail["grippers"] && e.detail["objs"]) {
					this.grippers = e.detail["grippers"];
					this.objs = e.detail["objs"];
					this.redrawGr();
					this.redrawObjs();
				} else {
					console.log("Error: Received state does not have the right format." + 
						" Expected keys 'grippers' and 'objs'.");
				}
			});
			// new gripper state -> redraw grippers
			document.addEventListener("update_grippers", (e) => {
				this.grippers = e.detail["grippers"];
				this.redrawGr();
			});
			// new object state -> redraw objects
			document.addEventListener("update_objs", (e) => {
				this.objs = e.detail["objs"];
				this.redrawObjs();
			});
			// new configuration -> save values and redraw everything
			document.addEventListener("update_config", (e) => {
				this._loadConfig(e.detail["config"]);
				this.redraw();
			});
		}

	}; // class LocalLayerView end
}); // on document ready end
