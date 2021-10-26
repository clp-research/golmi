$(document).ready(function () {

	/**
	 * Reads the log and feeds updates back into views (or other components)
	 * using document-wide events.
	 * @param {frames per second for replay rendering, default: 20} frameRate
	 */
	this.Replayer = class Replayer {
		constructor(frameRate=20, speed=1) {
			this._log;
			if (frameRate > 100) {
				console.log("Warning:",
					" High frame rates may cause the replay to slow down.");
			}
			this.frameRate = frameRate;  // fps
			this.speed = speed;
			this.currentTime = -1;
			this._endTime;
			this.replayLoop;
			// state
			this.grippers;
			this.objs;
			this.config;
			this._resetState();
		}

		// --- Getters and setters --- //

		set log(logData) {
			// stop current replay, reset properties
			this.stop();
			this._resetState();
			this._log = logData;
			this.startTime = 0;
		}

		get log() {
			return this._log;
		}

		set startTime(timeOffset) {
			// update internal state (at most up to endTime)
			// do not emit events for every single log entry, instead
			// emit "update_config" and "update_state once"
			this._fastForward(this, timeOffset, false);
			this._emitConfigUpdate();
			this._emitStateUpdate();
		}

		set endTime(timeOffset) {
			this._endTime = timeOffset;
		}

		/**
		 * @return set endTime, final timestamp of the log or null if both
		 * 		are missing
		 */
		get endTime() {
			if (this._endTime != undefined) {
				if (this.log) {
					return Math.min(this._endTime, this.log[this.log.length-1][0]);
				}
				return this._endTime;
			} else if (this.log) {
				return this.log[this.log.length-1][0];
			}
			return null;
		}

		/**
		 * Start playing from the current point of time in the log.
		 * @param {optional: set a time to start playing from} st
		 */ 
		start(fromTime=null) {
			// stop any ongoing loop
			this._stopReadingLog();
			if (fromTime != null) {
				if (typeof(fromTime) != "number") {
					console.log("Error at start(): fromTime must be numeric.",
						` Got ${fromTime}`);
				} else {
					this.startTime = fromTime;
				}
			}
			this._startReadingLog();
		}

		/**
		 * Stop playing.
		 */
		stop() {
			this._stopReadingLog();
		}

		// --- Loop management --- //

		/**
		 * Start a loop that continuously increases the current time 
		 * and emits update events when a timestamp in the log is reached.
		 */
		_startReadingLog() {
			let frameOffset = Math.round(1000 / this.frameRate);
			// Process at a certain frame rate until the log ends
			this.replayLoop = setInterval(() => {
				if (this.currentTime < this.endTime) {
					// load updates from currentTime to currentTime + offset
					this._fastForward(this, this.currentTime + frameOffset*parseFloat(this.speed), true);
				} else {
					this._stopReadingLog();
				}
			}, frameOffset);
		}

		/**
		 * Stop the update loop.
		 */
		_stopReadingLog() {
			clearInterval(this.replayLoop);
		}

		// --- Updating the state --- //

		/**
		 * Delete the current state.
		 */
		_resetState() {
			this.grippers = new Object();
			this.objs = new Object();
			this.config = new Object();
		}

		/**
		 * Update the internal state up to toTime, but at most up to the last
		 * log entry. Set notify to false to not emit update events.
		 */
		_fastForward(thisArg, toTime, notify=true) {
			// restart if toTime was already passed in the log
			if (toTime < thisArg.currentTime) {
				thisArg.currentTime = -1;
				thisArg._resetState();
			}
			// successively process log entries
			for (let [updateTime, update] of thisArg.log) {
				if (updateTime > toTime) {
					break;
				}
				 // skip already processed updates
				if (updateTime >= thisArg.currentTime) {
				 	thisArg._makeUpdate(update, notify);
				 	thisArg.currentTime = updateTime;
				}
			}
			thisArg.currentTime = Math.min(toTime, thisArg.endTime);
		}

		// TODO: This assumes objects can be modified and added, but not 
		// deleted! If we want to delete objects, we need to make sure 
		// all sent updates are complete ... -> not so sparse logs
		/**
		 * Incorporate an update into the internal state. 
		 * Set notify to false to not emit update events.
		 */
		_makeUpdate(update, notify=true) {
			if (update["config"]) {
				Object.assign(this.config, update["config"]);
				if (notify) {
					this._emitConfigUpdate();
				}
			}
			if (update["objs"]) {
				Object.assign(this.objs, update["objs"]);
				if (notify) {
					this._emitObjsUpdate();
				}
			}
			if (update["grippers"]) {
				Object.assign(this.grippers, update["grippers"]);
				if (notify) {
					this._emitGrippersUpdate();
				}

			}
		}

		/**
		 * Emit an update to the document notifying of a state update, 
		 * sending the current internal objects and grippers
		 */
		_emitStateUpdate() {
			document.dispatchEvent(new CustomEvent("update_state", {
				detail: {
					"objs": this.objs,
					"grippers": this.grippers
				}
			}));
		}

		/**
		 * Emit an update to the document notifying of a config update, 
		 * sending the current internal configuration.
		 */
		_emitConfigUpdate() {
			document.dispatchEvent(new CustomEvent("update_config", {
				detail: { "config": this.config }
			}));
		}

		/**
		 * Emit an update to the document notifying of an objects update, 
		 * sending the current internal objects.
		 */
		_emitObjsUpdate() {
			document.dispatchEvent(new CustomEvent("update_objs", {
				detail: { "objs": this.objs }
			}));
		}

		/**
		 * Emit an update to the document notifying of a grippers update, 
		 * sending the current internal grippers.
		 */
		_emitGrippersUpdate() {
			document.dispatchEvent(new CustomEvent("update_grippers", {
				detail: { "grippers": this.grippers }
			}));
		}

	}; // class Replayer end
}); // on document ready end
