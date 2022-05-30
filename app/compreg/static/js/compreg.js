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
    let default_target_values = {
        color: "BLUE",
        shape: "T",
        rel_position: "CENTER",
        unique_prop: "color"
    }
    const sceneConfig = {
        board: {
            width: 30,
            height: 30
        },
        target_piece: {
            color: default_target_values.color,
            shape: default_target_values.shape,
            rel_position: default_target_values.rel_position,
            unique_properties: [default_target_values.unique_prop],
        },
        distractors: {
            num_distractors: 4,
            pieces_per_pos: 2
        },
        varieties: {
            num_colors: 0, // all
            num_shapes: 0, // all
            num_positions: 0 // all
        }
    }
    const sceneControls = new document.SceneConfigControls(sceneConfig)
    $("#select_property").dropdown("set selected", default_target_values.unique_prop)
    $("#select_target_shape").dropdown("set selected", default_target_values.shape)
    $("#select_target_color").dropdown("set selected", default_target_values.color)
    $("#select_target_rel_position").dropdown("set selected", default_target_values.rel_position)

    const layerView = new document.PentoBoardView(socket, bgLayer, objLayer);

    objLayer.onclick = function onBoardClick(event) {
        socket.emit("compreg_mouseclick", {
            "target_id": event.target.id,
            "offset_x": event.offsetX,
            "offset_y": event.offsetY,
            "x": event.x,
            "y": event.y,
            "block_size": layerView.blockSize
        })
    }

    function request_new_scene() {
        console.log("new scene with " + sceneConfig)
        socket.emit("compreg_new_scene", {"scene_config": sceneConfig});
    }

    socket.on("update_instructions", (instr) => {
        $("#instructions").text(instr);
    })

    let setup_complete = false;
    socket.on("update_config", (config) => {
        if (!setup_complete) {
            request_new_scene()
            setup_complete = true;
        }
    });
    $("#toggle_show_grid").click(() => {
        console.log("toggle_show_grid")
        let el = $("#toggle_show_grid")
        if (el.hasClass("active")) {
            el.removeClass("active")
            el.text("Show Grid")
            layerView.redrawBg(false)
        } else {
            el.addClass("active")
            el.text("Hide Grid")
            layerView.redrawBg(true)
        }
    });

    $("#start").click(() => {
        socket.connect();
        socket.emit("join", {"room_id": "compreg_room"});
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