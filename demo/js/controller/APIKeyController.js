$(document).ready(function () {
	

	/**
	 * Demo of how to send local key events to a remote controller API for further processing.
	 * This code could be placed into the local view class, too.
	 */

	// We need to connect the two APIs we're working with
	const MODEL_API			= "127.0.0.1:5000";
	const CONTROLLER_API	= "127.0.0.1:5001";

	// This connects gripper '1' from the model at MODEL_API to the controller API.
	// We could connect any number of grippers and models by repeating this request with different parameters.
	let subscribeModelToController = new Request(`http://${CONTROLLER_API}/attach-model`, {method:"POST", body:`{"url": "${MODEL_API}", "gripper": "1"}`});
	fetch(subscribeModelToController)
	.then(r => {
	if (!r.ok) {
		console.log("Error connecting view and model API. Printing response...", r);
	}
	});

	// Start listening to the user pressing keys
	_initKeyListeners();

	// --- User events ---

	/**
	 * Register the key listeners to allow gripper manipulation.
	 * Notifies the associated controller of ANY key event, no filtering is happening locally.
	 */
	function _initKeyListeners() { 
		// pressing keys
		$(document).keydown( e => {
			let notifyController = new Request(`http://${CONTROLLER_API}/key-pressed/${e.keyCode}`, {method:"POST"});
			fetch(notifyController)
			.then( r => {
				if (!r.ok) { // status code 404 is returned if unassigned key code was sent
					console.log("Unassigned key pressed.");
				}
			});
		});
		// Some keys have a function assigned to being released
		$(document).keyup( e => {
			let notifyController = new Request(`http://${CONTROLLER_API}/key-pressed/${e.keyCode}`, {method:"DELETE"});
			fetch(notifyController)
			.then( r => {
				if (!r.ok) { // status code 404 is returned if unassigned key code was sent
					console.log("Unassigned key released.");
				}
			});
		});
	}

}); // on document ready end