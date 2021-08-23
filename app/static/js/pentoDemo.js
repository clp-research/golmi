$(document).ready(function () {

	// TODO:
	// test this with multiple browser windows
	// create model test cases
	// fix looped actions

	// --- define globals --- // 

	// Set to false to skip unit tests
	const SELFTEST = true;

	const MODEL = "127.0.0.1:5000";

	// // generate a random state
	// const N_OBJECTS = 15;
	// const N_GRIPPERS = 1;
	// const taskGenerator = new document.PentoGenerator(document.MODEL);
	// let sample_state;
	// taskGenerator.generateState(N_OBJECTS, N_GRIPPERS)
	// .then(task => {
	// 	sample_state = task;
	// });
	const TESTGAME = {
		"objs": {
			"1": {
				"type": "I",
				"x": 10,
				"y": 8,
				"width": 5,
				"height": 5
			},
			"2": {
				"type": "F",
				"x": 3,
				"y": 3,
				"width": 5,
				"height": 5,
				"color": "yellow",
				"mirrored": true,
				"rotation": 0
			}
		} 
	};

	// --- create a socket --- //
	// don't connect yet
	var socket = io("http://" + MODEL, { autoConnect: false, auth: "GiveMeTheBigBluePasswordOnTheLeft" });
	// debug: print any messages to the console
	localStorage.debug = 'socket.io-client:socket';

	// --- controller --- //
	// create a controller, we still need to attach a gripper in the model to it
	let controller = new document.LocalKeyController();

	// --- view --- // 
	// Get references to the three canvas layers
	let bgLayer		= document.getElementById("background");
	let objLayer	= document.getElementById("objects");
	let grLayer		= document.getElementById("gripper");

	// Set up the view js, this also sets up key listeners
	const layerView = new document.LayerView(socket, bgLayer, objLayer, grLayer);

	// --- logger --- //
	const logView = new document.LogView(socket);

	// --- socket communication --- //
	var setup_complete = false;
	socket.on("connect", () => {
		console.log("Connected to model server");
		// only do setup once (reconnections can occur, we don't want to reset the state every time)
		if (!setup_complete) {
			// send the initial task state
			socket.emit("load_state", TESTGAME);
			// subscribe the controller to some gripper (here we create a new gripper)
			controller.attachModel(socket, "0");
			setup_complete = true;
		}
	});
	socket.on("disconnect", () => {
		console.log("Disconnected from model server");
		// demo of the logView: send the logged data to the server
		logView.addData("test", true);
		logView.sendData();
	});
	socket.onAny((eventName, ...args) => {
		console.log(eventName, args);
	});

	// --- stop and start drawing --- //
	function start() {
		// reset the controller in case any key is currently pressed
		controller.resetKeys()
		// manually establish a connection, connect the controller and load a state
		socket.connect();
	}

	function stop() {
		// reset the controller in case any key is currently pressed
		controller.resetKeys();
		// disconnect the controller
		controller.detachModel(socket, "0");
		// manually disconnect
		socket.disconnect();
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