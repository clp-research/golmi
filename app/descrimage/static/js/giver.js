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

    socket.on("next_state", (data) => {
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
        set_description_panel(true, false)
    });

    socket.on("finish", (message) => {
        // we are done, show a message and the token
        $('#start_popup').html(message);
        $("#start_popup").fadeIn(50);
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

    function set_description_panel(activate, show_written_text) {
        let $description = $("#description");
        if (show_written_text) {
            $("#description_text_panel").show()
            $("#description_text").text($description.val())
        } else {
            // hide previous text
            $("#description_text_panel").hide()
        }
        if (activate) {
            // enable the inputs
            $("#description_button").removeClass("disabled")
            $("#description_button_panel").removeClass("disabled")
            $description.focus()
        } else {
            // show the text
            // reset and disable inputs
            $description.val("").blur() // blur to remove focus
            $("#description_button").addClass("disabled")
            $("#description_button_panel").addClass("disabled")
        }
    }

    function send_description() {
        // join a GOLMI room with the name "test_room_id"
        let description = document.getElementById("description").value;
        let state_index = $("#progress").progress("get value");
        if (description === "") {
            $("#description_text_warning").show()
        } else {
            $("#description_text_warning").hide()
            $("#positive_feedback").hide()
            $("#negative_feedback").hide()
            socket.emit("descrimage_description", {"description": description, "token": token, "state": state_index});
            set_description_panel(false, true)
        }
    }

    document.getElementById("score").value = 0;
    $(document).ready(function () {
        setTimeout(function () {
            $("#start_popup").fadeIn(50);
            set_description_panel(false, false)
        }, 200);

        // timeout at start needed?
        setTimeout(function () {
            $('#start_popup').html("Connection Lost");
            timeOut();
        }, 60000);

        $(".start_popupOK").click(function () {
            set_description_panel(true, false)
            $("#start_popup").fadeOut(700);
            start(token);
            socket.emit("test_person_connected", token);
        });
    });

    // Tiping Timer
    //  - 30 sec: a simple warning
    //  - 60 sec: timeout; user will be disconnected 
    var typingTimer1;
    var typingTimer2;
    var alertTimer = 30 * 1000;
    var disconnectTimer = 60 * 1000;
    var $description = $('#description');

    $description.on('keyup', function () {
        clearTimeout(typingTimer1);
        clearTimeout(typingTimer2);
        typingTimer1 = setTimeout(simpleAlert, alertTimer);
        typingTimer2 = setTimeout(timeOut, disconnectTimer);
    });

    //on keydown, clear the countdowns
    $description.on('keydown', function () {
        clearTimeout(typingTimer1);
        clearTimeout(typingTimer2);
    });

    // functions on timeouts
    function simpleAlert() {
        // alternative to alert where user does not press play
        audio_notification();
        $('body').toast({
            class: 'error',
            displayTime: 0,
            message: "You're taking too long, move on (click to dismiss)"
        });
    }

    function timeOut() {
        socket.emit("timeout", token)
        stop();
        alert("You've been disconnected, you can close the window");
    }

    function audio_notification() {
        // console.log(descrimage_bp.static)
        var snd = new Audio(notification_file);
        snd.play();
    }

    $("#description_button").click(() => {
        send_description();
    }).prop("disabled", true);

    $("#description").keypress(function (e) {
        let code = (e.keyCode ? e.keyCode : e.which);
        if (code === 13) { // press ENTER
            send_description();
        }
    });

    $("#description_text_panel").hide()
    $("#description_text_warning").hide()
    $("#positive_feedback").hide()
    $("#negative_feedback").hide()
}); // on document ready end