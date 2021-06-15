$(document).ready(function () {

	// Define the API URLs

	const MODEL_API			= "127.0.0.1:5000";
	const CONTROLLER_API	= "127.0.0.1:5001";
	const VIEW_API			= "127.0.0.1:5002";

	// Set up the MVC APIs
	// Connect View and Model API (so model can notify the view)
	let subscribeViewToModel = new Request(`http://${MODEL_API}/attach-view`, {method:"POST", body:`{"url": "${VIEW_API}"}`});
	fetch(subscribeViewToModel)
	.then(r => {
		if (!r.ok) {
			console.log("Error connecting view and model API. Printing response...");
		}
	});
	// Connect Controller to Model API (so controller can post to the model)
	let subscribeModelToController = new Request(`http://${CONTROLLER_API}/attach-model`, {method:"POST", body:`{"url": "${MODEL_API}"}`});
	fetch(subscribeModelToController)
	.then(r => {
		if (!r.ok) {
			console.log("Error connecting view and model API. Printing response...");
			console.log(r);
		}
	});

	// get references to the three canvas layers
	let bgLayer		= document.getElementById("background");
	let objLayer	= document.getElementById("objects");
	let grLayer		= document.getElementById("gripper");

	// Set up the view js, this also sets up key listeners
	this.layerView = new document.LayerView(VIEW_API, MODEL_API, CONTROLLER_API, bgLayer, objLayer, grLayer);

	// Set up buttons
	$("#start").click(() => document.layerView.startDrawing());
	$("#stop").click(() => document.layerView.stopDrawing());
	
}); // on document ready end