$(document).ready(function () {

	/**
	 * Extends the generic View class by implementations of the drawing functions. 
	 * This class works with three stacked canvas layers: the 'background' holds a grid 
	 * (so if no grid is needed, the function drawBg() should be modified), the 'object'
	 * layer has all static objects, that is objects not currently gripped, and finally the
	 * 'gripper' layer displays any grippers as well as objects held by the grippers.
	 * The reasoning behind this separation is that these components need to be redrawn in 
	 * varying frequency: while the background is static unless the game configuration (board 
	 * dimensions, etc.) change, the objects are meant to be manipulated throughout an
	 * interaction and might have to be redrawn several times. The gripper as well as the currently 
	 * gripped objects however change continuously and have to be redrawn constantly.
	 * @param {Socket io connection to the server} modelSocket
	 * @param {reference to the canvas DOM element to draw the background to} bgCanvas
	 * @param {reference to the canvas DOM element to draw the static objects to} objCanvas
	 * @param {reference to the canvas DOM element to draw grippers and gripped objects to} grCanvas
	 */
	this.LayerView = class LayerView extends document.View {
		constructor(modelSocket, bgCanvas, objCanvas, grCanvas) {
			super(modelSocket);
			// Three overlapping canvas
			this.bgCanvas	= bgCanvas;
			this.objCanvas	= objCanvas;
			this.grCanvas	= grCanvas;

			// array holding the currently gripped objects
			this.grippedObjs = new Array();

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
		 */
		drawObjs() {
			// first draw targets
			for (const obj of Object.values(this.targets))	{
				// skip any gripped object here
				if (obj.gripped) { continue; }

				let blockMatrix = obj.block_matrix;
				
				// call drawing helper functions with additional infos (gripped, color)
				let ctx = this.objCanvas.getContext("2d");
				let params = {
					x: obj.x,
					y: obj.y,
					color: "Cornsilk",
					highlight: true
				}
				this._drawBlockObj(ctx, blockMatrix, params);
			}
			// draw each object
			for (const obj of Object.values(this.objs))	{
				// skip any gripped object here
				if (obj.gripped) { continue; }

				let blockMatrix = obj.block_matrix;
				
				// call drawing helper functions with additional infos (gripped, color)
				let ctx = this.objCanvas.getContext("2d");
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
		 * In contrast to drawObjs(), this function assumes the objects have been drawn in the past
		 * and the old drawing needs to be removed first.
		 */
		redrawObjs() {
			this.clearObj();
			this.drawObjs();
		}

		/**
		 * Draw the gripper object and, if applicable, the gripped object.
		 * The gripper is used to navigate on the canvas and move objects.
		 */
		drawGr() {
			// set up
			let ctx = this.grCanvas.getContext("2d");
			for (const [grId, gripper] of Object.entries(this.grippers)) {
				// draw any gripped object first (i.e. 'below' the gripper)
				if (gripper.gripped) {
					for (const [grippedId, grippedObj] of Object.entries(gripper.gripped)) {
						let blockMatrix = grippedObj.block_matrix;
						
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

	}; // class LayerView end
}); // on document ready end
