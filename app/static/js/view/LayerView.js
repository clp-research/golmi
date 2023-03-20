$(document).ready(function () {

    /**
     * Extends the generic View class by implementations of the drawing
     * functions.
     * This class works with three stacked canvas layers: the 'background'
     * holds a grid and optionally marks target positions for objects, the
     * 'object' layer has all static objects (objects not currently gripped,
     * and finally the 'gripper' layer displays grippers as well as objects
     * held by the grippers.
     * The reasoning behind this separation is that these components need to
     * be redrawn in varying frequency: while the background is static unless
     * the game configuration (board dimensions, etc.) or object target
     * positions change, the objects are meant to be manipulated throughout an
     * interaction and might have to be redrawn several times. The gripper as
     * well as the currently gripped objects however change continuously and
     * have to be redrawn constantly.
     * @param {Socket io connection to the server} modelSocket
     * @param {reference to the canvas DOM element to draw the background to}
        bgCanvas
     * @param {reference to the canvas DOM element to draw the static objects
        to} objCanvas
     * @param {reference to the canvas DOM element to draw grippers and
        gripped objects to} grCanvas
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
            this.draw_grid = false;
            this.draw_obj_inner_borders = false;

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
            let ctx = this.bgCanvas.getContext("2d");
            // important: https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/clearRect
            // using beginPath() after clear() prevents odd behavior
            ctx.beginPath();
            ctx.fillStyle = "white";
            ctx.lineStyle = "black";
            ctx.lineWidth = 1;

            // white rectangle for background
            ctx.fillRect(0, 0, this.canvasWidth, this.canvasHeight);

            if (this.draw_grid) {
                // horizontal lines
                for (let row = 0; row <= this.rows; row++) {
                    ctx.moveTo(0, row * this.blockSize);
                    ctx.lineTo(this.canvasWidth, row * this.blockSize);
                }
                // vertical lines
                for (let col = 0; col <= this.cols; col++) {
                    ctx.moveTo(col * this.blockSize, 0);
                    ctx.lineTo(col * this.blockSize, this.canvasHeight);
                }
            }
            // draw to the screen
            ctx.stroke();

            // add targets
            console.log(this.targets_grid)
            console.log(this.targets)
            this.plotArrayBoard(ctx, this.targets_grid, this.targets, "cornsilk")
        }

        /**
         * Redraw the background.
         * In contrast to drawBg(), this function assumes the background has
         * been drawn before and the old drawing needs to be removed first.
         */
        redrawBg() {
            this.clearBg();
            this.drawBg();
        }

        /**
         * Draw the (static) objects.
         */
        drawObjs() {
            let ctx = this.objCanvas.getContext("2d");
            ctx.beginPath();
            this.plotArrayBoard(ctx, this.objs_grid, this.objs)
        }


        plotArrayBoard(ctx, board, obj_mapping, overwrite_color=null){
            for (let [key, value] of Object.entries(board)) {
                
                let position = key.split(":")
                let i = parseInt(position[0])
                let j = parseInt(position[1])

                for (let obj_idn of value){
                    let this_obj = obj_mapping[obj_idn]                    
                    let color = (this_obj.gripped) ? ("black") : (this_obj.color)

                    // the color must be overwrittenb
                    color = (overwrite_color !== null) ? overwrite_color : color

                    this._drawBlock(ctx, j, i, color, this_obj.gripped);

                    // draw borders
                    if (this._isUpperBorder(board, i, j, obj_idn)) {
                        this._drawUpperBorder(ctx, j, i);
                    }
                    if (this._isLowerBorder(board, i, j, obj_idn)) {
                        this._drawLowerBorder(ctx, j, i);
                    }
                    if (this._isLeftBorder(board, i, j, obj_idn)) {
                        this._drawLeftBorder(ctx, j, i);
                    }
                    if (this._isRightBorder(board, i, j, obj_idn)) {
                        this._drawRightBorder(ctx, j, i);
                    }   
                }
            }
        }

        /**
         * Redraw the (static) objects.
         * In contrast to drawObjs(), this function assumes the objects have
         * been drawn before and the old drawing needs to be removed first.
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
            let ctx = this.grCanvas.getContext("2d");
            ctx.beginPath()
            for (const [grId, gripper] of Object.entries(this.grippers)) {
                // draw any gripped object first (i.e. 'below' the gripper)
                // if (gripper.gripped) {
                //     for (const [grippedId, grippedObj] of Object.entries(gripper.gripped)) {
                //         let blockMatrix = grippedObj.block_matrix;

                //         let params = {
                //             x: grippedObj.x,
                //             y: grippedObj.y,
                //             color: grippedObj.color,
                //             highlight: "black" // highlight a gripped object
                //         }
                //         this._drawBlockObj(ctx,
                //                            blockMatrix,
                //                            params);
                //     }
                // }

                // modify style depending on whether an object is gripped
                let grSize = gripper.gripped ? 0.1 : 0.3;

                // draw the gripper itself
                // --- config ---
                ctx.strokeStyle = "#000000";
                ctx.lineWidth = 2;
                // draw. The gripper as a simple cross
                // Note: coordinates are at a tiles upper-left corner!
                // We draw a gripper from that corner to the bottom-right
                ctx.beginPath();
                // top-left to bottom-right

                let x = gripper.x * this.grid_factor 
                let y = gripper.y * this.grid_factor 


                ctx.moveTo(this._toPxl(x - grSize), this._toPxl(y - grSize));
                ctx.lineTo(this._toPxl(x + 1 + grSize), this._toPxl(y + 1 + grSize));
                // bottom-left to top-right
                ctx.moveTo(this._toPxl(x - grSize), this._toPxl(y + 1 + grSize));
                ctx.lineTo(this._toPxl(x + 1 + grSize), this._toPxl(y - grSize));
                ctx.stroke();
            }
            // this.redrawObjs()
        }

        /**
         * Redraw the gripper object and, if applicable, the gripped object.
         * In contrast to drawGr(), this function expects the gripper has been
         * drawn before and the old drawing needs to be removed first.
         */
        redrawGr() {
            this.clearGr();
            this.drawGr();
        }

        // --- draw helper functions ---

        // _drawBlockObj(ctx, bMatrix, params) {
        //     // Draw blocks
        //     for (let r=0; r<bMatrix.length;r++) {
        //         bMatrix[r].forEach((block, c) =>  {
        //             if (block) { // draw if matrix field contains a 1
        //                 let x = params.x + c;
        //                 let y = params.y + r;
        //                 this._drawBlock(ctx, x, y, params.color);
        //                 // draw object borders
        //                 if (this._isUpperBorder(bMatrix, c, r)) {
        //                     this._drawUpperBorder(ctx, x, y, params.highlight);
        //                 }
        //                 if (this._isLowerBorder(bMatrix, c, r)) {
        //                     this._drawLowerBorder(ctx, x, y, params.highlight);
        //                 }
        //                 if (this._isLeftBorder(bMatrix, c, r)) {
        //                     this._drawLeftBorder(ctx, x, y, params.highlight);
        //                 }
        //                 if (this._isRightBorder(bMatrix, c, r)) {
        //                     this._drawRightBorder(ctx, x, y, params.highlight);
        //                 }
        //             }
        //         });
        //     }
        // }

        _drawBlock(ctx, x, y, color, lineColor="grey", lineWidth=1) {
            // --- config ---
            ctx.fillStyle = color;

            ctx.beginPath();
            ctx.moveTo(this._toPxl(x), this._toPxl(y));
            ctx.lineTo(this._toPxl(x+1), this._toPxl(y)); // top right
            ctx.lineTo(this._toPxl(x+1), this._toPxl(y+1)); // bottom right
            ctx.lineTo(this._toPxl(x), this._toPxl(y+1)); // bottom left
            ctx.closePath(); // return to starting point
            if (this.draw_obj_inner_borders) {
                ctx.stroke(); // draw the returning line
            }
            ctx.fill(); // add color
        }

        _drawUpperBorder(
            ctx, x, y, highlight=false, borderColor="black", borderWidth=2) {
            this._drawBorder(ctx, x, y, x+1, y, highlight);
        }

        _drawLowerBorder(
            ctx, x, y, highlight=false, borderColor="black", borderWidth=2) {
            this._drawBorder(ctx, x, y+1, x+1, y+1, highlight);
        }

        _drawLeftBorder(
            ctx, x, y, highlight=false, borderColor="black", borderWidth=2) {
            this._drawBorder(ctx, x, y, x, y+1, highlight);
        }

        _drawRightBorder(
            ctx, x, y, highlight=false, borderColor="black", borderWidth=2) {
            this._drawBorder(ctx, x+1, y, x+1, y+1, highlight);
        }

        _drawBorder(ctx, x1, y1, x2, y2, highlight=false, borderColor="black",
            borderWidth=2) {
            // --- config ---
            // for no highlight, shadowBlur is set to 0 (= invisible)
            ctx.shadowBlur = highlight ? 5 : 0;
            ctx.shadowColor = highlight;
            ctx.lineStyle = borderColor;
            ctx.lineWidth = borderWidth;

            ctx.beginPath();
            ctx.moveTo(this._toPxl(x1), this._toPxl(y1));
            ctx.lineTo(this._toPxl(x2), this._toPxl(y2));
            ctx.stroke();
            ctx.shadowBlur = 0;
        }

        _toPxl(coord) {
            return coord * this.blockSize;
        }

        _isUpperBorder(sparse_matrix, row, column, this_obj_idn) {
            if (row === 0 || (!(`${row-1}:${column}` in sparse_matrix))){
                return true;
            } else if (!(sparse_matrix[`${row-1}:${column}`].includes(this_obj_idn))) {
                return true
            }
            return false
        }

        _isLowerBorder(sparse_matrix, row, column, this_obj_idn) {
            if (row === this.rows - 1 || (!(`${row+1}:${column}` in sparse_matrix))){
                return true;
            } else if (!(sparse_matrix[`${row+1}:${column}`].includes(this_obj_idn))) {
                return true
            }
            return false
        }

        _isLeftBorder(sparse_matrix, row, column, this_obj_idn) {
            if (column === 0 || (!(`${row}:${column-1}` in sparse_matrix))){
                return true;
            } else if (!(sparse_matrix[`${row}:${column-1}`].includes(this_obj_idn))) {
                return true
            }
            return false
        }

        _isRightBorder(sparse_matrix, row, column, this_obj_idn) {
            if (column === this.cols - 1 || (!(`${row}:${column+1}` in sparse_matrix))){
                return true;
            } else if (!(sparse_matrix[`${row}:${column+1}`].includes(this_obj_idn))) {
                return true
            }
            return false
        }
    }; // class LayerView end
}); // on document ready end
