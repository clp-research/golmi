$(document).ready(function () {
    // --- define globals --- //

    // Set to false to skip unit tests
    const SELFTEST = true;

    // expect same as backend e.g. the default "http://127.0.0.1:5000";
    const MODEL = window.location.origin
    console.log("Connect to " + MODEL)

    // parameters for random initial state
    // (state is generated once the configuration is received)
    const N_OBJECTS = 5;
    const N_GRIPPERS = 1;

    // --- create a socket --- //
    // don't connect yet
    let socket = io(MODEL, {
        autoConnect: false,
        auth: { "password": "GiveMeTheBigBluePasswordOnTheLeft" }
    });
    // debug: print any messages to the console
    localStorage.debug = 'socket.io-client:socket';

    // --- controller --- //
    // create a controller, we still need to attach a gripper in the model to it
    let controller = new document.LocalKeyController();

    // --- view --- //
    // Get references to the three canvas layers
    let bgLayer     = document.getElementById("background");
    let objLayer    = document.getElementById("objects");
    let grLayer     = document.getElementById("gripper");

    // Set up the view js, this also sets up key listeners
    const layerView = new document.LayerView(socket, bgLayer, objLayer, grLayer);

    // --- logger --- //
    const logView = new document.LogView(socket);

    // --- socket communication --- //
    socket.on("connect", () => {
        console.log("Connected to model server");
    });

    socket.on("disconnect", () => {
        console.log("Disconnected from model server");
        // demo of the logView: send the logged data to the server
        logView.addData("test", true);
        logView.sendData();
    });

    var setup_complete = false;
    socket.on("update_config", (config) => {
        // only do setup once (reconnections can occur, we don't want to reset the state every time)
        if (!setup_complete) {
            // ask model to load a random state
            socket.emit("random_init", {"n_objs": N_OBJECTS,
                                        "n_grippers": N_GRIPPERS,
                                        "random_gr_position":false,
                                        "area_block": "top",
                                        "area_target": "bottom"});
            // subscribe the controller to the only generated gripper
            controller.attachModel(socket, "0");
            setup_complete = true;
        }
    });

    // for debugging: log all events
    socket.onAny((eventName, ...args) => {
        console.log(eventName, args);
    });

    // --- stop and start drawing --- //
    function start() {
        // reset the controller in case any key is currently pressed
        controller.resetKeys()
        // manually establish a connection, connect the controller and load a state
        socket.connect();
    }

    function stop() {
        // reset the controller in case any key is currently pressed
        controller.resetKeys();
        // disconnect the controller
        controller.detachModel(socket, "0");
        // manually disconnect
        socket.disconnect();
    }

    // --- buttons --- //
    $("#start").click(() => {
        start();
        // disable this button, otherwise it is now in focus and Space/Enter will trigger the click again
        $("#start").prop("disabled", true);
    });
    $("#stop").click(() => {
        stop();
        // reactive the start button
        $("#start").prop("disabled", false);
    });
}); // on document ready end