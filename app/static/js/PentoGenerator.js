$(document).ready(function () {

	/**
	 *
	 */
	this.PentoGenerator = class PentoGenerator {
		constructor(socket) {
			this.socket = socket;
		}

		/**
		 * Generate a random state and initialize the model.
		 * @param {number of objects to generate} nObjs
		 * @param {number of grippers to generate} nGrippers
		 * @param {configuration received from model} config
		 * @param {true to determine the gripper start position randomly, false to start in the center. default: false} randomGrPos
		 * @return the generated state, null if something went wrong
		 */
		async initRandomState(nObjs, nGrippers, config, randomGrPos=false) {
			let rState = await this.generateState(nObjs, nGrippers, config, randomGrPos);
			// something went wrong during state generation
			if (!rState) { return null; }
			this.socket.emit("load_state", rState);
		}

		/**
		 * Generate a random state following the model's configuration.
		 * @param {number of objects to generate} nObjs
		 * @param {number of grippers to generate} nGrippers
		 * @param {true to determine the gripper start position randomly, false to start in the center. default: false} randomGrPos
		 * @param {configuration received from model} config
		 * @return State object that can be sent to a model, object ids are numbers. null if something went wrong.
		 */
		async generateState(nObjs, nGrippers, config, randomGrPos=false) {
			let state = new Object();

			// grippers (they don't grip any object)
			state.grippers = new Object();
			let takenPositions = [];
			for (let i=0; i<nGrippers; i++) {
				// don't generate grippers at the same position
				if (randomGrPos) {
					let x,y;
					do {
						// shift all positions bei 0.5 blocks to center grippers in a block (purely aesthetic reasons)
						x = this._randomInt(0, config.width)+0.5;
						y = this._randomInt(0, config.height)+0.5;
					}
					while (takenPositions.includes([x,y]));
					takenPositions.push([x,y]);
					state.grippers[i] = {"x": x, "y": y};
				} else {
					state.grippers[i] = {"x": (config.width/2)-0.5, "y": (config.height/2)-0.5};
				}
			}

			// objects
			state.objs = new Object();
			// don't generate pieces at the same position (overlap is possible as for right now)
			takenPositions = [];
			for (let i=0; i<nObjs; i++) {
				// choose a random type
				let types = Object.keys(config.type_config); // get available types
				let type = types[this._randomInt(0, types.length)];
				// determine size // TODO size generation?
				let height = config.type_config[type].length;
				let width = config.type_config[type][0].length;
				// generate position. Rudimentary overlap check. TODO: don't allow overlapping according to gameState
				let x,y;
				do {
					x = this._randomInt(0, config.width-width);
					y = this._randomInt(0, config.height-height);
				}
				while (takenPositions.includes([x,y]));
				takenPositions.push([x,y]);

				// generate color
				let color = config.colors[this._randomInt(0, config.colors.length)];
				// generate rotation and mirrored, if corresponding actions are allowed
				let rotation, mirrored;
				if (config.actions.includes("rotate")) {
					rotation = config.rotation_step * this._randomInt(0, Math.floor(360/config.rotation_step))
				} else {
					rotation = 0;
				}
				if (config.actions.includes("flip")) {
					mirrored = Boolean(this._randomInt(0,2));
				} else {
					mirrored = false;
				}
				state.objs[i] = {"type": type, "x": x, "y": y, "width": width, "height": height, "color": color, "mirrored": mirrored, "rotation": rotation};
			}
			return state;
		}

		/**
		 * Helper function to generate a random integer i: min <= i < max
		 * @param {int, lower limit (inclusive) for result} min
		 * @param {int, upper limit (exclusive) for result} max
		 * @return (pseudo) random integer within limits (including the lower limit)
		 */
		_randomInt(min, max) {
			return min + Math.floor(Math.random() * (max-min));
		}

		sleep(ms) {
      		return new Promise(resolve => setTimeout(resolve, ms));
   		}

	}; // class PentoGenerator end

	// Unit test function
	/**
	 * Performs some tests on the PentoGenerator class and outputs the results to the console.
	 * @return true if all tests have been passed, false if an error occurred
	 */
	document.pentoGeneratorTest = async function () {
		console.log("Performing tests for PentoGenerator...");
		let diagnose = "";
		let testGenerator = new document.PentoGenerator(document.MODEL_API);
		if (!testGenerator) {
			console.log("Error: PentoGenerator could not be constructed");
			return false;
		}
		// generate a state and check the format
		let nObjs = 2, nGrippers = 2;
		let testState = await testGenerator.generateState(nObjs, nGrippers, true);
		if (!testState) {
			diagnose += "Error: No state could be generated\n";
		} else if (!testState.objs || !testState.grippers) {
			diagnose += "Error: expected keys 'objs' and 'grippers' not found\n";
		} else if (Object.keys(testState.objs).length != nObjs) {
			diagnose += `Error: Attempted to generate ${nObjs} objects, got ${Object.keys(testState.objs).length}`;
		} else if (Object.keys(testState.grippers).length != nGrippers) {
			diagnose += `Error: Attempted to generate ${nGrippers} grippers, got ${Object.keys(testState.grippers).length}`;
		}
		// output the result
		console.log(diagnose.length > 0 ? diagnose : "PentoGenerator tests passed.");
		return diagnose.length == 0;
	}
}); // on document ready end