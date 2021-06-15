$(document).ready(function () {
	
	/**
	 * @param {URL of the View API} viewAPI
	 * @param {URL of the Model API} modelAPI
	 * @param {URL of the Controller API} controllerAPI
	 * @param {reference to the canvas DOM element to draw the background to} bgCanvas
	 * @param {reference to the canvas DOM element to draw the static objects to} objCanvas
	 * @param {reference to the canvas DOM element to draw grippers and gripped objects to} grCanvas
	 */
	this.LayerView = class LayerView extends document.View {
		constructor(viewAPI, modelAPI, controllerAPI, bgCanvas, objCanvas, grCanvas) {
			super(viewAPI, modelAPI, controllerAPI);
			// Three overlapping canvas
			this.bgCanvas	= bgCanvas;
			this.objCanvas	= objCanvas;
			this.grCanvas	= grCanvas;

			this.loopId;		// stores timeout ID to manage the update request loop

			// Configuration. Is assigned at startDrawing()
			this.blockSize;		// block width/height in pixels
			this.cols;			// canvas width in blocks
			this.rows;			// canvas height in blocks
			this.typeConfig;	// map: type -> block matrix

			// Set up key listeners
			this._initKeyListener();

			// Empty the canvas
			this.clear();
		}

		// Canvas width in pixels. Assumes all 3 canvas are the same size
		get canvasWidth() {
			return this.bgCanvas.width;
		}

		get canvasHeight() {
			return this.bgCanvas.height;
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


		// sleep(ms) {
		// 	return new Promise(resolve => setTimeout(resolve, ms));
		// }

		/**
		 *  Remove any old drawings.
		 */
		clear() {
			// clear all three canvas
			this.clearBg();
			this.clearObj();
			this.clearGr();
		}

		/**
		 * Remove old drawings from the background layer.
		 */
		clearBg() {
			let ctx = this.bgCanvas.getContext("2d");
			ctx.clearRect(0, 0, this.bgCanvas.width, this.bgCanvas.height);
		}

		/**
		 * Remove old drawings from the object layer.
		 */
		clearObj() {
			let ctx = this.objCanvas.getContext("2d");
			ctx.clearRect(0, 0, this.objCanvas.width, this.objCanvas.height);
		}

		/**
		 * Remove old drawings from the gripper layer.
		 */
		clearGr() {
			let ctx = this.grCanvas.getContext("2d");
			ctx.clearRect(0, 0, this.grCanvas.width, this.grCanvas.height);
		}

		/**
		 * Override base class function. With the layerless method, the gripped object needs
		 * to be drawn last to appear 'on top'.
		 */
		draw() {
			this.drawBg();
			//this.drawObj();
			//this.drawGr();
		}

		drawObj(id) {
			// get info from model (type, x, y, rotation, mirror, gripped, color)
			let obj = this.model.objById(id);
			if (!obj) {
				console.log(`Error at drawObj(): Couldn't find object with id ${id}`);
				return;
			}
			// get info on how to draw type from config
			let blockMatrix = this.typeConfig[obj.type];
			// perform manipulations (rotate, mirror)
			if (obj.rotation != 0) {
				blockMatrix = document.rotateByRearrange(blockMatrix, obj.rotation);
			}
			// call drawing helper functions with additional infos (gripped, color)
			let ctx = this.canvas.getContext("2d");
			//TODO: size
			let params = {
				x: obj.x,
				y: obj.y,
				color: obj.color,
				highlight: obj.gripped ? "black" : false
			}
			this._drawBlockObj(ctx, blockMatrix, params);
		}

		/**
		 * Redraw a single object.
		 * In contrast to drawObj(), this function assumes the object has been drawn in the past
		 * and the old drawing needs to be removed first.
		 * @param {identifier of the object to be drawn, matches an id in the model's state} id
		 */
		redrawObj(id) {
			this.clearObj();
			this.drawObj();
		}

		/**
		 * Draws a grid black on white as the background.
		 */
		drawBg() {
			// set up
			let ctx = this.bgCanvas.getContext("2d");
			ctx.fillStyle = "white";
			ctx.strokeStyle = "black";
			ctx.strokeWidth = 1;

			// white rectangle for background
			ctx.fillRect(0,0, this.canvasWidth, this.canvasHeight);

			// horizontal lines
			for (let row = 0; row <= this.rows; row++) {
				ctx.moveTo(0, row*this.blockSize);
				ctx.lineTo(this.canvasWidth, row*this.blockSize);
			}
			// vertical lines
			for (let col = 0; col <= this.cols; col++) {
				ctx.moveTo(col*this.blockSize, 0);
				ctx.lineTo(col*this.blockSize, this.canvasHeight);
			}
			// draw to the screen
			ctx.stroke();
		}

		/**
		 * Redraw the background.
		 * In contrast to drawBg(), this function assumes the background has been drawn in the past
		 * and the old drawing needs to be removed first.
		 */ 
		redrawBg() {
			this.clearBg();
			this.drawBg();
		}

		/**
		 * Draw the gripper object (used to navigate on the canvas and move objects)
		 */
		drawGr() {
			let gripper= this.model.gripper;
			// modify style depending on whether an object is gripped
			let grSize = this.model.grippedObj ? 0.2 : 0.5;
			this.canvas_ref.drawLine({
				layer: false,
				strokeStyle: "red",
				strokeWidth: 2,
				x1: this._toPxl(gripper.x-grSize), y1: this._toPxl(gripper.y-grSize),
				x2: this._toPxl(gripper.x+grSize), y2: this._toPxl(gripper.y+grSize)
			});
			this.canvas_ref.drawLine({
				layer: false,
				strokeStyle: "red",
				strokeWidth: 2,
				x1: this._toPxl(gripper.x-grSize), y1: this._toPxl(gripper.y+grSize),
				x2: this._toPxl(gripper.x+grSize), y2: this._toPxl(gripper.y-grSize)
			});

			let grippedObj = this.model.grippedObj;
			if (!grippedObj) {
				super.draw();
			} else {
				this.drawBg();
				// draw all objects except the gripped one
				this.model.objectIds.forEach((id) => { if (id != grippedObj) { this.drawObj(id); } });
				// draw gripped object on top and finally the gripper
				this.drawObj(grippedObj);
				this.drawGripper();
			}
		}

		/**
		 * Redraw the gripper object. 
		 * In contrast to drawGripper(), this function expects the gripper has been drawn in the past
		 * and the old drawing needs to be removed first.
		 */
		redrawGripper() {
			this.clearGr();
			this.drawGr();
		}

		/**
		 * Load objects from the model and draw.
		 */
		initialDraw() {
			this.draw();
		}

		// --- draw helper functions ---

		_drawBlockObj(ctx, bMatrix, params) {
			// Draw blocks
			for (let r=0; r<bMatrix.length;r++) {
				bMatrix[r].forEach((block, c) =>  {
					if (block) { // draw if matrix field contains a 1
						let x = params.x + c;
						let y = params.y + r;
						this._drawBlock(ctx, x, y, params.color);
						// draw object borders
						// top
						if (r == 0 || !(bMatrix[r-1][c])) { this._drawBorder(ctx, x, y, x+1, y, params.highlight); }
						// right
						if (c == bMatrix[r].length || !(bMatrix[r][c+1])) { this._drawBorder(ctx, x+1, y, x+1, y+1, params.highlight); }
						// bottom
						if (r == bMatrix.length || !(bMatrix[r+1][c])) { this._drawBorder(ctx, x, y+1, x+1, y+1, params.highlight); }
						// left
						if (c == 0 || !(bMatrix[r][c-1])) { this._drawBorder(ctx, x, y, x, y+1, params.highlight); }
					}
				});
			}
		}

		_drawBlock(ctx, x, y, color, lineColor="grey", lineWidth=1) {
			// TODO: does highlight work???
			// --- config ---
			//ctx.shadowColor = highlight;
			// shadowBlur is set to 0 if highlight is false, effectively making it invisible
			//ctx.shadowBlur = highlight ? 10 : 0;
			// --- start drawing ---
			this.canvas_ref.drawPath({
				strokeStyle: lineColor,
				strokeWidth: lineWidth,
				fillStyle: color,
				closed: true, // automatically return to starting point after last coordinate
				p1: {
					type: "line",
					x1: this._toPxl(x), y1: this._toPxl(y),		// starting point: top left
					x2: this._toPxl(x+1), y2: this._toPxl(y),	// top right
					x3: this._toPxl(x+1), y3: this._toPxl(y+1),	// bottom right
					x4: this._toPxl(x), y4: this._toPxl(y+1)	// bottom left
				}
			});
			//ctx.beginPath();
			//ctx.moveTo(this._toPxl(x), this._toPxl(y)); 
			//ctx.lineTo(this._toPxl(x+1), this._toPxl(y)); // top right
			//ctx.lineTo(this._toPxl(x+1), this._toPxl(y+1)); // bottom right
			//ctx.lineTo(this._toPxl(x), this._toPxl(y+1)); // bottom left
			//ctx.closePath(); // return to starting point
			//ctx.stroke(); // draw the returning line
			//ctx.fill(); // add color
		}

		_drawBorder(ctx, x1, y1, x2, y2, highlight=false, borderColor="black", borderWidth=2) {
			this.canvas_ref.drawLine({
				strokeStyle: borderColor,
				strokeWidth: borderWidth,
				shadowBlur: highlight ? 10 : 0,
				shadowColor: highlight,
				x1: this._toPxl(x1), y1: this._toPxl(y1),
				x2: this._toPxl(x2), y2:this._toPxl(y2)
			})
		}

		_toPxl(coord) {
			return coord * this.blockSize;
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
		    	// Fetch updates that have been posted the the View API
				let updates = await thisInstance._getUpdates();
				// if there are updates, draw and check for further updates immediately
				while (updates) {
					thisInstance._processUpdates(updates);
					updates = await thisInstance._getUpdates();
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
			console.log(this)
			// query the view for new updates to apply
			let updateReq = new Request(`http://${this.viewAPI}/updates`, {method:"GET"});
			let response = await fetch(updateReq);
			if (response.status == 204) { // No updates
				return null
			} else if (response.ok) { // Parse the response as json and save the config values
				let json_data = await response.json();
				// check if empty object
				return json_data;
			} else { // Something went wrong - emit an error message
				console.log("Error: Could not fetch updates from the view API");
				return null
			}
		}

		_processUpdates() {
			console.log("_processUpdates at LayerView: not implemented");
		}

		// --- User events ---

		/**
		 * Register the key listeners to allow gripper manipulation.
		 * Notifies the associated controller of key events.
		 */
		_initKeyListener() { 
			$(document).keydown( e => {
				let notifyController = new Request(`http://${this.controllerAPI}/key-pressed/${e.keyCode}`, {method:"POST"});
				fetch(notifyController)
				.then( r => {
					if (!r.ok) {
						// TODO: inform user about controls ?
						console.log("Unassigned key pressed.");
					}
				});
			});
		}

	}; // class LayerView end
}); // on document ready end