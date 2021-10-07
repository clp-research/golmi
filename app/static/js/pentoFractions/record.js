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

	// --- controller --- //
	// create a controller, we still need to attach a gripper in the model to it
	let controller = new document.LocalTalkativeKeyController();

	// --- view --- // 
	// Get references to the three canvas layers
	let bgLayer		= document.getElementById("background");
	let objLayer	= document.getElementById("objects");
	let grLayer		= document.getElementById("gripper");

	// Set up the view js, this also sets up key listeners
	const layerView = new document.LayerView(socket, bgLayer, objLayer, grLayer);

	// --- logger --- //
	const logView = new document.LogView(socket, false);

	// --- task generator --- //

	const N_OBJECTS = 20;
	const N_GRIPPERS = 0;
	const taskGenerator = new document.PentoGenerator(socket);
			

	// --- socket communication --- //
	var setup_complete = false;

	socket.on("connect", () => {
		console.log("Connected to model server");
	});

	//TODO: wait until manual config is complete
	socket.on("update_config", (config) => {
		// only do setup once when config is sent for the first time
		if (!setup_complete) {
			// generate and send a random state
			taskGenerator.initRandomState(N_OBJECTS, N_GRIPPERS, config)
			.then(() => {
				// subscribe the controller to some gripper (here we create a new gripper)
				controller.attachModel(socket, "0");
			});
			setup_complete = true;
		}
	});

	// --- stop and start drawing --- //
	function start() {
		logView.clearLog();
		// reset the controller in case any key is currently pressed
		controller.resetKeys()
		// manually establish a connection, connect the controller and load a state
		socket.connect();
	}

	function stop() {
		// reset the controller in case any key is currently pressed
		controller.resetKeys();
		logView.sendData();
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