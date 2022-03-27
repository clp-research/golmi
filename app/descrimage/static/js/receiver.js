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
        // socket.emit("load_config", CUSTOM_CONFIG);
        console.log(`Joined room ${data.room_id} as client ${data.client_id}`);
    })

    socket.on("disconnect", () => {
        console.log("Disconnected from model server");
        // demo of the logView: send the logged data to the server
        logView.addTopLevelData("test", true);
        logView.sendData("/pentomino/save_log");
    });

    socket.on("description_from_server", (data) => {
        console.log(data)
        document.getElementById("description").value = data;
    });

    socket.on("incoming connection", () => {
        audio_notification();
    });

    // var setup_complete = false;
    // socket.on("update_config", (config) => {
    //     // only do setup once (reconnections can occur, we don't want to reset the state every time)
    //     if (!setup_complete && custom_config_is_applied(CUSTOM_CONFIG,
    //                                                     config)) {
    //         // ask model to load a random state
    //         socket.emit("random_init", {"n_objs": N_OBJECTS,
    //                                     "n_grippers": N_GRIPPERS,
    //                                     "random_gr_position":false,
    //                                     "obj_area": "top",
    //                                     "target_area": "bottom"});
    //         // manually add a gripper that will be assigned to the controller
    //         // TODO: Should this happen somewhere else?
    //         // Options:
    //         // - automatically get gripper when joining room / use join parameter
    //         //      -> but then why do we even need pre-generated grippers?
    //         // - manually add gripper once room is joined
    //         //      -> but then I need to know generated names? or same problem.
    //         // so maybe there are 2 approaches that make sense:
    //         // 1. random init on model side + automatically attach to some gripper that is generated on the fly
    //         // 2. pass state & attach manually to specific gripper
    //         socket.emit("add_gripper");
    //         setup_complete = true;
    //         document.getElementById("description").value = data
    //     }
    // });
    
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

    function bad_description() {
        socket.emit("descrimage_bad_description");
    }

    function load_file() {
        var myUploadedFile = document.getElementById("fileinput").files;
        socket.emit("load_file", myUploadedFile);
    }

    function audio_notification() {
        var snd = new Audio("static/notification.mp3");
        console.log("this workd")
        snd.play();
    }


    // listener for state selection
    var selectElem = document.getElementById('state_id')
    selectElem.addEventListener('change', function() {
        var index = selectElem.selectedIndex;
        // Add that data to the <p>
        socket.emit("load_state_index", index, token);
    })


    start(token);
    socket.emit("add_gripper")
    // --- buttons --- //
    $("#start").click(() => {
        start(token);
        // disable this button, otherwise it is now in focus and Space/Enter will trigger the click again
        $("#start").prop("disabled", true);
    });
    $("#stop").click(() => {
        stop();
        // reactive the start button
        $("#start").prop("disabled", false);
    });
    $("#bad_description").click(() => {
        bad_description();
    });
    $("#load_file").click(() => {
        load_file();
    });
}); // on document ready end