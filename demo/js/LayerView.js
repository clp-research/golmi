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
			// Empty the canvas
			this.clear();

			// Set up key listeners
			this._initKeyListener();
		}

		// Canvas width in pixels. Assumes all 3 canvas are the same size
		get canvasWidth() {
			return this.bgCanvas.width;
		}

		get canvasHeight() {
			return this.bgCanvas.height;
		}

		// --- drawing functions --- //

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
		 * Draw the (static) objects.
		 */
		async drawObj() {
			// get objects from the model
			let objReq = new Request(`http://${this.modelAPI}/objects`, {method:"GET"});
			let response = await fetch(objReq);
			let objects;
			if (response.ok) { // Parse the response as json
				objects = await response.json();
			} else { // Something went wrong - emit an error message and leave the function
				console.log("Error: Could not fetch objects from the model API");
				return;
			}

			// get gripped object from the model (because it should not be drawn to this layer)
			let grippedObjReq = new Request(`http://${this.modelAPI}/gripper/grip`, {method:"GET"});
			response = await fetch(grippedObjReq);


			// accumulate the ids into an array
			let grippedIds = new Array();
			if (response.ok) { // Parse the response as json
				// response maps gripper ids to a map {obj-id -> obj-details}
				let gripperToObjMaps = await response.json();
				for (let objMap of Object.values(gripperToObjMaps)) {
					grippedIds = grippedIds.concat(Object.keys(objMap));
				}
			} else { // Something went wrong - emit an error message
				console.log("Error: Could not fetch gripped object from the model API");
			}

			// draw each object
			for (let [id, obj] of Object.entries(objects))	{
				// skip any gripped object here
				if (grippedIds.includes(id)) { continue; }

				// get info on how to draw type from config
				let blockMatrix = this.typeConfig[obj.type];
				
				// perform manipulations (rotate, mirror)
				//if (obj.rotation != 0) {
				//	blockMatrix = document.rotateByRearrange(blockMatrix, obj.rotation);
				//}
				// call drawing helper functions with additional infos (gripped, color)
				let ctx = this.objCanvas.getContext("2d");
				//TODO: size
				let params = {
					x: obj.x,
					y: obj.y,
					color: obj.color,
					highlight: false
				}
				this._drawBlockObj(ctx, blockMatrix, params);
			}
		}

		/**
		 * Redraw the (static) objects.
		 * In contrast to drawObj(), this function assumes the objects have been drawn in the past
		 * and the old drawing needs to be removed first.
		 */
		redrawObj() {
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
			ctx.lineStyle = "black";
			ctx.lineWidth = 1;

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
		 * Draw the gripper object and, if applicable, the gripped object.
		 * The gripper is used to navigate on the canvas and move objects.
		 */
		async drawGr() {
			// get gripper(s) and gripped object(s) from the model
			let gripperReq = new Request(`http://${this.modelAPI}/gripper`, {method:"GET"});
			let response = await fetch(gripperReq);
			let grippers;
			if (response.ok) { // Parse the response as json
				grippers = await response.json();
			} else { // Something went wrong - emit an error message and leave the function
				console.log("Error: Could not fetch grippers from the model API");
				return;
			}

			// get gripped object from the model
			let grippedObjsReq = new Request(`http://${this.modelAPI}/gripper/grip`, {method:"GET"});
			response = await fetch(grippedObjsReq);
			let grippedObjs;
			if (response.ok) { // Parse the response as json
				grippedObjs = await response.json();
				grippedObjs
			} else { // Something went wrong - emit an error message
				console.log("Error: Could not fetch gripped object from the model API");
			}

			// // set up
			// let ctx = this.grCanvas.getContext("2d");
			// let gripper= this.model.gripper;
			// // modify style depending on whether an object is gripped
			// let grSize = this.model.grippedObj ? 0.2 : 0.5;
			// this.canvas_ref.drawLine({
			// 	layer: false,
			// 	strokeStyle: "red",
			// 	strokeWidth: 2,
			// 	x1: this._toPxl(gripper.x-grSize), y1: this._toPxl(gripper.y-grSize),
			// 	x2: this._toPxl(gripper.x+grSize), y2: this._toPxl(gripper.y+grSize)
			// });
			// this.canvas_ref.drawLine({
			// 	layer: false,
			// 	strokeStyle: "red",
			// 	strokeWidth: 2,
			// 	x1: this._toPxl(gripper.x-grSize), y1: this._toPxl(gripper.y+grSize),
			// 	x2: this._toPxl(gripper.x+grSize), y2: this._toPxl(gripper.y-grSize)
			// });

			// let grippedObj = this.model.grippedObj;
			// if (!grippedObj) {
			// 	super.draw();
			// } else {
			// 	this.drawBg();
			// 	// draw all objects except the gripped one
			// 	this.model.objectIds.forEach((id) => { if (id != grippedObj) { this.drawObj(id); } });
			// 	// draw gripped object on top and finally the gripper
			// 	this.drawObj(grippedObj);
			// 	this.drawGr();
			// }
		}

		/**
		 * Redraw the gripper object and, if applicable, the gripped object.
		 * In contrast to drawGr(), this function expects the gripper has been drawn in the past
		 * and the old drawing needs to be removed first.
		 */
		redrawGr() {
			this.clearGr();
			this.drawGr();
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
						if (c == (bMatrix[r].length-1) || !(bMatrix[r][c+1])) { this._drawBorder(ctx, x+1, y, x+1, y+1, params.highlight); }
						// bottom
						if (r == (bMatrix.length-1) || !(bMatrix[r+1][c])) { this._drawBorder(ctx, x, y+1, x+1, y+1, params.highlight); }
						// left
						if (c == 0 || !(bMatrix[r][c-1])) { this._drawBorder(ctx, x, y, x, y+1, params.highlight); }
					}
				});
			}
		}

		_drawBlock(ctx, x, y, color, lineColor="grey", lineWidth=1) {
			// --- config ---
			ctx.fillStyle = color;

			ctx.beginPath();
			ctx.moveTo(this._toPxl(x), this._toPxl(y)); 
			ctx.lineTo(this._toPxl(x+1), this._toPxl(y)); // top right
			ctx.lineTo(this._toPxl(x+1), this._toPxl(y+1)); // bottom right
			ctx.lineTo(this._toPxl(x), this._toPxl(y+1)); // bottom left
			ctx.closePath(); // return to starting point
			ctx.stroke(); // draw the returning line
			ctx.fill(); // add color
		}

		_drawBorder(ctx, x1, y1, x2, y2, highlight=false, borderColor="black", borderWidth=2) {
			// --- config ---
			ctx.lineStyle = borderColor;
			ctx.lineWidth = borderWidth;
			// TODO: HIGHLIGHTS
			// shadowBlur is set to 0 if highlight is false, effectively making it invisible
			ctx.shadowBlur = highlight ? 10 : 0;
			ctx.shadowColor = highlight;

			ctx.beginPath();
			ctx.moveTo(this._toPxl(x1), this._toPxl(y1));
			ctx.lineTo(this._toPxl(x2), this._toPxl(y2));
			ctx.stroke();
		}

		_toPxl(coord) {
			return coord * this.blockSize;
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