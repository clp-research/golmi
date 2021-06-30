$(document).ready(function () {
	
	/**
	 * @param {Array of [modelURL, gripperId], optional} modelAPIs
	 */
	this.GripperKeyController = class GripperKeyController {
		constructor(modelAPIs=null) {
			// array of model URLs to notify
			this.models = modelAPIs ? modelAPIs : new Array();
			
			// assign functions to key codes: [function for keydown, function for keyup, down?] 
			this.keyAssignment = {
				13: [this.grip, null, false],				// Enter
				32: [this.grip, this.stopGrip, false],				// Space
				37: [this.moveLeft, this.stopMove, false],			// arrow left
				38: [this.moveUp, this.stopMove, false],			// arrow up
				39: [this.moveRight, this.stopMove, false],			// arrow right
				40: [this.moveDown, this.stopMove, false],			// arrow down
				65: [this.rotateLeft, this.stopRotate, false],		// a
				68: [this.rotateRight, this.stopRotate, false],		// d
				83: [this.flipHorizontally, this.stopFlip, false],	// s
				87: [this.flipVertically, this.stopFlip, false]		// w
			};

			// Stores codes of pressed keys waiting for key release
			this.activeKeys = new Set();

			// Set up key listeners
			this._initKeyListener();
		}

		// --- (Un)Subscribing models ---

		/**
		 * Subscribe a new model. Duplicate subscription is prevented.
		 * @param {url of the model API to notify} url
		 * @param {id of the gripper to control} gripperId
		 */
		attachModel(url, gripperId) {
			// Make sure not to subscribe a model twice
			if (!this.models.includes([url, gripperId])) {
				this.models.push([url, gripperId]);
			}
		}

		/**
		 * Remove a model from the internal list of models to notify.
		 * @param {url of the model API to unsubscribe} url
		 * @param {id of the gripper to unsubscribe, optional. If null, all grippers of the model url will be unsubscribed} gripperId
		 * 
		 */
		detachModel(url, gripperId=null) {
			if (gripperId) {
				// Only remove the pair [url, gripperId]
				this.models = this.models.filter(model => model != [url, gripperId]);
			} else {
				// Remove any occurence of the URL (even though duplicates should not exist using attachModel())
				this.models = this.models.filter(model => model[0] != url);
			}
		}

		// --- Notifying subscribed models ---

		/**
		 * Notifies all subscribed models that a "grip" should be attempted.
		 * Makes a POST request to the /gripper/grip endpoint.
		 * @param {reference to GripperKeyController instance (this)} thisArg
		 */
		grip(thisArg) {
			// send a request to each subscribed model
			for (let modelGripper of thisArg.models) {
				let gripReq = new Request(`http://${modelGripper[0]}/gripper/grip`, {method:"POST", body:`{"id": ${modelGripper[1]}}`});
				thisArg._sendRequest(gripReq, `Error starting to grip: gripper #${modelGripper[1]} at ${modelGripper[0]}`);
			}
		}

		stopGrip(thisArg) {
			// send a request to each subscribed model
			for (let modelGripper of thisArg.models) {
				let stopReq = new Request(`http://${modelGripper[0]}/gripper/grip`, {method:"DELETE", body:`{"id": ${modelGripper[1]}}`});
				thisArg._sendRequest(stopReq, `Error stopping to grip: gripper #${modelGripper[1]} at ${modelGripper[0]}`);
			}
		}

		/**
		 * Notify models to move the gripper 1 block to the left.
		 * @param {reference to GripperKeyController instance (this)} thisArg
		 */
		moveLeft(thisArg) { thisArg._moveGr(-1, 0); }

		/**
		 * Notify models to move the gripper 1 block up.
		 * @param {reference to GripperKeyController instance (this)} thisArg
		 */
		moveUp(thisArg) {
			thisArg._moveGr(0, -1); 
		}
		
		/**
		 * Notify models to move the gripper 1 block to the right.
		 * @param {reference to GripperKeyController instance (this)} thisArg
		 */
		moveRight(thisArg) { thisArg._moveGr(1, 0); }

		/**
		 * Notify models to move the gripper 1 block down.
		 * @param {reference to GripperKeyController instance (this)} thisArg
		 */
		moveDown(thisArg) { thisArg._moveGr(0, 1); }

		/**
		 * Helper function to notify models to move the gripper 1 block in a specified direction.
		 * @param {number of blocks to move in x direction} dx
		 * @param {number of blocks to move in y direction} dy
 		 */
		_moveGr(dx, dy) {
			for (let modelGripper of this.models) {
				let moveReq = new Request(`http://${modelGripper[0]}/gripper/position`, {method:"POST", body:`{"id": ${modelGripper[1]}, "dx": ${dx}, "dy": ${dy}, "speed": 1}`});
				this._sendRequest(moveReq, `Error moving gripper #${modelGripper[1]} at ${modelGripper[0]}`);
			}
		}

		stopMove(thisArg) {
			for (let modelGripper of thisArg.models) {
				let moveReq = new Request(`http://${modelGripper[0]}/gripper/position`, {method:"DELETE", body:`{"id": ${modelGripper[1]}}`});
				thisArg._sendRequest(moveReq, `Error stopping gripper #${modelGripper[1]} at ${modelGripper[0]}`);
			}
		}

		/**
		 * 
		 * @param {reference to GripperKeyController instance (this)} thisArg
		 */
		rotateLeft(thisArg) { thisArg._rotate(-1); }

		/**
		 * 
		 * @param {reference to GripperKeyController instance (this)} thisArg
		 */
		rotateRight(thisArg) { thisArg._rotate(1); }

		/**
		 * Helper function to notify models to rotate a gripped object in a specified direction.
		 * @param {number of units to turn. Pass negative value for leftwards rotation} direction
		 */
		_rotate(direction) {
			for (let modelGripper of this.models) {
				console.log("rotate", direction, modelGripper[0], modelGripper[1])
			}
		}

		stopRotate(thisArg) {
			console.log("stopRotate");
		}

		/**
		 * 
		 * @param {reference to GripperKeyController instance (this)} thisArg
		 */
		flipHorizontally(thisArg) { thisArg._flip(0); }

		/**
		 * 
		 * @param {reference to GripperKeyController instance (this)} thisArg
		 */
		flipVertically(thisArg) { thisArg._flip(1); }

		/**
		 * Helper function to notify models to flip a gripped object on a specified axis.
		 * @param {Axis of reflection. 0: horizontal, 1: vertical} axis
		 */
		_flip(axis) {
			for (let modelGripper of this.models) {
				console.log("flip", axis, modelGripper[0], modelGripper[1])
			}
		}

		stopFlip(thisArg) {
			console.log("stopFlip")
		}

		/**
		 * Helper function for sending and processing a single request
		 * @param {Request object, containing method and optional body} request
		 * @param {error message to log to the console if something goes wrong} errMsg
		 */
		_sendRequest(request, errMsg) {
			// send a request to each subscribed model, log to console if something goes wrong:
			fetch(request)
			.then(r => {
				// log to console if something goes wrong:
				if (!r.ok) {
					let info = r.status == 404 ? ": gripper with this id does not exist" : "";
					console.log(`${errMsg}${info}`);
				}
			});
		}

		// --- Reacting to user events ---

		/**
		 * Start fresh, delete any keys remembered as currently pressed.
		 */
		resetKeys(){
			for (let key of Object.keys(this.keyAssignment)) {
				// set property pressed to false for each key
				this.keyAssignment[key][2] = false;
			}
		}

		/**
		 * Register the key listeners to allow gripper manipulation.
		 * Notifies the associated models.
		 */
		_initKeyListener() {
			$(document).keydown( e => {
				if (this._downAssigned(e.keyCode)) {
					// only progress if the key is not already in state "down"
					if (!this._isDown(e.keyCode)) {
						// if a keyup-function is assigned, change the state to "down"
						if (this._upAssigned(e.keyCode)) {
							this.keyAssignment[e.keyCode][2] = true;
						}
						// execute the function assigned to the keydown event
						this.keyAssignment[e.keyCode][0](this);
					}
				}
			});

			$(document).keyup( e => {
				// check if a function is assigned. Only execute if the key was remembered as "down"
				if (this._upAssigned(e.keyCode) && this._isDown(e.keyCode)) {
					// execute the function assigned to the keyup event
					this.keyAssignment[e.keyCode][1](this);
					// change the state to "up"
					this.keyAssignment[e.keyCode][2] = false;
				}
			});
		}

		/** 
		 * Check whether a function is assigned to the keydown event of a given key code.
		 * @param {int, code of the key in question} keyCode
		 * @return bool, true signifying a function is assigned to keydown
		 */
		_downAssigned(keyCode) {
			return this.keyAssignment[keyCode] && this.keyAssignment[keyCode][0];
		}

		/** 
		 * Check whether a function is assigned to the keyup event of a given key code.
		 * @param {int, code of the key in question} keyCode
		 * @return bool, true signifying a function is assigned to keyup
		 */
		_upAssigned(keyCode) {
			return this.keyAssignment[keyCode] && this.keyAssignment[keyCode][1];
		}

		/**
		 * Check whether a key is currently in "down" state aka currently pressed.
		 * @return bool, true if the key is "down"
		 */
		_isDown(keyCode) {
			return this.keyAssignment[keyCode][2];
		}

	}; // class LayerView end

}); // on document ready end