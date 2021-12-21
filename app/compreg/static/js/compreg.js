$(document).ready(function () {
    // --- define globals --- //

    // expect same as backend e.g. the default "http://127.0.0.1:5000";
    const MODEL = window.location.origin
    console.log("Connect to " + MODEL)

    // --- create a socket --- //
    // don't connect yet
    let socket = io(MODEL, {
        autoConnect: false,
        auth: {"password": "GiveMeTheBigBluePasswordOnTheLeft"}
    });
    // debug: print any messages to the console
    localStorage.debug = 'socket.io-client:socket';

    // --- view --- //
    let bgLayer = document.getElementById("background");
    let objLayer = document.getElementById("objects");

    // Set up the view js, this also sets up key listeners
    const layerView = new document.PentoBoardView(socket, bgLayer, objLayer);
    const control_state = {
        "property_name": "color"
    }

    $("#select_color").click(() => {
        control_state.property_name = "color"
    })
    $("#select_shape").click(() => {
        control_state.property_name = "shape"
    })
    $("#select_position").click(() => {
        control_state.property_name = "rel_position"
    })

    objLayer.onclick = function onBoardClick(event) {
        socket.emit("mouseclick", {
            "target_id": event.target.id,
            "offset_x": event.offsetX,
            "offset_y": event.offsetY,
            "x": event.x,
            "y": event.y,
            "block_size": layerView.blockSize
        })
    }

    function request_new_scene() {
        console.log("new scene with " + control_state)
        socket.emit("new_comp_scene", {"controls": control_state});
    }

    var setup_complete = false;
    socket.on("update_config", (config) => {
        if (!setup_complete) {
            request_new_scene()
            setup_complete = true;
        }
    });

    $("#start").click(() => {
        socket.connect();
        // disable this button, otherwise it is now in focus and Space/Enter will trigger the click again
        $("#start").prop("disabled", true);
    });
    $("#restart").click(() => {
        request_new_scene()
    });
    $("#stop").click(() => {
        socket.disconnect();
        // reactive the start button
        $("#start").prop("disabled", false);
    });


    socket.on("connect", () => {
        console.log("Connected to model server");
    });

    socket.on("disconnect", () => {
        console.log("Disconnected from model server");
    });

    socket.onAny((eventName, ...args) => {
        console.log(eventName, args);
    });

}); // on document ready end