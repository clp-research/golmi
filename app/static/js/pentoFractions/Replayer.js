$(document).ready(function () {

	/**
	 * Reads the log and feeds updates back into views (or other components)
	 * using document-wide events.
	 * TODO: add framerate
	 */
	this.Replayer = class Replayer {
		constructor() {
			this._log;
			this.currentTime = 0;
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
			this.currentTime = 0;
			this._resetState();
			this._log = logData;
		}

		get log() {
			return this._log;
		}

		//TODO: Immediately display the state here or only once start() is called?
		set startTime(timeOffset) {
			// update internal state
			timeOffset = Math.min(timeOffset, this.endTime);
			this._fastForward(timeOffset);
			this.currentTime = timeOffset;
		}

		/**
		 * @return final timestamp of thelog or null if no log is loaded
		 */
		get endTime() {
			if (this.log) {
				return this.log[this.log.length-1][0];
			} else {
				return null;
			}
		}

		/**
		 * Start playing from the current point of time in the log.
		 * @param optional: set a time to start playing from
		 */ 
		start(startTime=null) {
			// stop any ongoing loop
			this._stopReadingLog();
			if (startTime != null) {
				if (typeof(startTime) != "number") {
					console.log("Error at start(): startTime must be numeric.",
						` Got ${startTime}`);
				} else {
					this.startTime = startTime;
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
			console.log("_startReadingLog(): not implemented.");
		}

		/**
		 * Stop the update loop.
		 */
		_stopReadingLog() {
			console.log("_stopReadingLog(): not implemented.");
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
		 * Update the internal state up to endTime without emitting any updates
		 */
		_fastForward(endTime) {
			console.log("_fastForward(): not implemented.");
		}

	}; // class Replayer end
}); // on document ready end
