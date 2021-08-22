$(document).ready(function () {
	// create an anonymous user id:
	let USER_DATA = new Object(); 
	const ONSERVER = true;
	// if true, some unit tests will be performed
	const SELFTEST = false;

	// --- set up the APIs --- //
	// Define the API URLs
	const MODEL			= "127.0.0.1:5000";

	const CONFIG = document.CONFIG;
	// TODO: POST config here
	
	// --- create a socket --- //
	// don't connect yet
	var socket = io("http://" + MODEL, { autoConnect: false, auth: "GiveMeTheBigBluePasswordOnTheLeft" });
	// debug: print any messages to the console
	localStorage.debug = 'socket.io-client:socket';

	// --- controller --- //
	// create a controller, we still need to attach a gripper in the model to it
	let controller = new document.LocalKeyController();
	// the controller will be attached to gripper "0" later
	let gripperId = "0";
	
	// --- view --- //
	// Get references to the three canvas layers
	let bgLayer		= document.getElementById("background");
	let objLayer	= document.getElementById("objects");
	let grLayer		= document.getElementById("gripper");

	// Set up the view js
	this.layerView = new document.LayerView(socket, bgLayer, objLayer, grLayer);

	// --- socket communication --- //
	let setup_complete = false;
	socket.on("connect", () => {
		console.log("Connected to model server");
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
		console.log("Disconnected from model server");
	});
	socket.onAny((eventName, ...args) => {
		console.log(eventName, args);
	});
	
	// --- tasks and instruction giving view --- //
	
	const N_TASKS = 5;
	const N_OBJECTS = 15;
	const N_GRIPPERS = 1;

	let instructionGiver;
	let tasks;
	// generate tasks randomly
	/*let taskGenerator = new document.PentoGenerator(MODEL);
	tasks = new Object();
	for (let i=0; i<N_TASKS; i++) {
		// generate a random task
		taskGenerator.generateState(N_OBJECTS, N_GRIPPERS)
		.then(task => {
			tasks[i] = {"task": task};
			// randomly select one object as the target
			tasks[i]["target"] = Math.floor(Math.random() * (N_OBJECTS)).toString();
			});
	}
	*/
	// need to be on a server because of same origin policy
	if (ONSERVER) {
		// load json file with tasks
		const task_route = "/ba_tasks";
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
					instructionGiver = new document.IGView(socket, tasks, "SE", gripperId);
				});
			}
		});
	} else {
		tasks = document.TASKS;
		// Set up the instruction giver once the tasks are loaded
		instructionGiver = new document.IGView(socket, tasks, "SE", gripperId);			
	}

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

	$("#close_welcome").click(() => {
		welcome.close();
		audiotest.showModal();
	});

	$("#close_audiotest").click(() => {
		// save the user's audio transcript
		USER_DATA["audiotest"] = encodeURIComponent($("#transcript").val());
		audiotest.close();
		start();
	});

	$("#close_questionnaire").click(() => {
		// get all the form data:
		let freeformData = ["age", "gender", "education", "language", "comments"];
		let scaleData = ["fluency", "anthropomorphism1", "anthropomorphism2", "anthropomorphism3",
			"likeability1", "likeability2", "likeability3", "intelligence1", "intelligence2", "intelligence3"];
		freeformData.forEach(dataId => {
			USER_DATA[dataId] = encodeURIComponent($("#"+dataId).val());
		})
		scaleData.forEach(dataId => {
			USER_DATA[dataId] = $("#"+dataId).val();
		})
		// TODO: save!
		console.log(USER_DATA)
		questionnaire.close();
		goodbye.showModal();
	})

	// --- event handling --- //

	// "tasksCompleted" is dispatched by the IGView
	document.addEventListener("tasksCompleted", e => {
		stop();
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

	// --- start --- //
	// open the welcome dialog
	//welcome.showModal();

	// --- unit tests --- //
	if (SELFTEST) {
		document.pentoGeneratorTest();
	}
}); // on document ready end
