$(document).ready(function () {

    this.PentoBoardView = class PentoBoardView extends document.View {
        constructor(modelSocket, bgCanvas, objCanvas) {
            super(modelSocket);
            this.socket = modelSocket;
            this.bgCanvas = bgCanvas;
            this.objCanvas = objCanvas;
            this.rel_position_granularity = 3
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
            // draw each object
            for (const obj of Object.values(this.objs)) {
                // skip any gripped object here
                let blockMatrix = obj.block_matrix;

                // we use the "gripped" here to indicate the "target piece"
                let objHighlight = false
                if (obj.gripped) {
                    objHighlight = "red"
                }

                // call drawing helper functions with additional infos (gripped, color)
                let ctx = this.objCanvas.getContext("2d");
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
            for (let r = 0; r < bMatrix.length; r++) {
                bMatrix[r].forEach((block, c) => {
                    if (block) { // draw if matrix field contains a 1
                        let x = params.x + c;
                        let y = params.y + r;
                        this._drawBlock(ctx, x, y, params.color);
                        // draw object borders
                        // top
                        if (r == 0 || !(bMatrix[r - 1][c])) {
                            this._drawBorder(ctx, x, y, x + 1, y, params.highlight);
                        }
                        // right
                        if (c == (bMatrix[r].length - 1) || !(bMatrix[r][c + 1])) {
                            this._drawBorder(ctx, x + 1, y, x + 1, y + 1, params.highlight);
                        }
                        // bottom
                        if (r == (bMatrix.length - 1) || !(bMatrix[r + 1][c])) {
                            this._drawBorder(ctx, x, y + 1, x + 1, y + 1, params.highlight);
                        }
                        // left
                        if (c == 0 || !(bMatrix[r][c - 1])) {
                            this._drawBorder(ctx, x, y, x, y + 1, params.highlight);
                        }
                    }
                });
            }
            /*
            if (params.highlight) {
                this._drawBoundingBox(ctx, params.x, params.y, "red", 5)
            } else {
                this._drawBoundingBox(ctx, params.x, params.y, "black", 3)
            }
             */
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

        _drawBlock(ctx, x, y, color, lineColor = "grey", lineWidth = 1) {
            // --- config ---
            ctx.fillStyle = color;
            ctx.strokeStyle = lineColor;
            ctx.lineWidth = lineWidth;

            ctx.beginPath();
            ctx.moveTo(this._toPxl(x), this._toPxl(y));
            ctx.lineTo(this._toPxl(x + 1), this._toPxl(y)); // top right
            ctx.lineTo(this._toPxl(x + 1), this._toPxl(y + 1)); // bottom right
            ctx.lineTo(this._toPxl(x), this._toPxl(y + 1)); // bottom left
            ctx.closePath(); // return to starting point
            ctx.stroke(); // draw the returning line
            ctx.fill(); // add color
        }

        _drawBorder(ctx, x1, y1, x2, y2, borderColor = "black", borderWidth = 2, highlight = false) {
            // --- config ---
            // TODO: fix highlights
            // shadowBlur is set to 0 if highlight is false, effectively making it invisible
            ctx.strokeStyle = borderColor;
            ctx.lineWidth = borderWidth;
            if (highlight) {
                ctx.strokeStyle = "red";
                ctx.lineWidth = 5;
            }

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
