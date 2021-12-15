$(document).ready(function () {

    this.DynaMattView = class DynaMattView extends document.View {
        constructor(modelSocket, bgCanvas, objCanvas, func_restart) {
            super(modelSocket);
            this.bgCanvas = bgCanvas;
            this.objCanvas = objCanvas;
            this.clear();
            this.func_restart = func_restart
            this.IA = new document.IA();
            this.messages = new document.Messages();
        }

        /** Select one of the objects and give instruction **/
        onUpdateState(state) {
            // TODO Selecting the target should not be part of the view (but the task)
            this.targetObj = null
            let objs = Object.values(state.objs) // objs is a n object
            if (objs.length > 0) {
                const selection = document.randomFromArray(objs);
                if (selection) {
                    // we do this now at the backend via mouseclick
                    // selection.gripped = true
                    this.giveInstruction(objs, selection);
                    this.targetObj = selection
                }
            }
        }

        onUpdateObjects(objs) {
            let objects = Object.values(objs)
            // this is supposed to be backend logic
            if (this.targetObj) {
                // check success condition
                objects.forEach(obj => {
                    if (obj.gripped) {
                        if (this.targetObj.id_n === obj.id_n) {
                            this.func_restart()
                        }
                    }
                })
            }
        }

        // --- User communication --- //

        welcome() {
            // welcome the participant
            this.messages.queue("Welcome! I'm Matthew.");
        }

        goodbye() {
            this.messages.queue("Have a nice day");
        }

        giveInstruction(currentObjects, currentTarget) {
            let instr = this.IA.generate(currentObjects, currentTarget)
            this.messages.queue(instr, "instruction");
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
            ctx.fillStyle = "white";
            ctx.lineStyle = "black";
            ctx.lineWidth = 1;

            // white rectangle for background
            ctx.fillRect(0, 0, this.canvasWidth, this.canvasHeight);

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
            for (const obj of Object.values(this.targets)) {
                // skip any gripped object here
                if (obj.gripped) {
                    continue;
                }

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
        }

        _drawBlock(ctx, x, y, color, lineColor = "grey", lineWidth = 1) {
            // --- config ---
            ctx.fillStyle = color;

            ctx.beginPath();
            ctx.moveTo(this._toPxl(x), this._toPxl(y));
            ctx.lineTo(this._toPxl(x + 1), this._toPxl(y)); // top right
            ctx.lineTo(this._toPxl(x + 1), this._toPxl(y + 1)); // bottom right
            ctx.lineTo(this._toPxl(x), this._toPxl(y + 1)); // bottom left
            ctx.closePath(); // return to starting point
            ctx.stroke(); // draw the returning line
            ctx.fill(); // add color
        }

        _drawBorder(ctx, x1, y1, x2, y2, highlight = false, borderColor = "black", borderWidth = 2) {
            // --- config ---
            // TODO: fix highlights
            // shadowBlur is set to 0 if highlight is false, effectively making it invisible
            ctx.shadowBlur = highlight ? 10 : 0;
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
