$(document).ready(function () {
    // --- define globals --- //

    // expect same as backend e.g. the default "http://127.0.0.1:5000";
    const MODEL = window.location.origin
    console.log("Connect to " + MODEL)

    // parameters for random initial state
    // (state is generated once the configuration is received)
    const N_OBJECTS = 10;
    const N_GRIPPERS = 0; // no pre-generated gripper

    const CUSTOM_CONFIG = {
        "move_step": 0.5,
        "width": 25,
        "height": 25
    };

    // --- create a socket --- //
    // don't connect yet
    let socket = io(MODEL, {
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
    // second parameter disables full state logging, significantly reducing
    // log sizes while still keeping track of all changes.
    const logView = new document.LogView(socket, false);

    // --- socket communication --- //
    socket.on("connect", () => {
        console.log("Connected to model server");
    });

    socket.on("joined_room", (data) => {
        socket.emit("load_config", CUSTOM_CONFIG);
        console.log(`Joined room ${data.room_id} as client ${data.client_id}`);
    })

    socket.on("disconnect", () => {
        console.log("Disconnected from model server");
        // demo of the logView: send the logged data to the server
        logView.addTopLevelData("test", true);
        logView.sendData("/pentomino/save_log");
    });

    socket.on("descrimage_bad_description", (data) => {
        console.log(data)
        // CREATE POPUP
        alert("Your description is bad and you should feel bad");
        old_score = parseInt(document.getElementById("score").value);
        document.getElementById("score").value = old_score - 1;
    });

    socket.on("next_state", (state) => {
        document.getElementById("progress").value = state;
        old_score = parseInt(document.getElementById("score").value);
        document.getElementById("score").value = old_score + 1;
    });
    
    socket.on("finish", () => {
        alert("We are done here, you can close the window");
        stop();
    });

    // for debugging: log all events
    socket.onAny((eventName, ...args) => {
        console.log(eventName, args);
    });

    function custom_config_is_applied(custom_config, config_update) {
        return Object.keys(custom_config).every(key => {
            return config_update[key] == custom_config[key];
        });
    }

    // --- stop and start drawing --- //
    function start(token) {
        // reset the controller in case any key is currently pressed
        controller.resetKeys()
        controller.attachModel(socket);
        // join a GOLMI room with the name "test_room_id"
        socket.emit("join", {"room_id": token});
    }

    function stop() {
        // reset the controller in case any key is currently pressed
        controller.resetKeys();
        // disconnect the controller
        controller.detachModel(socket);
        // manually disconnect
        socket.disconnect();
    }

    function send_description() {
        // join a GOLMI room with the name "test_room_id"
        let description = document.getElementById("description").value;
        let state_index = document.getElementById("progress").value;
        socket.emit("descrimage_description", {"description":description, "token": token, "state": state_index});
        document.getElementById("description").value = "";
    }

    document.getElementById("score").value = 0;
    $(document).ready(function(){   
        setTimeout(function () {
            $("#start_popup").fadeIn(700);
         }, 1000);
        $(".start_popupOK").click(function() {
            $("#start_popup").fadeOut(700);
            start(token);
            socket.emit("test_person_connected");
        }); 
    }); 
    
    // --- buttons --- //
    $("#start").click(() => {
        start(token);
        socket.emit("test_person_connected")
        // disable this button, otherwise it is now in focus and Space/Enter will trigger the click again
        $("#start").prop("disabled", true);
    });
    $("#description_button").click(() => {
        send_description();
    });
}); // on document ready end