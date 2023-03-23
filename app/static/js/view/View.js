$(document).ready(function () {
    /**
     * Abstract interface class. Separates the interface into background, objects and grippers
     * which concrete implementations of this view might want to draw separately to improve the
     * performance (the components are static to varying degrees).
     * While drawing functions lack implementations, internal data structures and basic communication
     * with the model are already sketched out in this class.
     * @param {Socket io connection to the server} modelSocket
     */
    this.View = class View {
        constructor(modelSocket) {
            this.socket = modelSocket;
            this._initSocketEvents();

            // Configuration. Is assigned at startDrawing()
            this.cols;			// canvas width in blocks
            this.rows;			// canvas height in blocks
            this.grid_factor;

            // Current state
            this.grippers = new Object();
            this.objs = new Object();
            this.objs_grid = new Object();
            this.targets = new Object();
            this.targets_grid = new Object();
        }

        /**
         * Start listening to events emitted by the model socket. After this
         * initialization, the view reacts to model updates.
         */
        _initSocketEvents() {
            // new state -> redraw object and gripper layer,
            // if targets are given, redraw background
            this.socket.on("update_state", (state) => {
                this.onUpdateState(state) // hook
                this.grippers = state["grippers"];
                this.objs = state["objs"];
                this.objs_grid = state["objs_grid"]
                this.targets = state["targets"];
                this.targets_grid = state["targets_grid"]
                this.redraw();
      
            });
            // new configuration -> save values and redraw everything
            this.socket.on("update_config", (config) => {
                this._loadConfig(config);
                this.redraw();
            });
        }

        // --- getter / setter --- //
        // canvas width in pixels.
        get canvasWidth() {
            console.log("get canvasWidth() at View: not implemented");
            return undefined;
        }

        get canvasHeight() {
            console.log("get canvasHeight() at View: not implemented");
            return undefined;
        }

        get blockSize() {
            return this.canvasWidth/this.cols;
        }

        // --- drawing functions --- //

        /**
         * Remove any old drawings.
         */
        clear() {
            console.log("clear() at View: not implemented");
        }

        /**
         * Draw background, objects, gripper.
         */
        draw() {
            this.drawBg();
            this.drawGr();
            this.drawObjs();
        }

        /**
         * Redraw everything.
         * In contrast to draw(), this function assumes the game has been drawn in the past
         * and the old drawing needs to be removed first.
         */
        redraw() {
            this.clear();
            this.draw();
        }

        /**
         * Draw a background to the game.
         */
        drawBg() {
            console.log("drawBg() at View: not implemented");
        }

        /**
         * Redraw the background.
         * In contrast to drawBg(), this function assumes the background has been drawn in the past
         * and the old drawing needs to be removed first.
         */
        redrawBg() {
            console.log("redrawBg() at View: not implemented");
        }

        /**
         * Draw the (static) objects.
         */
        drawObjs() {
            console.log(`drawObjs() at View: not implemented`);
        }

        /**
         * Redraw the (static) objects.
         * In contrast to drawObjs(), this function assumes the objects have been drawn in the past
         * and the old drawing needs to be removed first.
         */
        redrawObjs() {
            console.log(`redrawObjs() at View: not implemented`);
        }

        /**
         * Draw the gripper object (and, depending on the implementation, the gripped object too)
         * The Gripper is used to navigate on the canvas and move objects.
         */
        drawGr() {
            console.log("drawGr() at View: not implemented");
        }

        /**
         * Redraw the gripper object (and, depending on the implementation, the gripped object too).
         * In contrast to drawGr(), this function assumes the gripper has been drawn in the past
         * and the old drawing needs to be removed first.
         */
        redrawGr() {
            console.log("redrawGr() at View: not implemented");
        }

        onUpdateObjects(objs) {
            console.log(`onUpdateObjects() at View: not implemented`);
        }

        onUpdateTargets(targets) {
            console.log(`onUpdateTargets() at View: not implemented`);
        }

        onUpdateState(state) {
            console.log(`onUpdateState() at View: not implemented`);
        }


        /**
         * Loads a configuration received from the model. The values are saved since the configuration is
         * not expected to change frequently.
         * If no configuration is passed, it is requested from the model.
         * Implemented as an async function to make sure the configuration is complete before
         * subsequent steps (i.e. drawing) are made.
         * @param {config object, obtained from the model} config
         */
        _loadConfig(config) {
            // Save all relevant values
            this.cols = config.width * Math.max(1, Math.floor(1/config.move_step));
            this.rows = config.height * Math.max(1, Math.floor(1/config.move_step));
            this.grid_factor = Math.max(1, Math.floor(1/config.move_step))
        }

    }; // class View end
}); // on document ready end
