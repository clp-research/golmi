$(document).ready(function () {
    // --- define globals --- //

    // expect same as backend e.g. the default "http://127.0.0.1:5000";
    const MODEL = window.location.origin
    console.log("Connect to " + MODEL)

    // --- create a socket --- //
    let socket = io(MODEL, {
        auth: { "password": "GiveMeTheBigBluePasswordOnTheLeft" }
    });

    // --- controller --- //
    // create a controller and wait until the model assigns a gripper
    let controller = new document.LocalKeyController();
    controller.awaitGripperFrom(socket);

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
        // This test room uses the default configuration and can only hold 2
        // players. It will be created by the first connecting client.
        socket.emit("join_game", {"room_id": "test_room", "role": "random"})
    });

    socket.on("joined_room", (data) => {
        console.log(`Joined room ${data.room_id} as client ${data.client_id}`);
    })

    socket.on("disconnect", () => {
        console.log("Disconnected from model server");
        // reset the controller in case any key is currently pressed
        controller.resetKeys();
        // disconnect the controller
        controller.detachFrom(socket);
        // demo of the logView: send the logged data to the server
        logView.addData("test", true);
        logView.sendData("/pentomino_game/save_log");
    });

    // for debugging: log all events
    socket.onAny((eventName, ...args) => {
        console.log(eventName, args);
    });
}); // on document ready end