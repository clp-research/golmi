$(document).ready(function () {
	/**
	 * Logger class. Relies on events exchanged between a specific client and server.
	 * Starts logging as soon as the client receives the first state
	 * @param {Socket io connection to the server} modelSocket
	 * @param {set true to save the full state at every change, false to only log the update}
	 */
	this.LogView = class LogView {
		constructor(modelSocket, logFullState=true) {
			this.socket = modelSocket;

			this.data = {"log": new Array()};
			this.logFullState = logFullState;
			this.startTime;
			// if used, only log updates for this gripper
			this.grId;
			// only used if logFullState is true
			this.currentObjs = new Object();
			this.currentGrippers = new Object();
			this.currentConfig = new Object();
			// start listening to events
			this._initEventListeners();
		}

		_initEventListeners() {
			// register socket event listeners
			this._initSocketEvents();
			// register document event listeners
			document.addEventListener("logSegment", e => {
				if (e.detail["segmentTitle"] != undefined && e.detail["segmentTitle"] != null) {
					this.addSegment(e.detail["segmentTitle"].toString(), e.detail["additionalData"]);
				} else {
					console.log("Error: No segment title sent with logSegment event");
				}
			});
			document.addEventListener("emitMessage", e => {
				// append the message as a regular event to the log
				let timeOffset;
				if (!this.startTime) {
					timeOffset = -1;
				} else {
					timeOffset = Date.now() - this.startTime;
				}
				this._addSnapshot(timeOffset, e.detail);
			});
			// TODO
			document.addEventListener("startAction", e => {
				console.log("received startAction event");
			});
			document.addEventListener("stopAction", e => {
				console.log("received stopAction event");
			});
		}

		/**
		 * Start listening to events emitted by the model socket. After this 
		 * initialization, the view logs the client-server communication.
		 */
		_initSocketEvents() {
			this.socket.on("attach_gripper", (assignedId) => {
				this.grId = assignedId;
			});
			this.socket.on("update_state", (state) => {
				// Assumes the logging starts at first 'update_state' event.
				let timeOffset;
				if (!this.startTime) {
					// don't start logging if an empty state was sent
					if (Object.keys(state["objs"]).length == 0 && 
						Object.keys(state["grippers"]).length == 0) {
						return;
					}
					this.startTime = Date.now();
					timeOffset = 0;
				} else {
					timeOffset = Date.now() - this.startTime;
				}
				if (this.logFullState) {
					this.currentObjs = state["objs"];
					this.currentGrippers = state["grippers"];
					this._addSnapshot(timeOffset, this._getFullState());
				}
				else {
					// save snapshot of changes to the state
					this._addSnapshot(timeOffset, this._getStateUpdates(state));
					this.currentObjs = state["objs"];
					this.currentGrippers = state["grippers"];
				}
			})
			this.socket.on("update_grippers", (grippers) => {
				if (this.startTime) {
					let timeOffset = Date.now() - this.startTime;
					if (this.logFullState) {
						this.currentGrippers = grippers;
						this._addSnapshot(timeOffset, this._getFullState());
					} else {
						// TODO: remove this, use gripper updates instead!
						// reduce the log size if a gripper id is given
						if (this.grId) { 
							if (grippers[this.grId]) {
								let update = new Object();
								update[this.grId] = {
									"x": grippers[this.grId]["x"],
									"y": grippers[this.grId]["y"]
								};
								if (grippers[this.grId].gripped) {
									update[this.grId]["gripped"] = 
										Object.keys(grippers[this.grId].gripped)[0];
								}
								// log the id of the gripped object
								this._addSnapshot(timeOffset, {"grippers": update});
							}
						} else {
							this._addSnapshot(timeOffset, {"grippers": this._getGrUpdates(grippers)});
							this.currentGrippers = grippers;
						}
					}
				}
				
			});
			this.socket.on("update_objs", (objs) => {
				if (this.startTime) {
					let timeOffset = Date.now() - this.startTime;
					if (this.logFullState) {
						this.currentObjs = objs;
						this._addSnapshot(timeOffset, this._getFullState());
					}
					else {
						this._addSnapshot(timeOffset, {"objs": this._getObjUpdates(objs)});
						this.currentObjs = objs;
					}
				}
			});
			this.socket.on("update_config", (config) => {
				if (this.startTime) {
					let timeOffset = Date.now() - this.startTime;
					if (this.logFullState) {
						this.currentConfig = config;
						this._addSnapshot(timeOffset, this._getFullState());
					} else {
						this._addSnapshot(timeOffset, {"config": this._getConfigUpdates(config)});
						this.currentConfig = config;
					}
				} else if (this.logFullState) {
					// save the config for later in case it arrived before the first state
					this.currentConfig = config;
				} else {
					// save the config once in the beginning in case it arrived before the first state
					this._addSnapshot(-1, {"config": config});
				}
			});
		}

		// --- add, change, delete data --- // 

		/** 
		 * Make a cut and store the data logged so far (or since the last segment) as a 
		 * segment with key segmentTitle. Optionally add some extra info to the segment.
		 * @param {key to store the logged data with, can not be "log"} segmentTitle
		 * @param {optional data object to store with the new segment, default: null} additionalData
		 */
		addSegment(segmentTitle, additionalData=null) {
			if (segmentTitle == "log") {
				// 'log' key is reserved for the collected event data
				console.log("Error at LogView.createSegment(): 'log' is reserved, use another segment name");
			} else {
				this.data[segmentTitle] = {"log": this.data["log"]};
				if (additionalData) {
					Object.entries(additionalData).forEach(([key, value]) => {
						if (key != "log") {
							this.data[segmentTitle][key] = value;
						} else {
							console.log("Skipping key 'log' of additional data in LogView.addSegment()");
						}
					});
				}
				this.clearLog();
			}
		}

		/**
		 * Add additional data to the current log. Will be saved at 
		 * the top-level of the log object.
		 * @param {string, identifier for the data, 'log' is reserved} key
		 * @param {data to save, can be any json-friendly format, e.g. object, list, string} data
		 */
		addData(key, data) {
			if (key == "log") {
				// 'log' key is reserved for the collected event data
				console.log("Error at LogView.addData(): Cannot manually add data with reserved key 'log'.");
			} else {
				this.data[key] = data;
			}
		}

		/**
		 * Save additional data to an already created segment.
		 * @param {name of an existing segment to save the data to} segment
		 * @param {string, identifier for the data, 'log' is reserved} key
		 * @param {data to save, can be any json-friendly format, e.g. object, list, string} data
		 */
		addDataToSegment(segment, key, data) {
			if (!this.data[segment]) {
				console.log(`Error at LogView.addDataToSegment(): segment ${segment} does not exist.`);
			} else if (key == "log") {
				// 'log' key is reserved for the collected event data
				console.log("Error at LogView.addDataToSegment(): Cannot manually add data with reserved key 'log'.");
			} else {
				this.data[segment][key] = data;
			}
		}

		/**
		 * Delete the current log and reset the saved state except for the configuration.
		 */
		clearLog() {
			this.data["log"] = new Array();
			this.startTime = undefined;
			this.currentObjs = new Object();
			this.currentGrippers = new Object();
		}

		// --- save data --- // 

		/**
		 * Save the data on the server.
		 * @param {route to POST the collected data to, default: /save_log} endpoint
		 * @return true at success
		 */
		sendData(endpoint="/save_log") {
			fetch(new Request(endpoint, {
				method:"POST", 
				headers: { "Content-Type": "application/json;charset=utf-8" },
				body:JSON.stringify(this.data)}))
			.then(response => {
				if (!response.ok) {
					console.log("Error saving log data!");
					return true;
				} else {
					console.log("Saved log data to the server.");
					return false;
				}
			});
		}

		// --- helper functions --- //

		/**
		 * @return a state object containing the objects, grippers and config as received last
		 */
		_getFullState() {
			return {"objs": this.currentObjs,
					"grippers": this.currentGrippers,
					"config": this.currentConfig};
		}

		/**
		 * @return a state object containing only changed objs and grippers
		 */
		_getStateUpdates(newState) {
			return {
				"objs": this._getObjUpdates(newState["objs"]),
				"grippers": this._getGrUpdates(newState["grippers"])};
		}

		/**
		 * Currently has no way of detecting "deleted" objects.
		 * Gripped objects have the "gripped" property set to true, so the
		 * LayerView knows not to draw them on the object layer
		 * @return object mapping obj ids to changed objs
		 */
		_getObjUpdates(newObjs) {
			let updates = new Object();
			for (let [id, obj] of Object.entries(newObjs)) {
				if (this.currentObjs[id]) {
					// check if any property changed
					for (let [prop, value] of Object.entries(obj)) {
						// skip arrays for now. Only occur for block_matrix
						// which does not change without modification to other
						// properties
						if (!(value instanceof Array) &&
							(this.currentObjs[id][prop] != value)) {
							updates[id] = obj;
							break;
						}
					}
				} else {
					// new object
					updates[id] = obj;
				}
			}
			return updates;
		}

		/**
		 * @return object mapping gripper ids to changed grippers
		 */
		_getGrUpdates(newGrs) {
			/*let updates = new Object();
			for (let [id, gr] of Object.entries(newGrs)) {
				if (this.currentGrippers[id]) {
					// check if any property changed
					for (let [prop, value] of Object.entries(obj)) {
						if (prop == "gripped" && value != null) {
							//TODO
						}
						// skip arrays for now. Only occur for block_matrix
						// which does not change without modification to other
						// properties
						if (!(value instanceof Array) &&
							(this.currentObjs[id][prop] != value)) {
							updates[id] = obj;
							break;
						}
					}
				} else {
					// new object
					updates[id] = obj;
				}
			}
			return updates;*/
			return newGrs;
		}

		/**
		 * TODO: not yet implemented
		 * @return object containing changed configurations
		 */
		_getConfigUpdates(newConfig) {
			//console.log("oldConf", this.currentConfig)
			//console.log("newConf", newConfig)
			return newConfig;
		}

		/**
		 * Add a single data update with a timestamp to the log.
		 * @param {timestamp to associate the data with, e.g. time passed since log start} timestamp
		 * @param {update to save} data
		 */
		_addSnapshot(timestamp, data) {
			this.data["log"].push([timestamp, data]);
		}
	}; // class LogView end
}); // on document ready end
