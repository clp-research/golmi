$(document).ready(function () {
    // --- define globals --- //

    // Set to false to skip unit tests
    const SELFTEST = true;

    // expect same as backend e.g. the default "127.0.0.1:5000"
    const MODEL = window.location.origin
    console.log("Connect to " + MODEL);

    // --- create a socket --- //
    // don't connect yet
    let socket = io(MODEL, { autoConnect: false, auth: {
        "password": "GiveMeTheBigBluePasswordOnTheLeft"
    }});
    // debug: print any messages to the console
    localStorage.debug = "socket.io-client:socket";

    // --- controller --- //
    // create a controller, we still need to attach a gripper in the model to it
    let controller = new document.LocalTalkativeKeyController();

    // --- view --- //
    // Get references to the three canvas layers
    let bgLayer     = document.getElementById("background");
    let objLayer    = document.getElementById("objects");
    let grLayer     = document.getElementById("gripper");

    // Set up the view js, this also sets up key listeners
    const layerView = new document.LayerView(
        socket, 
        bgLayer, 
        objLayer, 
        grLayer,
        { bgColor: "white", bgGridShow: false }
    );

    // --- logger --- //
    const logView = new document.LogView(socket, false);

    // --- task generator --- //

    const N_OBJECTS = 20;
    const N_GRIPPERS = 0;

    // --- configuration --- //
    const record_config = {
        "width": 40,
        "height": 40,
        "action_interval": 0.1
    }

    // --- socket communication --- //
    socket.on("connect", () => {
        console.log("Connected to model server");
    });

    socket.on("update_config", (new_config) => {
        // check if this is the config we sent -
        // we ignore the initially sent default config
        if (Object.keys(record_config).every(key => {
                return new_config[key] == record_config[key];})) {
            // now do the setup and start recording!
            // ask model to load a random state
            socket.emit("random_init", {
                "n_objs": N_OBJECTS,
                "n_grip": N_GRIPPERS,
                "random_grip":false,
                "area_block": "all",
                "area_target": "all"
            });
            // subscribe the controller to the only generated gripper
            controller.attachModel(socket, "0");
        }
    });

    // --- stop and start drawing --- //
    function start() {
        logView.clearLog();
        // reset the controller in case any key is currently pressed
        controller.resetKeys()
        // manually establish a connection
        socket.connect();
        // send an initial config
        socket.emit("load_config", record_config);
    }

    function stop() {
        // reset the controller in case any key is currently pressed
        controller.resetKeys();
        logView.sendData();
    }

    // --- buttons --- //
    $("#start").click(() => {
        start();
        // disable this button, otherwise it is now in focus and Space/Enter
        // will trigger the click again
        $("#start").prop("disabled", true);
    });
    $("#stop").click(() => {
        stop();
        // reactive the start button
        $("#start").prop("disabled", false);
    });
}); // on document ready end