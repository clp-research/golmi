$(document).ready(function () {
    // --- define globals --- // 

    // Set to false to skip unit tests
    const SELFTEST = true;

    const MODEL = window.location.origin // expect same as backend e.g. the default "127.0.0.1:5000";
    console.log("Connect to " + MODEL)

    // --- create a socket --- //
    // don't connect yet
    var socket = io(MODEL, { autoConnect: false, auth: {
        "password": "GiveMeTheBigBluePasswordOnTheLeft"
    }});
    // debug: print any messages to the console
    localStorage.debug = 'socket.io-client:socket';

    // --- view --- // 
    // Get references to the three canvas layers
    let bgLayer     = document.getElementById("background");
    let objLayer    = document.getElementById("objects");
    let grLayer     = document.getElementById("gripper");

    // Set up the view js, this also sets up key listeners
    const layerView = new document.LocalLayerView(bgLayer, objLayer, grLayer);

    // Create a replayer with 20 fps
    const replayer = new document.Replayer(20);
    
    // load a log from the server, 
    // disable the start button until the log is loaded
    
    loadLog(document.TESTLOG);

    // --- stop and start replaying --- //
    function start() {
        replayer.start();
    }

    function stop() {
        replayer.stop();
    }

    function loadLog(log) {
        replayer.log = log;
        // see https://api.jqueryui.com/slider/ for slider widget documentation
        $( "#slider-range" ).slider({
                range: true,
                min: 0,
                max: replayer.endTime / 1000,  // convert ms to seconds
                values: [ 0, replayer.endTime ],
                step: 0.1,
                slide: function(event, ui) {
                    $( "#replayTimeRange" ).val(
                        prettyTime($("#slider-range").slider("values", 0)) + " - " + 
                        prettyTime($("#slider-range").slider("values", 1)) 
                    );
                },
                stop: function(event, ui) {
                    replayer.startTime = ui.values[0]*1000;
                    replayer.endTime = ui.values[1]*1000;
                }
            });
        $("#replayTimeRange").val(
            prettyTime($("#slider-range").slider("values", 0)) + " - " + 
            prettyTime($("#slider-range").slider("values", 1)));
    }

    /**
     * Create a nicely readable string from a number of seconds.
     */
    function prettyTime(seconds) {
        return `${Math.floor(seconds/60)}:` +  // minutes followed by ":"
            `${(seconds%60)<10?"0":""}` +  // insert 0 if seconds have only one digit
            `${(seconds%60).toFixed(1)}`;  // seconds and one point milliseconds 
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
    $("#reset").click(() => {
        stop();
        // reactive the start button
        $("#start").prop("disabled", false);
        // return to the start of the replay
        console.log($("#slider-range").slider("values", 0));
        replayer.startTime = $("#slider-range").slider("values", 0);
    });

    // --- unit tests --- //
    if (SELFTEST) {
        console.log("Unit tests passed");
    }
}); // on document ready end