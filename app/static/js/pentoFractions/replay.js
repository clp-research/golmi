$(document).ready(function () {
	// --- define globals --- // 

	// Set to false to skip unit tests
	const SELFTEST = true;

	const MODEL = "127.0.0.1:5000";

	// --- create a socket --- //
	// don't connect yet
	var socket = io("http://" + MODEL, { autoConnect: false, auth: "GiveMeTheBigBluePasswordOnTheLeft" });
	// debug: print any messages to the console
	localStorage.debug = 'socket.io-client:socket';

	// --- view --- // 
	// Get references to the three canvas layers
	let bgLayer		= document.getElementById("background");
	let objLayer	= document.getElementById("objects");
	let grLayer		= document.getElementById("gripper");

	// Set up the view js, this also sets up key listeners
	const layerView = new document.LayerView(socket, bgLayer, objLayer, grLayer);

	// Create a replayer
	const replayer = new document.Replayer();
	// TODO: where to load logs from? -> Golmi server? -> from files ? (cross-origin ...)
	// Temporarily use hard-coded log
	replayer.log = document.TESTLOG;

	// Get start time. For now number field, should be some kind of scale
	function getStartTime() {
		return $("#starttime").val();
	}

	// --- stop and start replaying --- //
	function start() {
		replayer.startTime = getStartTime();
		replayer.start();
	}

	function stop() {
		replayer.stop();
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

	// --- unit tests --- //
	if (SELFTEST) {
		console.log("Unit tests passed");
	}
}); // on document ready end