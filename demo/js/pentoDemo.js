$(document).ready(function () {

	// Define the API URLs

	const MODEL_API			= "127.0.0.1:5000";
	const CONTROLLER_API	= "127.0.0.1:5001";
	const VIEW_API			= "127.0.0.1:5002";

	const TESTGAME = {
		"grippers": {
			"1": {
				"x": 5,
				"y": 5,
				"gripped": "2"
			}
		},
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
				"rotation": 90
			}
		} 
	};

	// Set up the MVC APIs
	// Connect View and Model API (so model can notify the view)
	let subscribeViewToModel = new Request(`http://${MODEL_API}/attach-view`, {method:"POST", body:`{"url": "${VIEW_API}"}`});
	fetch(subscribeViewToModel)
	.then(r => {
		if (!r.ok) {
			console.log("Error connecting view and model API. Printing response...", r);
		}
	});

	// Load a game
	let loadGameReq = new Request(`http://${MODEL_API}/state`, {method:"POST", body:JSON.stringify(TESTGAME)});
	fetch(loadGameReq)
	.then(r => {
		if (!r.ok) {
			console.log("Error loading a game state. Printing response...", r);
		}
	});

	// Connect Controller to Model API (so controller can post to the model)
	// Attach the controller to gripper "1"
	let subscribeModelToController = new Request(`http://${CONTROLLER_API}/attach-model`, {method:"POST", body:`{"url": "${MODEL_API}", "gripper": "1"}`});
	fetch(subscribeModelToController)
	.then(r => {
		if (!r.ok) {
			console.log("Error connecting view and model API. Printing response...", r);
		}
	});


	// Get references to the three canvas layers
	let bgLayer		= document.getElementById("background");
	let objLayer	= document.getElementById("objects");
	let grLayer		= document.getElementById("gripper");

	// Set up the view js, this also sets up key listeners
	this.layerView = new document.LayerView(VIEW_API, MODEL_API, CONTROLLER_API, bgLayer, objLayer, grLayer);

	// Set up buttons
	$("#start").click(() => {
		document.layerView.startDrawing();
		// disable this button, otherwise it is now in focus and Space/Enter will trigger the click again
		$("#start").prop("disabled", true);
	});
	$("#stop").click(() => {
		document.layerView.stopDrawing();
		// reactive the start button
		$("#start").prop("disabled", false);
	});
	
}); // on document ready end