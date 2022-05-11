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
        clearTipingTimers();
        logView.addTopLevelData("test", true);
        logView.sendData("/pentomino/save_log");
        
    });

    socket.on("warning", () => {
        $("#warning_prompt").addClass("active")
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
        set_description_panel(true, false);
        startTipingTimers();
    });

    socket.on("finish", (data) => {
        end_experiment(data["message"], data["message_color"])
    });

    socket.on("token_IG", (data) => {
        tokenIG = data;
    });

    // for debugging: log all events
    socket.onAny((eventName, ...args) => {
        console.log(eventName, args);
    });

    function end_experiment(message, text_color) {

        // we are done, show a message and the token
        $('#end_prompt').addClass("active");
        $("#end_prompt_message").addClass(text_color).text(message)
        if (tokenIG !== null) {
            $("#end_prompt_token_box").show()
            $('#end_prompt_token').text(tokenIG);
        } else {
            $("#end_prompt_token_box").hide()
        }
        $("#content").hide();
        stop();
    }

    $("#test_timeout_start").click(() => {
        end_experiment(null, "Sorry, but you took too long to start the experiment. You can close the window now.", "red")
    })
    $("#test_timeout_write").click(() => {
        end_experiment("test_token", "Sorry, but you took too long to continue the experiment", "yellow")
    })
    $("#test_success").click(() => {
        end_experiment("test_token", "Thanks for your participation!", "green")
    })

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
        clearTipingTimers();
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
            clearTipingTimers();
            socket.emit("descrimage_description", {"description": description, "token": token, "state": state_index});
            set_description_panel(false, true)
        }
    }

    // Tiping Timer
    //  - 30 sec: a simple warning
    //  - 60 sec: timeout; user will be disconnected 
    var typingTimer1;
    var typingTimer2;
    var alertTimer = 30 * 1000;
    var disconnectTimer = 60 * 1000;
    var $description = $('#description');

    document.getElementById("score").value = 0;
    $(document).ready(function () {
        set_description_panel(false, false)

        // start timeout
        let timeoutInMilliseconds = 100000
        let start_timeout = setTimeout(function () {
            on_start_timeout()
        }, timeoutInMilliseconds);

        // start countdown
        let remainingTimeInSeconds = ~~(timeoutInMilliseconds / 1000);
        $("#welcome_countdown").text(remainingTimeInSeconds)
        let start_countdown = setInterval(function () {
            if (remainingTimeInSeconds > 0) {
                remainingTimeInSeconds = remainingTimeInSeconds - 1
                $("#welcome_countdown").text(remainingTimeInSeconds)
            }
        }, 1000)

        $("#start_popupOK").click(function () {
            set_description_panel(true, false)
            $("#welcome_prompt").removeClass("active")
            clearTimeout(start_timeout);
            clearInterval(start_countdown)
            start(token);
            socket.emit("test_person_connected", token);
            startTipingTimers()
        });
    });

    window.onoffline = event => {
        end_experiment("PLACEHOLDER", "Your connection is unstable", "orange")
        stop()
    }

    $description.on('keyup', function () {
        clearTipingTimers();
        startTipingTimers();
    });

    //on keydown, clear the countdowns
    $description.on('keydown', function () {
        clearTipingTimers();
    });


    function clearTipingTimers() {
        clearTimeout(typingTimer1);
        clearTimeout(typingTimer2);
    }

    function startTipingTimers() {
        typingTimer1 = setTimeout(simpleAlert, alertTimer);
        typingTimer2 = setTimeout(timeOut, disconnectTimer);
    }

    // functions on timeouts
    function simpleAlert() {
        // alternative to alert where user does not press play
        audio_notification();
        $('body').toast({
            class: 'error',
            displayTime: 0,
            message: "Please type and send your description (click to dismiss)"
        });
    }

    function on_start_timeout() {
        $("#welcome_prompt").removeClass("active")
        socket.emit("timeout", {"token": token, "state": 0});
        end_experiment(null, "Sorry, but you took too long to start the experiment. You can close the window now.", "red")
    }

    function timeOut() {
        let state_index = $("#progress").progress("get value");
        socket.emit("timeout", {"token": token, "state": state_index})
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
    $("#help_button").click(() => {
        $("#help_prompt").addClass("active");

        // halt timers
        clearTipingTimers();
        typingTimer2 = setTimeout(timeOut, 5 * 60 * 1000);
    });
    $("#close_helpOK").click(() => {
        $("#help_prompt").removeClass("active");

        // restart timers
        clearTimeout(typingTimer2);
        typingTimer1 = setTimeout(simpleAlert, alertTimer);
        typingTimer2 = setTimeout(timeOut, disconnectTimer);

    });
    $("#close_warnOK").click(() => {
        $("#warning_prompt").removeClass("active");
    });

    $("#description_text_panel").hide()
    $("#description_text_warning").hide()
    $("#positive_feedback").hide()
    $("#negative_feedback").hide()
}); // on document ready end