$(document).ready(function () {

    this.PentoBoardView = class PentoBoardView extends document.View {
        constructor(modelSocket, bgCanvas, objCanvas) {
            super(modelSocket);
            this.socket = modelSocket;
            this.bgCanvas = bgCanvas;
            this.objCanvas = objCanvas;
            this.rel_position_granularity = 3
            this.showGrid = false;
            this.clear();
        }

        onUpdateState(state) {
        }

        onUpdateObjects(objs) {
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
         * Draws a grid black on white as the background.
         */
        drawBg() {
            // set updates
            let ctx = this.bgCanvas.getContext("2d");

            // white rectangle for background
            ctx.fillStyle = "white";
            ctx.fillRect(0, 0, this.canvasWidth, this.canvasHeight);

            if (this.showGrid) {
                ctx.strokeStyle = "#f3f0f0";
                ctx.lineWidth = 1;

                let width_step = this.canvasWidth / this.rel_position_granularity
                let height_step = this.canvasHeight / this.rel_position_granularity
                // horizontal lines
                for (let row = 0; row <= this.rel_position_granularity; row++) {
                    let offset = row * height_step;
                    ctx.moveTo(0, offset);
                    ctx.lineTo(this.canvasWidth, offset);
                }
                // vertical lines
                for (let col = 0; col <= this.rel_position_granularity; col++) {
                    let offset = col * width_step;
                    ctx.moveTo(offset, 0);
                    ctx.lineTo(offset, this.canvasHeight);
                }
                // draw to the screen
                ctx.stroke()
            }
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
            let ctx = this.objCanvas.getContext("2d");
            ctx.beginPath();
            // draw each object
            for (const obj of Object.values(this.objs))	{
                // skip any gripped object here

                // we use the "gripped" here to indicate the "target piece"
                let objHighlight = false
                if (obj.gripped) {
                    objHighlight = "red"
                }

                let blockMatrix = obj.block_matrix;

                // call drawing helper functions with additional infos
                let params = {
                    x: obj.x,
                    y: obj.y,
                    color: obj.color,
                    highlight: objHighlight
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
                        if (this._isUpperBorder(bMatrix, c, r)) {
                            this._drawUpperBorder(ctx, x, y, params.highlight);
                        }
                        if (this._isLowerBorder(bMatrix, c, r)) {
                            this._drawLowerBorder(ctx, x, y, params.highlight);
                        }
                        if (this._isLeftBorder(bMatrix, c, r)) {
                            this._drawLeftBorder(ctx, x, y, params.highlight);
                        }
                        if (this._isRightBorder(bMatrix, c, r)) {
                            this._drawRightBorder(ctx, x, y, params.highlight);
                        }
                    }
                });
            }
        }


        _drawBoundingBox(ctx, x, y, lineColor = "grey", lineWidth = 1) {
            ctx.strokeStyle = lineColor;
            ctx.lineWidth = lineWidth;
            ctx.beginPath();
            ctx.moveTo(this._toPxl(x), this._toPxl(y));
            ctx.lineTo(this._toPxl(x + 5), this._toPxl(y)); // top right
            ctx.lineTo(this._toPxl(x + 5), this._toPxl(y + 5)); // bottom right
            ctx.lineTo(this._toPxl(x), this._toPxl(y + 5)); // bottom left
            ctx.closePath(); // return to starting point
            ctx.stroke(); // draw the returning line
        }

        _drawBlock(ctx, x, y, color, lineColor="grey", lineWidth=1) {
            // --- config ---
            ctx.fillStyle = color;
            let px = this._toPxl(x);
            let py = this._toPxl(y);
            let w = Math.abs(px - this._toPxl(x+1));
            let h =  Math.abs(py - this._toPxl(y+1));
            ctx.fillRect(px, py, w, h);
        }

        _drawUpperBorder(
            ctx, x, y, highlight=false, borderColor="black", borderWidth=2) {
            this._drawBorder(ctx, x, y, x+1, y, highlight, borderColor, borderWidth);
        }

        _drawLowerBorder(
            ctx, x, y, highlight=false, borderColor="black", borderWidth=2) {
            this._drawBorder(ctx, x, y+1, x+1, y+1, highlight, borderColor, borderWidth);
        }

        _drawLeftBorder(
            ctx, x, y, highlight=false, borderColor="black", borderWidth=2) {
            this._drawBorder(ctx, x, y, x, y+1, highlight, borderColor, borderWidth);
        }

        _drawRightBorder(
            ctx, x, y, highlight=false, borderColor="black", borderWidth=2) {
            this._drawBorder(ctx, x+1, y, x+1, y+1, highlight, borderColor, borderWidth);
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

        _isUpperBorder(blockMatrix, column, row) {
            // true if 'row' is the top row OR there is no block above
            return row == 0 || blockMatrix[row-1][column] == 0;
        }

        _isLowerBorder(blockMatrix, column, row) {
            // true if 'row' is the bottom row OR there is no block below
            return row == (blockMatrix.length-1) ||
                blockMatrix[row+1][column] == 0;
        }

        _isLeftBorder(blockMatrix, column, row) {
            // true if 'column' is the leftmost column OR there is no block
            // to the left
            return column == 0 || blockMatrix[row][column-1] == 0;
        }

        _isRightBorder(blockMatrix, column, row) {
            // true if 'column' is the rightmost column OR there is no block
            // to the right
            return column == (blockMatrix[row].length-1) ||
                blockMatrix[row][column+1] == 0;
        }

    }; // class LayerView end
}); // on document ready end
