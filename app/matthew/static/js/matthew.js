/**
 * File: matthew.js
 * Main file to the experiment interface. Builds a connection to
 * the <Model>, sets up a <LocalKeyController> and the view components
 * (one instance each of <LayerView>, <IGView> and <LView>),
 * retrieves tasks from the respective GOLMI endpoint.
 * Presents introductory and questionnaire dialogs to the user
 * and starts the tasks.
 */

$(document).ready(function () {
	// if true, some unit tests will be performed
	const SELFTEST = false;

	// --- set up the APIs --- //
	// Variable: MODEL
	// protocol, domain and port of the server
	const MODEL	= window.location.protocol + "//" +document.domain + ':' + location.port;

	// --- create a socket --- //
	// don't connect yet
	let socket = io(MODEL, {
		autoConnect: false,
		auth: {"password": "GiveMeTheBigBluePasswordOnTheLeft"}
	});
	// debug: print any messages to the console
	localStorage.debug = 'socket.io-client:socket';

	// --- controller --- //
	// create a controller, we still need to attach a gripper
	//  in the server to it
	let controller = new document.LocalKeyController();
	// the controller will be attached to gripper "0" later
	let gripperId = "0";
	
	// --- view --- //
	// Get references to the three canvas layers
	let bgLayer		= document.getElementById("background");
	let objLayer	= document.getElementById("objects");
	let grLayer		= document.getElementById("gripper");
	// resize the canvas and their container to the window
	_resizeCanvas();
	// initialize the GUI component
	const layerView = new document.LayerView(socket, bgLayer, objLayer, grLayer);

	// --- logger --- //
	const logFullState = false; // only log updated data at each change
	const logView = new document.LogView(socket, logFullState);

	// --- socket communication --- //
	let setup_complete = false;
	// this event listener starts the experiment by loading
	// the configuration, attaching the server to the controller
	// and starting the instruction giving view
	socket.on("connect", () => {
		console.log("Connected to server server");
		// only do setup once (reconnections can occur, we don't want to reset the state every time)
		if (!setup_complete) {
			// start giving instructions and feedback
			instructionGiver.start();
			// subscribe the controller to some gripper (here we create a new gripper)
			controller.attachModel(socket, "0");
			setup_complete = true;
		}
	});
	socket.on("disconnect", () => {
		console.log("Disconnected from server server");
	});
	
	// --- tasks and instruction giving view --- //
	// randomly select one of the algorithms
	const algorithms = ["IA", "RDT", "SE"];
	const randomAlg = document.randomFromArray(algorithms);
	// log what algorithm has been used
	logView.addData("algorithm", randomAlg);
	const feedbackTimeInt = 10000;
	const feedbackDistInt = 3;
	let instructionGiver;
	let tasks;
	// load json file with tasks
	const task_route = "/matthew/get_tasks/ba_tasks";
	fetch(new Request(task_route, {method:"GET"}))
	.then(response => {
		if (!response.ok) {
			console.log("Error loading tasks!");
			error.showModal(); // show error screen to the user
		} else {
			response.json()
			.then(json => {
				tasks = JSON.parse(json);
				// Set up the instruction giver once the tasks are loaded
				instructionGiver = new document.IGView(
					socket, tasks, randomAlg, gripperId, feedbackTimeInt, feedbackDistInt);
			});
		}
	});

	// --- stop and start drawing --- //
	
	/**
	 * Func: start
	 * Establish a connection to the <Model>. A client-side
	 * listener to the 'connect' event will start the tasks
	 * at success.
	 */
	function start() {
		// reset the controller in case any key is currently pressed
		controller.resetKeys()
		// manually establish a connection, connect the controller and load a state
		socket.connect();
	}

	/**
	 * Func: stop
	 * Disconnect the <LocalKeyController> from the <Model> to delete the
	 * assigned <Gripper>, then cut the socket connection.
	 */
	function stop() {
		// reset the controller in case any key is currently pressed
		controller.resetKeys();
		// disconnect the controller
		controller.detachModel(socket, "0");
		// manually disconnect
		socket.disconnect();
	}

	// --- buttons --- //
	$("#close_welcome").click(() => {
		welcome.close();
		audiotest.showModal();
		// start the looped test audio
		startAudiotest();
	});

	$("#close_audiotest").click(() => {
		stopAudiotest();
		// save the user's audio transcript
		logView.addData("audiotest", encodeURIComponent($("#transcript").val()));
		audiotest.close();
		start();
	});

	$("#close_questionnaire").click(() => {
		// get all the form data and send it to the logView
		let freeformData = ["age", "gender", "education", "language", "comments"];
		let checkboxData = ["pentoVeteran"];
		let scaleData = ["fluency", "anthropomorphism1", "anthropomorphism2", "anthropomorphism3",
			"likeability1", "likeability2", "likeability3", "intelligence1", "intelligence2", "intelligence3"];
		freeformData.forEach(dataId => {
			logView.addData(dataId, encodeURIComponent($("#"+dataId).val()));
		});
		checkboxData.forEach(dataId => {
			logView.addData(dataId, $("#"+dataId).is(":checked"));
		});
		scaleData.forEach(dataId => {
			logView.addData(dataId, $("#"+dataId).val());
		});
		// save all collected data to the server
		logView.sendData();
		// show a 'thank you' dialog to the participant
		questionnaire.close();
		goodbye.showModal();
	});

	// --- event handling --- //
	window.onresize = function(event) {
		_resizeCanvas();
		layerView.redraw();
	};
	
	// one tasks complete (dispatched by IGView)
	$(document).on("logSegment", e => {
		if (instructionGiver.currentTask >= 0) {
			// show progress to user. first task is not counted because
			// it is a training example here
			updateProgressBar(Math.floor(
				100 * ((instructionGiver.currentTask+1) / (Object.keys(tasks).length-1))
			));
		}
	});

	// all tasks completed (dispatched by IGView)
	$(document).on("tasksCompleted", e => {
		stop();
		// update the progress bar to show 100 %
		updateProgressBar(100);
		// open the goodbye dialog
		if (!questionnaire.open || !goodbye.open) {
			questionnaire.showModal();
		// should not happen
		} else {
			console.log("Error: Attempted to open 'questionnaire' dialog, but dialog was already open.");
		}
	});

	// --- dialogs --- // 
	let welcome			= document.getElementById("welcome");
	let audiotest		= document.getElementById("audiotest");
	let goodbye			= document.getElementById("goodbye");
	let error			= document.getElementById("error");
	let questionnaire	= document.getElementById("questionnaire");

	// polyfill is used to help with browsers without native support for 'dialog'
	dialogPolyfill.registerDialog(welcome);
	dialogPolyfill.registerDialog(audiotest);
	dialogPolyfill.registerDialog(goodbye);
	dialogPolyfill.registerDialog(error);
	dialogPolyfill.registerDialog(questionnaire);
	
	// --- helper functions --- //
	
	var testSample;
	/**
	 * Func: startAudiotest
	 * Start playing an audiosample in a loop similarly to how
	 * the IGView will play instructions later.
	 */
	function startAudiotest() {
		testSample = new Audio("./static/resources/audio/audiotest.mp3");
		testSample.loop = true;
		testSample.play();
	}
	
	/**
	 * Func: stopAudiotest
	 * Stop the looped test audio.
	 */
	function stopAudiotest() {
		if (testSample) {
			testSample.pause();
		}
	}
	
	/**
	 * Func: updateProgressBar
	 * Update the displayed progress bar.
	 *
	 * Params:
	 * completion - Completion in percent (_int_)
	 */
	function updateProgressBar(completion) {
		// update width
		$('#progress_bar').css('width', `${completion}%`);
		// update number
		$('#progress_bar').html(`${completion}%`);
	}
	
	/**
	 * Adapt the three canvas elements to the current window sizes.
	 */
	function _resizeCanvas() {
		let newSize = 0.8 * window.innerHeight;
		for (let element of [bgLayer, objLayer, grLayer]) {
			element.width = newSize;
			element.height = newSize;
		}
		$("#viewport").css({"width": newSize, "height": newSize});
	};

	// --- start --- //
	// open the welcome dialog
	welcome.showModal();

}); // on document ready end
