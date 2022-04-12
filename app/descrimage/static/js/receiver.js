$(document).ready(function () {
    // --- define globals --- //

    // expect same as backend e.g. the default "http://127.0.0.1:5000";
    const MODEL = window.location.origin
    console.log("Connect to " + MODEL)

    // --- create a socket --- //
    // don't connect yet
    let socket = io(MODEL, {
        auth: {"password": "GiveMeTheBigBluePasswordOnTheLeft"}
    });
    // debug: print any messages to the console
    localStorage.debug = 'socket.io-client:socket';

    // --- controller --- //
    // create a controller, we still need to attach a gripper in the model to it
    let controller = new document.LocalKeyController();

    // --- view --- //
    // Get references to the three canvas layers
    let bgLayer = document.getElementById("background");
    let objLayer = document.getElementById("objects");
    let grLayer = document.getElementById("gripper");

    // Set up the view js, this also sets up key listeners
    const layerView = new document.LayerView(socket, bgLayer, objLayer, grLayer);

    function onMouseClick(event) {
        let $progress = $("#progress");
        let current = $progress.progress("get value")
        let total = $progress.progress("get total")
        socket.emit("descrimage_mouseclick", {
            "target_id": event.target.id,
            "offset_x": event.offsetX,
            "offset_y": event.offsetY,
            "x": event.x,
            "y": event.y,
            "block_size": layerView.blockSize,
            "token": token,
            "this_state": current,
            "n_states": total
        })
    }

    grLayer.onclick = onMouseClick
    // --- logger --- //
    // second parameter disables full state logging, significantly reducing
    // log sizes while still keeping track of all changes.
    const logView = new document.LogView(socket, false);

    // --- socket communication --- //
    socket.on("connect", () => {
        console.log("Connected to model server");
    });

    socket.on("joined_room", (data) => {
        console.log(`Joined room ${data.room_id} as client ${data.client_id}`);
    })

    socket.on("timeout", () => {
        alert("Your partner disconnected. The experiment is over")
        stop();
    })

    socket.on("disconnect", () => {
        console.log("Disconnected from model server");
        // demo of the logView: send the logged data to the server
        logView.addTopLevelData("test", true);
        logView.sendData("/pentomino/save_log");
    });

    function on_description(data) {
        console.log(data)
        $("#description_text").text(data);
        $("#awaiting_text_panel").hide()
        $("#blocking_board_panel").hide()
        $("#positive_feedback").hide()
        $("#negative_feedback").hide()
        $('body').toast({
            class: 'info',
            message: `A new instruction arrived!`
        });
    }

    socket.on("description_from_server", on_description);

    socket.on("incoming connection", () => {
        audio_notification();
        $('body').toast({
            class: 'success',
            message: "A user connected to this room"
        });
    });

    socket.on("next_state", (data) => {
        $('body').toast({
            class: 'warning',
            message: "Next state has been loaded"
        });
        $("#awaiting_text_panel").show()
        $("#blocking_board_panel").show()
        // todo show "success" progress, when final state
        $('#progress').progress('increment', 1)
        // todo score should come from the server
        let score_received = data.score_delta
        if (score_received < 1) {
            $("#negative_feedback").show()
        } else {
            $("#positive_feedback").show()
        }
        // increase the score
        let $score = $("#score");
        let old_score = parseInt($score.text());
        $score.text(old_score + score_received);
    });

    socket.on("finish", (dada) => {
        alert("We are done here, you can close the window");
        stop();
    });

    // for debugging: log all events
    socket.onAny((eventName, ...args) => {
        console.log(eventName, args);
    });

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
        let description = document.getElementById("description").value;
        let state_index = $("#progress").progress("get value");
        document.getElementById("description").value = ""
        old_score = parseInt(document.getElementById("score").value);
        document.getElementById("score").value = old_score - 1;

        socket.emit("descrimage_bad_description", {"description": description, "token": token, "state": state_index});
    }

    function audio_notification() {
        // console.log(descrimage_bp.static)
        var snd = new Audio(notification_file);
        snd.play();
    }

    start(token);
    document.getElementById("score").value = 0;

    // --- buttons --- //
    $("#bad_description").click(() => {
        bad_description();
    });
    $("#test_description").click(() => {
        on_description("Dummy text");
    });
    $("#load_file").click(() => {
        load_file();
    });
    $("#positive_feedback").hide()
    $("#negative_feedback").hide()
}); // on document ready end