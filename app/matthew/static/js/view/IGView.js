/**
 * File: IGView.js
 * Contains the <IGView> class.
 *
 * Author:
 *		Karla Friedrichs
 *
 * GOLMI Extension For Bachelor Thesis:
 *		"Modeling collaborative reference in a Pentomino domain
 *		using the GOLMI framework"
 */
$(document).ready(function () {

	/**
	 * Class: IGView
	 * Instruction giver view.
	 * Spoken instructions are emitted, guiding a user to choose a specific object.
	 */
	this.IGView = class IGView {
		/**
		 * Func: Constructor
		 * Initializes socket events.
		 *
		 * Params:
		 * modelSocket - Socket io connection to the server
		 * tasks - object mapping task index to tasks,
		 *		in JSON format as accepted by the <Model>
		 * referenceAlg - _str_, name of the algorithm to use for an initial
		 *		instruction, one of ["IA", "RDT", "SE"].
		 *		Determines the feedback algorithm too.
		 * gripperId - identifier used by the <Model> for the <Gripper>
		 *		the instructed user is controlling
		 * feedbackTimeInt - _int_, optional: time (ms) to wait before
		 *		giving feedback if the user is idle
		 * feedbackDistInt - optional: distance (blocks) the user has to
		 *		move the <Gripper> before feedback is given
		 * maxTries - _int_, number of incorrect selections allowed per task
		 */
		constructor(modelSocket, tasks, referenceAlg, gripperId,
			feedbackTimeInt=10000, feedbackDistInt=2, maxTries=3) {
			// server
			this.socket = modelSocket;

			// task management
			this.tasks = tasks;
			this.currentTask = -2; // index of current task
			this.currentTarget; // id of the goal object in the current task
			this.currentObjects; // store objects for performance reasons.
			this.gripperId = gripperId; // id of tracked gripper
			this.config; // server configuration
			this.maxTries = maxTries;
			this.currentTries = 0;

			// set reference and feedback algorithm according to the given name
			this._referenceAlg, this._feedbackAlg;
			this.setAlgorithms(referenceAlg);

			// instruction parameters
			this.instrStart = ["Take", "Select", "Get"];
			this.generalTypes = ["piece"];
			this.properties = ["color", "shape", "posRelBoard"];
			this.trProperties = ["hPosRelGr", "vPosRelGr"];

			// feedback parameters
			this.feedbackTimeInt = feedbackTimeInt;
			this.feedbackDistInt = feedbackDistInt;
			this.lastMsg = 0; // timestamp of the last output message
			this.targetCoords; // target object coordinates (center of object)
			// track positions since last message: [timestamp, x, y]
			this.gripperTrace = new Array();
			this.feedbackTimeoutId; // stores timeout id to manage timed feedback
			
			// audios currently playing or waiting to be played
			this.msgQueue = new Array();
			this._initSocketEvents();
		}

		// --- Getter ---

		// Property: nTasks
		// number of tasks the instance has been assigned
		get nTasks() {
			return Object.keys(this.tasks).length;
		}

		// Property: nextTask
		// Returns next task, counter currentTask is incremented.
		// If there are no more tasks, returns null.
		get nextTask() {
			return (++this.currentTask) < this.nTasks ?
				this.tasks[(this.currentTask).toString()] : null;
		}

		// Property: hasStarted
		// true if some task (excluding training tasks) has been loaded already
		get hasStarted() {
			return this.currentTask >= 0;
		}

		// Property: width
		// Number of blocks per row on the board.
		// If no config was loaded, returns the default 20.
		get width() {
			return this.config ? this.config.width : 20;
		}

		// Property: height
		// Number of blocks per column on the board.
		// If no config was loaded, returns the default 20.
		get height() {
			return this.config ? this.config.height : 20;
		}

		// Property: referenceAlg
		// Function used to generate referring expressions.
		get referenceAlg() {
			return this._referenceAlg;
		}

		// Property: feedbackAlg
		// Function used to generate feedback expressions.
		get feedbackAlg() {
			return this._feedbackAlg;
		}
		
		/**
		 * Func: setAlgorithms
		 * Takes a string and chooses the appropriate class functions
		 * for reference generation and feedback-giving.
		 * Logs an error if function could not be found and defaults
		 * to <IA> and <simpleFeedback>.
		 *
		 * Params:
		 * referenceAlgName - _str_, name of the REG algorithm to use.
		 * 		One of ["IA", "RDT", "SE"].
		 */
		setAlgorithms(referenceAlgName) {
			switch (referenceAlgName) {
				case "IA":
					this._referenceAlg = this.IA;
					this._feedbackAlg = this.simpleFeedback;
					break;
				case "RDT":
					this._referenceAlg = this.RDT;
					this._feedbackAlg = this.RDTFeedback;
					break;
				case "SE": // no reference generation
					this._referenceAlg = null;
					this._feedbackAlg = this.SEFeedback;
					break;
				default:
					console.log("No (valid) reference algorithm selected." +
						" Defaulting to Incremental Algorithm and simple feedback...");
					this.setAlgorithms("IA");
			}
		}
		
		/**
		 * Func: getGripperX
		 *
		 * Params:
		 * stepsBack - _int_ < 0, how many logged positions to look back
		 *
		 * Returns:
		 * gripper x coordinate _stepsBack_ steps back, undefined if no
		 *		coordinate has been logged yet
		 */
		getGripperX(stepsBack=-1) {
			if (this.gripperTrace.length < -stepsBack) {
				return undefined;
			} else {
				// position added last
				return this.gripperTrace[this.gripperTrace.length+stepsBack][1];
			}
		}
		
		/**
		 * Func: getGripperY
		 *
		 * Params:
		 * stepsBack - _int_ < 0, how many logged positions to look back
		 *
		 * Returns:
		 * gripper y coordinate _stepsBack_ steps back, undefined if no
		 *		coordinate has been logged yet
		 */
		getGripperY(stepsBack=-1) {
			if (this.gripperTrace.length < -stepsBack) {
				return undefined;
			} else {
				// position added last
				return this.gripperTrace[this.gripperTrace.length+stepsBack][2];
			}
		}

		/**
		 * Func: getObj
		 *
		 * Params:
		 * id - <Obj> id
		 *
		 * Returns:
		 * object associated to the given id, undefined if id does not exist
		 */
		getObj(id) {
			return this.currentObjects[id];
		}

		/**
		 * Func: getObjValue
		 *
		 * Params:
		 * id - <Obj> id
		 * property - <Obj> property name
		 *
		 * Returns:
		 * value an object with the given id has for the given property name,
		 * undefined if id is unknown or property not defined
		 */
		getObjValue(id, property) {
			if (this.currentObjects[id]) { 
				return this.currentObjects[id][property];
			}
			return undefined;
		}

		// --- socket events --- //
	
		// initialize listeners for socket events
		_initSocketEvents() {
			this.socket.on("update_config", (config) => {
				this.config = config;
			});
			// state was loaded. Start giving instructions
			this.socket.on("update_state", (state) => {
				// get the objects from the server, since the state might differ slightly
				// from the sent task (because of defaults and configuration restrictions).
				// It's best to synchronize with the server to match the instruction with
				// what is displayed.
				this.currentObjects = state["objs"];
				// save the target coordinates (if objects containing the target were sent)
				if (this.currentObjects[this.currentTarget]) {
					let target = this.currentObjects[this.currentTarget];
					this.targetCoords = [target.x+(target.width/2), target.y+(target.height/2)];
					this.giveInstruction();
				}
			});
			this.socket.on("update_grippers", (grippers) => {
				if (grippers[this.gripperId]) {
					if (grippers[this.gripperId]["gripped"]) {
						// task is completed if 
						// (a) correct object was selected
						// (b) maxTries incorrect attempts were made
						if (Object.keys(grippers[this.gripperId]["gripped"]).includes(
								this.currentTarget)) {
							// target was selected
							this.taskCompleted();	
						} else {
							if (++this.currentTries >= this.maxTries) {
								this.taskCompleted();
							} else {
								// automatically ungrip the piece
								this.socket.emit("grip", {"id": this.gripperId});
								// tell the participant they have to try again
								this._queueMsg("That was incorrect", "feedback");
								// empty the gripper trace. The user is obviously on
								// the wrong track so we do a small reset
								this.gripperTrace = this.gripperTrace.slice(-1);
								this.giveFeedback(true);
							}
						}
						
					} else {
						// the gripper has been moved (-> might trigger feedback)
						// save the new gripper position
						this.gripperTrace.push([
												Date.now(),
												grippers[this.gripperId].x,
												grippers[this.gripperId].y
												]);
						// if feedback algorithm is set and significant progress
						// was made, give feedback to user
						if (this.feedbackAlg) {
							this.giveFeedback();
						}
					}
				}
			});
		}

		// --- Task flow ---

		/**
		 * Func: start
		 * Load the first task and start listening to server updates.
		 * Logs an error if loading fails.
		 */
		start() {
			// introduction
			this.welcome();
			// start the task flow
			this.currentTask = -2;
			if (!this._loadTask()) {
				console.log("Error: No task could be loaded at IGView." +
					" Passed empty task object?");
				this.goodbye();
			}
		}

		/**
		 * Func: taskCompleted
		 * User completed a task. Emit a message to the user,
		 * stop updating and try loading the next task.
		 * Emits 'logSegment' event to the document.
		 */ 
		taskCompleted() {
			// abort pending messages
			this.abortAllMsgs();
			// pause feedback loop until a new task is started
			this.stopFeedbackTimeout();
			// emit global event for logger to catch
			document.dispatchEvent(new CustomEvent("logSegment", { detail: {
				"segmentTitle": this.currentTask, "additionalData": {
					"target": this.currentTarget,
					"incorrectAttempts": this.currentTries
				}
			}}));
			if (!this._loadTask()) {
				this.goodbye();
			}
		}

		/**
		 * If there is another task, emit a 'load_state' event
		 * to the server, then save the objects and target of this task.
		 * Returns: true if a task was loaded, false if no
		 *		more tasks are available
		 */
		_loadTask() {
			// load the next (predefined) task
			let task = this.nextTask;
			// task is null if no tasks remain
			if (!task) { return false; }
			// empty the instruction display
			this._emptyDisplay();
			// reset the attempts
			this.currentTries = 0;
			// set the goal object
			this.currentTarget = task.target.toString();
			// remember the gripper start position
			this.gripperTrace = [ [
									Date.now(),
									task.task.grippers[this.gripperId].x,
									task.task.grippers[this.gripperId].y
								] ];

			// load the task into the server
			this.socket.emit("load_state", task.task);
			return true;
		}

		// --- User communication --- //

		/**
		 * Func: welcome
		 * Welcome the user, explain rules, etc.
		 */
		welcome() {
			// welcome the participant
			this._queueMsg("Welcome! I'm Matthew." +
				" Let's pick up some Pentomino pieces together." +
				" The first task is just for warming up before we get to the study");
			// explain the rules
			this._queueMsg("Move around using the arrow keys" +
				" and select an object using space or enter." +
				" You have 3 tries to get the correct piece");
		}

		/**
		 * Func: goodbye
		 * Thank the user for participating, etc.
		 * Emit a 'tasksCompleted' event to the document.
		 */
		goodbye() {
			this._queueMsg("Thank you for participating. Have a nice day");
			document.dispatchEvent(new Event("tasksCompleted"));
		}

		/**
		 * Func: giveInstruction
		 * Construct and queue a full instruction, describing the target piece
		 * to the user, using the selected REG algorithm.
		 */
		giveInstruction() {
			// use reference algorithm to generate an instruction, otherwise force feedback 
			let instr = this.referenceAlg ? this.referenceAlg() : this.feedbackAlg(true);
			this._queueMsg(instr, "instruction");
		}

		/**
		 * Func: giveFeedback
		 * If a feedback algorithm is set, react to the user's progress
		 * by constructing and queueing a feedback message.
		 * Depending on the algorithm, this might be further information,
		 * correction or support.
		 *
		 * Params:
		 * force - if set to true, no additional checks will be made
		 */
		giveFeedback(force=false) {
			// try to contruct feedback - returns null if no feedback needed
			let feedback = this.feedbackAlg(force);
			if (feedback) {
				this._queueMsg(feedback, "feedback");
			}
		}

		/**
		 * Prepare a message to deliver to the user. It will be played
		 * once it reaches the top of the message queue.
		 * Params:
		 * msg - _str_, message to send
		 * type - type of message, one of ["instruction", "feedback", "meta"],
		 * 		used for logging
		 */
		_queueMsg(msg, type="meta") {
			// stop the feedback loop, will be restarted once queue is empty
			this.stopFeedbackTimeout();
			// get the audio filename: msg in lower case, without spaces or
			// special characters and with an .mp3 extension
			let msgFile = msg.toLowerCase();
			for (let char of [" ", ",", ".", "'", "!", "?"]) {
				msgFile = msgFile.replaceAll(char, "");
			}
			msgFile = "./static/resources/audio/" + msgFile + ".mp3";
			let audio = new Audio(msgFile);
			// Safari browser needs this line
			audio.load();
			// keep the message in the queue until it has been delivered, this way we have a
			// reference to it in case we need to abort playing
			this.msgQueue.push([msg, audio, type]);
			
			// if there is no other message currently playing, start this message immediately
			if (this.msgQueue.length == 1) {
				this._playNextMsg();
			}
		}
		
		/**
		 * Func: abortAllMsgs
		 * Stop any audio currently playing and delete waiting messages.
		 */
		abortAllMsgs() {
			if (this._hasPendingMsg()) {
				this.msgQueue[0][1].pause();
				this.msgQueue = new Array();
			}
		}
		
		/**
		 * Play the first message waiting in the message queue.
		 * Emits a 'emitMessage' event to the document.
		 */
		_playNextMsg() {
			if (this._hasPendingMsg()) {
				// play the first message in the queue
				let [nextMsg, nextAudio, nextType] = this.msgQueue[0];
				// if an error occurs because the audio doesn't exist,
				// at least display the message on the screen
				if (nextAudio.error) {
					this._displayNextMsg();
					return;
				}
				nextAudio.onerror = () => this._displayNextMsg();
				nextAudio.onended = () => this._msgEnded();
				// dispatch event and play as soon as the audio is ready:
				if (nextAudio.readyState >= 2) {
						document.dispatchEvent(new CustomEvent("emitMessage", { detail: {
							"type": nextType, "content": nextMsg, "duration": nextAudio.duration
						}}));
						nextAudio.play();
				} else {
					nextAudio.oncanplaythrough = function() {
						// dispatch message event
						document.dispatchEvent(new CustomEvent("emitMessage", { detail: {
							"type": nextType, "content": nextMsg, "duration": nextAudio.duration
						}}));
						nextAudio.play();
					};
				}
			}
		}
		
		/**
		 * Fallback method for message delivery in case audio can't be used.
		 * Not very user-friendly, prints to the interface.
		 * Emits a 'emitMessage' event to the document.
		 */
		_displayNextMsg() {
			if (this._hasPendingMsg()) {
				let [nextMsg, nextAudio, nextType] = this.msgQueue[0];
				// dispatch message event (with error tag)
				document.dispatchEvent(new CustomEvent("emitMessage", { detail: {
					"type": nextType, "content": nextMsg, "error":true
				}}));
				// print message to console and display in the interface
				console.log(nextMsg);
				$("#instructions").text(nextMsg);
				// delete the message from the queue
				this._msgEnded();
				// continue with the next message
				this._playNextMsg();
			}
		}
		
		/**
		 * Delete any message currently displayed in the interface.
		 * (see _displayNextMsg())
		 */
		_emptyDisplay() {
			$("#instructions").text("");
		}
		
		/**
		 * Function called after a message has been delivered (i.e. was
		 * displayed or audio has ended). Reset gripper trace. Play the
		 * next waiting message or restart the feedback timer.
		 */
		_msgEnded() {
			// update the timestamp of the last message delivered to the user
			this.lastMsg = Date.now();
			// delete old gripper trace and start tracking again from the recorded last position
			this.gripperTrace = this.gripperTrace.slice(-1);
			// delete the audio from the queue
			let msgType = this.msgQueue[0][2];
			this.msgQueue = this.msgQueue.slice(1);
			// make sure any waiting message is played next
			if (this._hasPendingMsg()) {
				this._playNextMsg();
			} else if (msgType != "meta") {
				// (re)start the feedback loop if the delivered message was
				// instruction or feedback
				this.startFeedbackTimeout(this.feedbackTimeInt);
			}
		}
		
		/**
		 * Check if the internal message queue contains pending messages.
		 * Returns:
		 * true if a message is currently playing or waiting to be played
		 */
		_hasPendingMsg() {
			return this.msgQueue.length > 0;
		}
		
		/**
		 * Func: startFeedbackTimeout
		 * Give feedback to the user after some time has elapsed.
		 * Stop the loop using <stopFeedbackTimeout>.
		 *
		 * Params:
		 * delay - time (ms) to wait before generating feedback
		 */
		startFeedbackTimeout(delay) {
			this.stopFeedbackTimeout();
			// start a timer: after set time of no interaction with the user,
			// feedback message is given
			if (this.feedbackAlg) {
				let thisArg = this;
				this.feedbackTimeoutId = setTimeout(async function() {
					// pass argument true so _needFeedback is not checked
					thisArg.giveFeedback(true);
				}, delay);
			}
		}

		/**
		 * Func: stopFeedbackTimeout
		 * Stop giving feedback in regular time intervals.
		 */
		stopFeedbackTimeout() {
			if (this.feedbackTimeoutId) { clearTimeout(this.feedbackTimeoutId); }
		}

		// --- Reference generation algorithms --- //

		// --- Incremental Algorithm by E. Reiter & R. Dale --- //

		/**
		 * Func: IA
		 * Construct a reference using the incremental algorithm. 
		 * Algorithm adapted from E. Reiter & R. Dale (1992).
		 * See <https://aclanthology.org/C92-1038.pdf> and
		 * the thesis for the full source and a description.
		 */
		IA() {
			// preference order
			let P = this.properties;
			// construct a contrast set: first copy all objects into a set
			let C = new Set(Object.values(this.currentObjects));
			// target piece. Named r here to better match the pseudocode
			// by Reiter & Dale
			let r = this.currentObjects[this.currentTarget];
			// remove the target from the contrast set
			C.delete(r);

			// property-value pairs are collected here
			let L = new Array();
		
			for (let prop of P) {
				let val = this._findValue(r, prop);
				// check what objects would be eliminated using this prop-val pair
				let ruledOutObjs = this._rulesOut(prop, val, C);
				if (val && (ruledOutObjs.length > 0)) {
					// save the property
					L.push([prop, val]);
					// update the contrast set
					ruledOutObjs.forEach(ruledOut => C.delete(ruledOut));
				}

				// check if enough properties have been collected to rule out
				// all contrast objects
				if (C.size == 0) {
					return document.randomFromArray(this.instrStart) + " the " + this._verbalizeRE(L);
				}
			}
			// no expression that rules out all contrast objects was found
			// original algorithm declares "IA: failure", but with the task at hand
			// this case is expected. User is supported by feedback.
			return document.randomFromArray(this.instrStart) + " the " + this._verbalizeRE(L);
		}

		/**
		 * Helper function for IA.
		 * Params:
		 * prop - property name
		 * val - value the target object has assigned to the given property
		 * constrastSet - contrast set of objects to rule out by the given
		 *		the property-value pair
		 * Returns:
		 * array of contrast objects with a different value for prop
		 */
		_rulesOut(prop, val, contrastSet) {
			let ruledOutObjs = new Array();
			contrastSet.forEach(obj => {
				if (this._findValue(obj, prop) != val) {
					ruledOutObjs.push(obj);
				}
			});
			return ruledOutObjs;
		} 

		// --- REG algorithm with Reference Domain Theory by Denis (2010) --- //

		/**
		 * Func: RDT
		 * Function for the initial instruction when using the RDT
		 * algorithm by A. Denis 2010.
		 * See <https://aclanthology.org/W10-4203.pdf>.
		 * Define a 'nested class' Domain. Initially create the referential
		 * space and generate the first instruction.
		 *
		 * Returns:
		 * initial instruction created using the RDT algorithm
		 */
		RDT() {
			// Mimicking a 'nested class' here for the notion of a domain -
			// it's really just a function contructing an object
			
			// Class: Domain
			// Represents a domain as used by the RDT algorithm.
			this.Domain = class {
				/** Func: Constructor
				 *
				 * Params:
				 * ground - set of object in this <Domain>
				 * semanticDesc - set of property-value pairs applying to
				 *		all objects in the ground
				 * salience - int, score describing how 'activated' a <Domain>
				 *		is in the current dialogue
				 * partition - triple: property name, object mapping property
				 *		values to sets of objects with this value, focus of partition
				 */
				constructor(ground, semanticDesc, salience, partition) {
					this.ground			= ground;
					this.semanticDesc	= semanticDesc;
					this.salience 		= salience;
					this.partition		= partition;
				}
			}

			// create the referential space
			this.RS = new Set();
			// shallow copy of the property array
			let T = this.properties.slice()
			// create the root domain
			let D = new this.Domain(new Set(Object.keys(this.currentObjects)), new Set(), 0, null);
			// initially create a partition structure (all arguments are passed by reference)
			this._createPartitions(D, T);
			return document.randomFromArray(this.instrStart) + " " + this.generateRDT();
		}

		/**
		 * Func: generateRDT
		 * Generate a new reference to the current target object,
		 * using the current referential space.
		 * (see original paper Fig. 2: generate)
		 *
		 * Params:
		 * t - optional: referent or set of referents to generate a
		 * 		referring expression for *default*: set containing
		 *		current target
		 *
		 * Returns:
		 * referring expression describing t
		 */
		generateRDT(t=(new Set([this.currentTarget]))) {
			// get the most salient / specific domain containing currentTarget
			let D = this._getBestDomain(t);
			// get the properties describing the target in the selected domain:
			// 1. properties shared by all objects in the domain
			let S = new Set(D.semanticDesc);
			// 2. property differentiating the target(s) within the domain
			for (let [value, valueSet] of Object.entries(D.partition[1])) {
				// look for a partition that contains all of the target objects
				// if such a partition exists, add the property-value pair to the semantic description
				if (document.isSuperset(valueSet, t)) {
					S.add([D.partition[0], value]);
					break;
				}
			}

			// select an underspecified domain 
			let underspecifiedD = this._matchUnderspecifiedDomain(t, D, S);
			this.restructure(D, S);
			return underspecifiedD;
		}

		/**
		 * Func: restructure
		 * Restructure the referential space after a reference within D,
		 * using only the persistent properties of S. Transient properties
		 * and all <Domain>s and partitions generated using them are deleted.
		 * (see original paper Fig. 3: restructure)
		 *
		 * Params:
		 * D - <Domain>
		 * S - set of property-value pairs
		 */
		restructure(D, S) {
			// collect all persistent properties in S
			let Sp = new Set(S);
			// collect all objects from this domain that have these properties
			let Gp = new Set(D.ground);
			// delete any non-persistent property
			Sp.forEach(prop => {
				if (!this.properties.includes(prop[0])) {
					Sp.delete(prop);
				} else {
					// delete objects from Gp that don't have the property
					Gp.forEach(obj => {
						if (this._findValue(this.getObj(obj), prop[0]) != prop[1]) {
							Gp.delete(obj);
						}	
					});
				}
			});

			// increase the salience of the domain containing Gp
			let foundMatchingDomain = false;
			for (let domain of this.RS) {
				if (document.setEquals(domain.ground, Gp)) {
					domain.salience = this._getMaxSalience() + 1;
					foundMatchingDomain = true;
					break;
				}
			}
			if (!foundMatchingDomain) {
				// if no matching domain was found, create a new domain with maximum salience
				let newD = new this.Domain(
					Gp, Sp, this._getMaxSalience()+1, this._defaultPartition(Gp)
				);
				this.RS.add(newD);
			}
		}

		/**
		 * Create a partition tree structure. 
		 * Iterating throught the properties in the order defined by T,
		 * the set of objects ('ground' of the given <Domain> D) is divided
		 * into subsets sharing some property value, until sets with only
		 * one entry each are left.
		 * Newly created <Domain>s are added to this instance's RS set.
		 * (see original paper Fig. 1: createPartitions)
		 * Params:
		 * D - Domain instance to be further partitioned
		 * T - array of property names in a preference order
		 */
		_createPartitions(D, T) {
			this.RS.add(D);
			if (T.length > 0) {
				let P = this._getPartition(D.ground, T[0]);
				let partitionKeys = Object.keys(P);
				if (partitionKeys.length == 1) {
					// only one partition was created
					// add the property-value pair to the partition's shared description
					D.semanticDesc.add([T[0], partitionKeys[0]]);
					// recursively proceed with the remaining properties
					this._createPartitions(D, T.slice(1));
				} else {
					D.partition = [T[0], P, new Set()];
					// further divide any partition with more than one member
					partitionKeys.forEach(key => {
						if (P[key].size > 1) {
							// create the semantic description of the new domain (using set union)
							let newSemantic = new Set([[T[0], key]]);
							D.semanticDesc.forEach(desc => newSemantic.add(desc));
							// create the new domain and its partitions
							// the paper asks to create a default partition here, but this
							// is not necessary unless no more properties are left
							let newD = new this.Domain(P[key], newSemantic, D.salience, null);
							this._createPartitions(newD, T.slice(1));
						}
					})
				}
			} else {
				// no more properties are left, the default partition is used to give each object its own set anyway
				D.partition = this._defaultPartition(D.ground);
			}
		}

		/**
		 * Create the default partition defined as:
		 * def(X) = ("id", X/R_id, new Set())
		 * where X/R_id denotes creating subsets with one element of X each.
		 * Params:
		 * X - set of objects to create a default partition for
		 * Returns:
		 * partition array: ["id", subsets, focus]
		 */
		_defaultPartition(X) {
			let partition = ["id", new Object(), new Set()];
			// put each object into its own subset, labeled with the object identifier
			X.forEach(obj => { partition[1][obj] = new Set([obj]); });
			return partition;
		}

		/**
		 * Create a partition of a set of objects with respect to some property.
		 * In other words, create the quotient set of 'ground' by 'property'.
		 * Params:
		 * ground - set of objects to divide
		 * property - property name for division: each object in 'ground'
		 *		should have this property
		 * Returns:
		 * The partition is realized as an object here, each value found
		 * for property maps to a set of objects
		 */
		_getPartition(ground, prop) {
			let partition = new Object();
			// divide the objects
			ground.forEach(obj => {
				let val = this._findValue(this.getObj(obj), prop);
				// if value has not been encountered before, create a new set for obj
				if (!(partition[val])) {
					partition[val] = new Set([obj]);
				} else {
					partition[val].add(obj);
				}
			});
			return partition;
		}

		/**
		 * Find the best <Domain> to a set of targets. The original paper
		 * asks for selecting the <Domain> with the highest salience and
		 * the fewest members. It is not explicitly stated which of the
		 * criteria is to be prioritized, therefore the first-mentioned
		 * (salience) is prioritized here.
		 * t - optional: referent or set of referents to generate a RE
		 *		for, *default*: set containing current target
		 * Returns: most salient / specific <Domain> from RS for _t_
		 */
		_getBestDomain(t=(new Set([this.currentTarget]))) {
			let bestDomain;
			this.RS.forEach(domain => {
				// check if domain contains the current target
				if (document.isSuperset(domain.ground, t)) {
					if (!bestDomain) {
						// no competing domain found yet, just assign this one
						bestDomain = domain;
					} else {
						// check if this domain is more salient or is smaller (= more specific)
						// with equal salience
						if (domain.salience > bestDomain.salience) {
							bestDomain = domain;
						} else if (domain.salience == bestDomain.salience &&
								domain.ground.size < bestDomain.ground.size) {
							bestDomain = domain;
						}
					}
				}
			});
			return bestDomain;
		}

		/**
		 * Find an underspecified domain matching the given <Domain>.
		 * (see original paper Fig. 2 line 3; underspecified domains
		 * are defined in Table 1)
		 * Params:
		 * t - set of target object(s)
		 * D - most salient / specific <Domain> containing _t_
		 * S - property-value pairs describing _t_
		 * Returns: string, underspecified reference to _t_
		 */
		_matchUnderspecifiedDomain(t, D, S) {
			let plural = (t.size > 1);
			// the cases listed in Table 1 of the paper are checked in decreasing Giveness
			if (document.setEquals(D.partition[2], t)) {
				// case 1 and 2: Focus is {currentTarget}
				return plural ? "these ones" : "this one";
			}

			// if there is a constrasting attribute (i.e. the partition was
			// NOT constructed using "id"), find the partition in d that contains t
			let tPartition;
			if (D.partition[0] == "id") {
				tPartition = D.ground;
			} else {
				for (let partition of Object.values(D.partition[1])) {
					if (document.isSuperset(partition, t)) {
						tPartition = partition;
						break;
					}
				}
			}

			// if t is not a partition of D for some reason, use case 8
			if (!tPartition) return "a " + this._verbalizeRE(S, plural);

			if (tPartition.size == t.size) {
				// case 3: within the domain D, currentTarget is unambiguously describable 
				// (i.e. has its own partition)
				return "the " + this._verbalizeRE(S, plural);
			} else if (D.partition[2].size > 0) {
				// focus is not empty
				// two cases: either target is only partition out of focus
				// or multiple partitions are out of focus
				for (let partition of Object.values(D.partition[1])) {
					for (let partitionInFocus of D.partition[2]) {
						// check whether the partition is NOT in focus AND NOT the target set
						// -> case 6 / 7
						if (!document.setEquals(partition, partitionInFocus) && 	!document.setEquals(partition, t)) {
							return "another one";
						}
					}
				}
				// no 'out of focus' partition except t was found: case 4/5
				return "the other one";
			} else {
				return "a " + this._verbalizeRE(S, plural);
			}
			// failure case is emitted here since the last case ("a N") is used a default
		}

		// --- REG helper functions used by multiple algorithms --- //

		/**
		 * Determine the value an <Obj> has for a given property name.
		 * Logs an error if the given property name is not implemented.
		 * Params:
		 * obj - IGView's representation of a GOLMI <Obj>
		 * prop - _str_, property name
		 * Returns: _str_, value matching _obj_
		 */
		_findValue(obj, prop) {
			switch(prop) {
				case "shape":
					return obj.type;
				case "color":
					return obj.color;
				case "posRelBoard":
					// describe top/bottom position
					let val = "";
					// the x / y properties of objects describe the upper left corner
					// -> here we use the center coordinates instead 
					let x = obj.x + (obj.width/2);
					let y = obj.y + (obj.height/2);
					let fifth = this.width/5;
					if (y < 2*fifth) {
						val = "top";
					} else if (y >= 3*fifth) {
						val = "bottom";
					}
					// describe left/right position
					if (x < 2*fifth) {
						val = val.length > 0 ? val + " left" : "left";
					} else if (x >= 3*fifth) {
						val = val.length > 0 ? val + " right" : "right";
					// if no value was assigned yet, piece is in the center
					} else if (val.length == 0) {
						val = "center";
					}
					return val;
				case "hPosRelGr":
					// horizontal position relative to the gripper
					if (!this.getGripperX()) {
						return "";
					} else if (obj.x + obj.width <= this.getGripperX()) {
						return "left of";
					} else if (obj.x >= this.getGripperX()) {
						return "right of";
					} else {
						return "";
					}
				case "vPosRelGr":
					// vertical position relative to the gripper
					if (!this.getGripperY()) {
						return "";
					} else if (obj.y + obj.height <= this.getGripperY()) {
						return "above";
					} else if (obj.y >= this.getGripperY()) {
						return "below";
					} else {
						return "";
					}
				default:
					console.log(`Error at _findValue(): property ${prop} not implemented`);
					return null;
			}
		}

		/**
		 * Construct a natural language description from collected
		 * property-value pairs.
		 * Params:
		 * propVals - object mapping property names to values
		 * plural - _bool_, optional: pass true to produce a plural form
		 * Returns: _str_, RE containing the values from _propVals_
		 */
		_verbalizeRE(propVals, plural=false) {
			// property "id" is simply ignored
			let color = "", shape = "", posRelBoard = "", hPosRelGr = "", vPosRelGr = "";
			propVals.forEach(([prop, val]) => {
				switch(prop) {
					case "color":
						color = val;
						break;
					case "shape":
						shape = val;
						break;
					case "posRelBoard":
						posRelBoard = "in the " + val;
						break;
					case "hPosRelGr":
						hPosRelGr = val;
						break;
					case "vPosRelGr":
						vPosRelGr = val;
				}
			});
			// if no shape given, use a generic noun
			shape = shape ? shape :
				this.generalTypes[Math.floor(Math.random() * this.generalTypes.length)];
			// special case: hpos and vpos are the only properties, but the gripper
			// is right above the piece so both have the value ""
			
			// if two types of positions are used, connect them
			let conj = posRelBoard && (vPosRelGr || hPosRelGr) ? "of the board and " : "";
			// add the values in a natural-sounding order
			return `${color} ${shape}${plural ? "s" : ""} ${posRelBoard}` +
				` ${conj}${vPosRelGr} ${hPosRelGr}${(hPosRelGr || vPosRelGr) ? " the gripper" : ""}`;
		}

		/**
		 * Get the maximum value of salience any <Domain> in RS has.
		 */
		_getMaxSalience() {
			let maxS = 0;
			this.RS.forEach(domain => {
				if (domain.salience > maxS) {
					maxS = domain.salience;
				}
			});
			return maxS;
		}

		// --- Feedback algorithms --- //
		
		// --- Simple feedback for REG algorithms that come without feedback function --- //
		
		/**
		 * Func: simpleFeedback
		 * Dummy feedback algorithm to use for algorithms that don't come with
		 * a feedback mechanism by default. Resorts to giving positive or negative
		 * signals when the user is moving. If the user doesn't act, the reference
		 * algorithm is called to re-produce a referring expression (repeat type
		 * feedback).
		 *
		 * Params:
		 * force - _bool_, if set to true, no additional checks will be made
		 *
		 * Returns:
		 * natural language feedback expression or null
		 */
		simpleFeedback(force=false) {
			if (!force && !this._needFeedback()) {
				return null;
			}
			let negFeedback = ["Not this direction", "Not there", "No"];
			let posFeedback = ["Yes, this direction", "Yes", "Yeah", "Yes, this way"];
			// determine what kind of feedback to give
			let type;
			switch(this._lastDirectionToTarget()) {
				case 1:
					// moving towards target: positive feedback
					return document.randomFromArray(posFeedback);
				case -1:
					// moving away from target: negative feedback
					return document.randomFromArray(negFeedback);
				case 0:
					// no recent movement: repeat the RE
					return this.referenceAlg();
			}
		}
		
		/**
		 * Determines what direction in relation to the target the user
		 * has been moving recently.
		 * Returns:
		 * 1: towards target, -1: away from target, 0: no movement in feedbackTimeInt/2
		 */
		_lastDirectionToTarget() {
			if (this.gripperTrace.length < 2 ||
					this.gripperTrace[this.gripperTrace.length-1][0] -
					this.gripperTrace[this.gripperTrace.length-2][0] >
					this.feedbackTimeInt/2) {
				// if the user has not moved in the last feedbackTimeInt/2 ms,
				// no focus seems to be set
				return 0;
			}
			// check if distance to target has been reduced by last movement:
			let lastDist = document._vectorDist(
				this.gripperTrace[this.gripperTrace.length-2].slice(1), this.targetCoords
			);
			let currentDist = document._vectorDist(
				this.gripperTrace[this.gripperTrace.length-1].slice(1), this.targetCoords
			);
			if (currentDist < lastDist) {
				return 1;
			} else if (currentDist > lastDist) {
				return -1;
			} else {
				return 0;
			}
		}
		
		// --- REG algorithm with Reference Domain Theory by Denis (2010) --- //

		/**
		 * Func: RDTFeedback
		 * Feedback algorithm from A. Denis 2010.
		 * See <https://aclanthology.org/W10-4203.pdf>
		 * (feedback algorithm given in Figure 4).
		 * Feedback is emitted with respect to the current focus on objects
		 * from the most salient <Domain> containing the target. The internal
		 * referential space will be updated with each generated feedback.
		 *
		 * Params:
		 * force - _bool_, if set to true, no additional checks will be made
		 *
		 * Returns:
		 * natural language feedback expression or null
		 */
		RDTFeedback(force=false) {
			// check if feedback is needed
			if (!force && !this._needFeedback()) {
				return null;
			}
			// get the most salient / specific domain containing currentTarget
			let D = this._getBestDomain()
			let F = this._getObjsInFocus(D);
			// Update the focus of this domain
			D.partition[2] = F;
			if (F.has(this.currentTarget)) {
				if (F.size > 1) {
					let newD = new this.Domain(F, new Set(D.semanticDesc), D.salience+1, null);
					this._createPartitions(newD, this.trProperties);
					let feedback = "Yeah. " + this.generateRDT();
					// delete the domains that use transient properties
					this._removeTransientDomains();
					return feedback;
				} else {
					return "Yeah. " + this.generateRDT();
				}
			} else {
				if (F.size == 0) {
					return "Look for " + this.generateRDT();
				} else {
					return "Not " + this.generateRDT(F) + ". " +
						"Look for " + this.generateRDT();
				}
			}
		}

		/**
		 * Selects from the given <Domain> all objects in front / in moving
		 * direction of the gripper.
		 * In the original paper, a different setting is used and visible
		 * objects are objects in the same virtual room as the user.
		 * Here, all objects are always visible, so a different assumption
		 * is used: The user focuses on objects they move the gripper towards.
		 * Params:
		 * domain - <Domain> to filter for objects in focus
		 * Returns: set of objects 'in focus'
		 */
		_getObjsInFocus(domain) {
			if (this.gripperTrace.length <= 1) {
				// if the user has not moved, no focus seems to be set
				return new Set();
			} 

			let inFocus = new Set(domain.ground);
			// determine the moving direction (computed using the last two
			// logged positions)
			let horizontalDir = this.getGripperX(-1) - this.getGripperX(-2);
			let verticalDir = this.getGripperY(-1) - this.getGripperY(-2);

			if (horizontalDir == 0 && verticalDir == 0) {
				// if the user has not moved since last message, no focus seems
				// to be set
				return new Set();
			}
			// if a direction is 0, no filters need to be applied
			// otherwise, remove any objects 'behind' the current gripper
			// position (or at the same height/width)
			// filter for horizontal direction
			if (horizontalDir > 0) {
				inFocus.forEach(obj => {
					if (this.getObjValue(obj, "x") + this.getObjValue(obj, "width") -
							this.getGripperX() < 0) {
						inFocus.delete(obj);
					}
				});
			} else if (horizontalDir < 0) {
				inFocus.forEach(obj => {
					if (this.getObjValue(obj, "x") - this.getGripperX() > 0) {
						inFocus.delete(obj);
					}
				});
			}
			// filter for vertical direction
			if (verticalDir > 0) {
				inFocus.forEach(obj => {
					if (this.getObjValue(obj, "y") + this.getObjValue(obj, "height") -
							this.getGripperY() < 0) {
						inFocus.delete(obj);
					}
				});
			} else if (verticalDir < 0) {
				inFocus.forEach(obj => {
					if (this.getObjValue(obj, "y") - this.getGripperY() > 0) {
						inFocus.delete(obj);
					}
				});
			}
			return inFocus;
		}
		
		/**
		 * Remove any <Domain> in the reference space that uses transient
		 * properties in its semantic description or partition structure.
		 */
		_removeTransientDomains() {
			this.RS.forEach(domain => {
				if (this.trProperties.includes(domain.partition[0])) {
					this.RS.delete(domain);
				} else {
					for (let [prop, _] of domain.semanticDesc) {
						if (this.trProperties.includes(prop)) {
							this.RS.delete(domain);
							break;
						}
					}
				}
			});
		}
		
		// --- Supervised exploration --- //
		/**
		 * Func: SEFeedback
		 * Feedback to be used on its own.
		 * Produces incremental instructions relative to the current gripper
		 * position. See the thesis for details on the motivation of this
		 * algorithm.
		 *
		 * Params:
		 * force - _bool_, if set to true, no additional checks will be made
		 *
		 * Returns:
		 * natural language feedback expression or null
		 */
		SEFeedback(force=false) {
			// we need at least the start position
			if (this.gripperTrace.length == 0) {
				return null;
			}
			// correct position = three blocks in center
			let lThreshold = Math.floor(this.targetCoords[0]-1);	// left threshold
			let rThreshold = Math.ceil(this.targetCoords[0]+1);		// right threshold
			let tThreshold = Math.floor(this.targetCoords[1]-1);	// top threshold
			let bThreshold = Math.ceil(this.targetCoords[1]+1);		// bottom threshold
			
			// check if gripper is in the correct x range
			let inXRange = (this.getGripperX() > lThreshold && this.getGripperX() < rThreshold);
			// check if gripper entered the x range with the last step
			let justEnteredXRange = inXRange && this.gripperTrace.length > 1 &&
				(this.getGripperX(-2) <= lThreshold || this.getGripperX(-2) >= rThreshold);
			// check if gripper is in the correct y range
			let inYRange = this.getGripperY() > tThreshold && this.getGripperY() < bThreshold;
			// check if gripper entered the y range with the last step
			let justEnteredYRange = inYRange &&
				this.gripperTrace.length > 1 &&
				(this.getGripperY(-2) <= tThreshold || this.getGripperY(-2) >= bThreshold);

			if ((justEnteredXRange && inYRange) || justEnteredYRange && inXRange) {
				// instruct to grip if last user action brought the gripper close to the target
				//this.abortAllMsgs();
				return document.randomFromArray(this.instrStart) + " this object";
			} else if (justEnteredXRange) {
				// x axis is now correct, y axis not: give instruction for y direction
				return "Stop. " + document.randomFromArray(["Go", "Move"]) + " " +
					this._yFeedback();
			} else if (justEnteredYRange) {
				// x axis is now correct, y axis not: give instruction for y direction
				return "Stop. " + document.randomFromArray(["Go", "Move"]) + " " +
					this._xFeedback();
			} else if (force || this._needFeedback()) {
				// special case: instruction follower is ready to grip
				if (inXRange && inYRange) {
					//this.abortAllMsgs();
					return document.randomFromArray(this.instrStart) + " this object";
				}
				// give feedback if user made some progress or was idle for some time
				// check if the last step went into the right direction
				switch(this._lastDirectionToTarget()) {
					case 1:
						// moving towards target: give positive feedback
						return document.randomFromArray([
							"Yes, this direction", "Yes", "Yeah", "Yes, this way"
						]);
					case -1:
						// moving away from target: negative feedback + adjustment
						return "No. " + document.randomFromArray(["Go", "Move"]) + " " +
							((inXRange) ? this._yFeedback() : this._xFeedback());
					case 0:
						// no recent movement: give new adjustment
						return document.randomFromArray(["Go", "Move"]) + " " +
							((inXRange) ? this._yFeedback() : this._xFeedback());
					}
			} else {
				// no feedback triggered
				return null;
			}
		}
		
		/**
		 * Generate horizontal feedback for SEFeedback.
		 * Returns:
		 * feedback to the horizontal distance between <Gripper> and target
		 */
		_xFeedback() {
			let feedback = "";
			let xDifference = this.targetCoords[0] - this.getGripperX();
			switch (Math.sign(xDifference)) {
				case -1:
					feedback += "left";
					break;
				case 1:
					feedback += "right";
					break;
				default:
					// difference is 0 -> no feedback
					return feedback;
			}
			if (Math.abs(xDifference) > this.width/4) {
				return feedback;
			} else {
				return "a bit " + feedback;
			}
		}
		
		/**
		 * Generate horizontal feedback for SEFeedback.
		 * Returns:
		 * feedback to the vertical distance between <Gripper> and target
		 */
		_yFeedback() {
			let feedback = "";
			let yDifference = this.targetCoords[1] - this.getGripperY();
			switch (Math.sign(yDifference)) {
				case -1:
					feedback += "up";
					break;
				case 1:
					feedback += "down";
					break;
				default:
					// difference is 0 -> no feedback
					return feedback;
			}
			if (Math.abs(yDifference) > this.height/4) {
				return feedback;
			} else {
				return "a bit " + feedback;
			}
		}

		
		// --- Feedback helper functions used by multiple algorithms --- //

		/**
		 * Check whether to give feedback to the user at the current time.
		 * The decision is based on the user's progress since the last
		 * message.
		 * Returns:
		 * _bool_, true if feedback should be emitted
		 */
		_needFeedback() {
			// no message has been given to the user yet, so no initial instruction either -> no feedback
			if (this.gripperTrace.length == 0) return false;
			// criteria for feedback:
			// 1. user moved the gripper a predefined distance since last communication
			// 2. no other messages in the queue
			let distanceCrossed = document._vectorDist(
				this.gripperTrace[this.gripperTrace.length-1].slice(1),
				this.gripperTrace[0].slice(1)
			);
			return (distanceCrossed >= this.feedbackDistInt) && !this._hasPendingMsg();
		}

	}; // class IGView end
}); // on document ready end
