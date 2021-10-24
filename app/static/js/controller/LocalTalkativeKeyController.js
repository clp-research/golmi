$(document).ready(function () {
	
	/**
	 * Local controller. Emits events for keystrokes that trigger actions.
	 * 
	 * Can connect to one or more models. In each model, a gripper is created
	 * at connection. If a gripperId is passed, an existing gripper with this id is assigned.
	 * Otherwise a new gripper is added with the given id or alternatively the session id. 
	 * The user's keystrokes are used to control the assigned gripper(s) and any gripped object.
	 * @param {optional Array of [socket, gripperId], where gripperId can be null, default:null} modelSockets
	 */
	this.LocalTalkativeKeyController = class LocalTalkativeKeyController extends document.LocalKeyController {
		constructor(modelSockets=null) {
			super(modelSockets);

			this.keyEventNames = {
				13: "grip",  // Enter
				32: "grip",  // Space
				37: "moveLeft",	// arrow left
				38: "moveUp",  // arrow up
				39: "moveRight",  // arrow right
				40: "moveDown",  // arrow down
				65: "rotateLeft",  // a
				68: "rotateRight",  // d
				83: "flip",  // s
				87: "flip"  // w
			};
		}

		/**
		 * Register the key listeners to allow gripper manipulation.
		 * Notifies the associated models and emits events
		 */
		_initKeyListener() {
			$(document).keydown( e => {
				if (this._downAssigned(e.keyCode)) {
					// only progress if the key is not already in state "down"
					if (!this._isDown(e.keyCode)) {
						document.dispatchEvent(new CustomEvent("startAction", { detail: {
							"type": this.keyEventNames[e.keyCode]
						}}));
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
					document.dispatchEvent(new CustomEvent("stopAction", { detail: {
						"type": this.keyEventNames[e.keyCode]
					}}));
					// execute the function assigned to the keyup event
					this.keyAssignment[e.keyCode][1](this);
					// change the state to "up"
					this.keyAssignment[e.keyCode][2] = false;
				}
			});
		}
	}; // class LocalTalkativeKeyController end

}); // on document ready end