$(document).ready(function () {
	
	// how to know what objects are gripped:
	// -> ask model when redrawing ( list option at model API?)
	// -> save it. have obj: gr_id -> [gripped]. Has to be updated if grip/ungrip occurs ...
	// but then when grip/ungrip occurs gripper is sent! so we have that info.
	// but gripper has to be drawn last? or not??
	// -> extra view-storage category : "gripped_objs?

	/**
	 * @param {URL of the View API} viewAPI
	 * @param {URL of the Model API} modelAPI
	 * @param {reference to the canvas DOM element to draw the background to} bgCanvas
	 * @param {reference to the canvas DOM element to draw the static objects to} objCanvas
	 * @param {reference to the canvas DOM element to draw grippers and gripped objects to} grCanvas
	 */
	this.LayerView = class LayerView extends document.View {
		constructor(viewAPI, modelAPI, bgCanvas, objCanvas, grCanvas) {
			super(viewAPI, modelAPI);
			// Three overlapping canvas
			this.bgCanvas	= bgCanvas;
			this.objCanvas	= objCanvas;
			this.grCanvas	= grCanvas;
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
		 * Draws a grid black on white as the background.
		 */
		drawBg() {
			// set updates
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
		 * Draw the (static) objects.
		 * @param {optional: object data, e.g. obtained from the view API. default: null} preloadedObjs
		 * @param {optional: Array holding the indices of gripped objects not to be redrawn here. default: null} preloadedGripped
		 */
		async drawObj(preloadedObjs=null, preloadedGripped=null) {
			// if no objects have been preloaded, load from the model
			let objects;
			if (!preloadedObjs) {
				let response = await fetch(new Request(`http://${this.modelAPI}/objects`, {method:"GET"}));
				if (response.ok) { // Parse the response as json
					objects = await response.json();
				} else { // Something went wrong - emit an error message and leave the function
					console.log("Error: Could not fetch objects from the model API");
					return;
				}
			} else {
				objects = preloadedObjs;
			}

			// if gripped objects have not been preloaded, get them from the model
			let grippedIds;
			if (!preloadedGripped) {
				// get gripped object from the model (because it should not be drawn to this layer)
				let response = await fetch(new Request(`http://${this.modelAPI}/gripper/grip`, {method:"GET"}));
				// accumulate the ids into an array
				grippedIds = new Array();
				if (response.ok) { // Parse the response as json
					// response maps gripper ids to a map {obj-id -> obj-details}
					let gripperToObjMaps = await response.json();
					for (const objMap of Object.values(gripperToObjMaps)) {
						if (objMap) {
							grippedIds = grippedIds.concat(Object.keys(objMap));
						}
					}
				} else { // Something went wrong - emit an error message
					console.log("Error: Could not fetch gripped object from the model API");
				}
			} else {
				grippedIds = preloadedGripped;
			}

			// draw each object
			for (const [id, obj] of Object.entries(objects))	{
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
		 * @param {optional: object data, e.g. obtained from the view API. default: null} preloadedObjs
		 * @param {optional: Array holding the indices of gripped objects not to be redrawn here. default: null} preloadedGripped
		 */
		redrawObj(preloadedObjs=null, preloadedGripped=null) {
			this.clearObj();
			this.drawObj(preloadedObjs, preloadedGripped);
		}

		/**
		 * Draw the gripper object and, if applicable, the gripped object.
		 * The gripper is used to navigate on the canvas and move objects.
		 * @param {gripper data, e.g. obtained from the view API} preloadedGrippers
		 * @return Array holding the indices of gripped objects
		 */
		async drawGr(preloadedGrippers=null) {
			// if grippers have not been preloaded, get them from the model
			let grippers;
			if (!preloadedGrippers) {
				// get gripper(s) and gripped object(s) from the model
				let response = await fetch(new Request(`http://${this.modelAPI}/gripper`, {method:"GET"}));
				if (response.ok) { // Parse the response as json
					grippers = await response.json();
				} else { // Something went wrong - emit an error message and leave the function
					console.log("Error: Could not fetch grippers from the model API");
					return;
				}
			} else {
				grippers = preloadedGrippers;
			}

			// remember gripped objects drawn to this layer
			let drawnObjects = new Array();

			// set up
			let ctx = this.grCanvas.getContext("2d");
			for (const [grId, gripper] of Object.entries(grippers)) {
				// draw any gripped object first (i.e. 'below' the gripper)
				if (gripper.gripped) {
					for (const [grippedId, grippedObj] of Object.entries(gripper.gripped)) {
						drawnObjects.push(grippedId);
						let blockMatrix = this.typeConfig[grippedObj.type];
						let params = {
							x: grippedObj.x,
							y: grippedObj.y,
							color: grippedObj.color,
							highlight: "grey" // apply highlight to a gripped object
						}
						this._drawBlockObj(this.grCanvas.getContext("2d"), blockMatrix, params);
					}
				}

				// modify style depending on whether an object is gripped
				let grSize = gripper.gripped ? 0.2 : 0.5;
					
				// draw the gripper itself
				// --- config ---
				ctx.lineStyle = "red";
				ctx.lineWidth = 2;
				// draw. The gripper is a simple cross
				ctx.beginPath();
				ctx.moveTo(this._toPxl(gripper.x-grSize), this._toPxl(gripper.y-grSize));
				ctx.lineTo(this._toPxl(gripper.x+grSize), this._toPxl(gripper.y+grSize));
				ctx.moveTo(this._toPxl(gripper.x-grSize), this._toPxl(gripper.y+grSize));
				ctx.lineTo(this._toPxl(gripper.x+grSize), this._toPxl(gripper.y-grSize));
				ctx.stroke();
			}
			return drawnObjects;
		}

		/**
		 * Redraw the gripper object and, if applicable, the gripped object.
		 * In contrast to drawGr(), this function expects the gripper has been drawn in the past
		 * and the old drawing needs to be removed first.
		 * @param {gripper data, e.g. obtained from the view API} preloadedGrippers
		 * @return Array holding the indices of gripped objects
		 */
		async redrawGr(preloadedGrippers=null) {
			this.clearGr();
			return await this.drawGr(preloadedGrippers);
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
			// TODO: fix highlights
			// shadowBlur is set to 0 if highlight is false, effectively making it invisible
			ctx.shadowBlur = highlight ? 5 : 0;
			ctx.shadowColor = highlight;
			ctx.lineStyle = borderColor;
			ctx.lineWidth = borderWidth;

			ctx.beginPath();
			ctx.moveTo(this._toPxl(x1), this._toPxl(y1));
			ctx.lineTo(this._toPxl(x2), this._toPxl(y2));
			ctx.stroke();
		}

		_toPxl(coord) {
			return coord * this.blockSize;
		}

		// --- Updating functions ---

		/**
		 * Process an update object, calling the appropriate redrawing functions.
		 * OVERWRITING the parent function, because LayerView draws gripped objects on the 
		 * same layer as the gripper. Therefore, to assure gripped objects are not redrawn on the
		 * object layer, drawGripper() returns the indices of gripped objects, which is then
		 * passed to drawObjs(). 
		 * @param {object containing the keys "grippers", "objs", "config"} update_obj
		 * @return Boolean: true if updates were made, false otherwise
		 */
		async _processUpdates(updates) {
			// keep track of whether any update was made
			let update_applied = false;
			// if the config has changed, redraw everything
			if (updates["config"]) {
				await this._loadConfig(updates["config"]);
				this.redraw();
				update_applied = true;
			} else {
				let grippedObjs = null;
				// if any gripper was changed, redraw the gripper layer
				if (updates["grippers"] && Object.keys(updates["grippers"]).length > 0) {
					grippedObjs = await this.redrawGr(updates["grippers"]);
					update_applied = true;
				}
				// there is only 3 layers here and the background does not need to be updated.
				// if any object was changed, redraw the object layer
				if (updates["objs"] && Object.keys(updates["objs"]).length > 0) {
					this.redrawObj(updates["objs"], grippedObjs);
					update_applied = true;
				}
			}
			return update_applied;
		}

	}; // class LayerView end
}); // on document ready end