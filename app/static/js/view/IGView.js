$(document).ready(function () {

	/**
	 * Instruction giver view. Spoken instructions are emitted, guiding a user to choose a specific object.
	 * @param {Socket io connection to the server} modelSocket 
	 * @param {object mapping task index to tasks, in JSON format as accepted by the model} tasks
	 * @param {name of the algorithm to use for an initial instruction, one of ["IA", "RDT"]. Determines the feedback algorithm too.} referenceAlg
	 * @param {identifier of the gripper the instructed user is controlling} gripperId
	 * @param {optional: time (ms) to wait before giving feedback if the user is idle, default: 5000} feedbackTimeInt
	 * @param {optional: distance (blocks) the user has to move the gripper before feedback is given, default: 2} feedbackDistInt
	 */
	this.IGView = class IGView {
		constructor(modelSocket, tasks, referenceAlg, gripperId,
			feedbackTimeInt=10000, feedbackDistInt=2, maxTries=3) {
			// server
			this.socket			= modelSocket;

			// task management
			this.tasks 			= tasks;
			this.currentTask	= -1; // index of current task
			this.currentTarget; // id of the goal object in the current task
			this.currentObjects; // store objects for performance reasons.
			this.gripperId		= gripperId; // identifier of the gripper that is tracked
			this.config; 				// model configuration
			this.maxTries		= maxTries;
			this.currentTries	= 0;

			// set reference and feedback algorithm according to the given algorithm name
			this._referenceAlg, this._feedbackAlg;
			this.setAlgorithms(referenceAlg);

			// instruction parameters
			this.instrStart		= ["Pick", "Take", "Select", "Get", "Grip"];
			this.generalTypes	= ["object", "shape", "piece"];
			this.properties		= ["shapeLetter", "color", "location"];

			// feedback parameters
			this.feedbackTimeInt	= feedbackTimeInt;
			this.feedbackDistInt	= feedbackDistInt;
			this.lastMsg			= 0; // timestamp of the last message given to the user
			this.targetCoords; // target object coordinates (center of object)
			this.gripperTrace		= new Array(); // track locations since last message: [timestamp, x, y]
			this.feedbackTimeoutId; // stores timeout id to manage timed feedback
			
			this.msgQueue			= new Array(); // audios currently playing or waiting to be played
			this._initSocketEvents();
		}

		// --- Getter ---

		/**
		 * @return number of tasks the instance has been assigned.
		 */
		get nTasks() {
			return Object.keys(this.tasks).length;
		}

		/**
		 * @return next task and increment the counter. If there is no more tasks, return null.
		 */
		get nextTask() {
			return (++this.currentTask) < this.nTasks ? this.tasks[(this.currentTask).toString()] : null;
		}

		/**
		 * @return true if some task has been loaded already
		 */
		get hasStarted() {
			return this.currentTask >= 0;
		}

		/**
		 * @return number of blocks per row on the board. If no config was loaded, returns the default 20
		 */
		get width() {
			return this.config ? this.config.width : 20;
		}

		/**
		 * @return number of blocks per column on the board. If no config was loaded, returns the default 20
		 */
		get height() {
			return this.config ? this.config.height : 20;
		}

		/**
		 * Takes a string and chooses the appropriate class functions for reference generation and
		 * feedback-giving
		 * Logs an error if function could not be found and defaults to IA and simpleFeedback.
		 * @param {string, name of the algorithm for referring expression generation} referenceAlgName
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
					console.log("No (valid) reference algorithm selected. Defaulting to Incremental Algorithm and simple feedback...");
					this.setAlgorithms("IA");
			}
		}

		/**
		 * @return function used to generate referring expressions
		 */
		get referenceAlg() {
			return this._referenceAlg;
		}

		/**
		 * @return function used to generate feedback expressions
		 */
		get feedbackAlg() {
			return this._feedbackAlg;
		}
		
		/**
		 * @param {int < 0, how many logged positions to look back, default:-1} stepsBack
		 * @return penultimate gripper x coordinate, undefined if no coordinate has been logged yet
		 */
		getGripperX(stepsBack=-1) {
			if (this.gripperTrace.length < -stepsBack) {
				return undefined;
			} else {
				// location added last
				return this.gripperTrace[this.gripperTrace.length+stepsBack][1];
			}
		}
		
		/**
		 * @param {int < 0, how many logged positions to look back, default:-1} stepsBack
		 * @return penultimate gripper y coordinate, undefined if no coordinate has been logged yet
		 */
		getGripperY(stepsBack=-1) {
			if (this.gripperTrace.length < -stepsBack) {
				return undefined;
			} else {
				// location added last
				return this.gripperTrace[this.gripperTrace.length+stepsBack][2];
			}
		}

		/**
		 * @return object associated to the given id, else undefined
		 */
		getObj(id) {
			return this.currentObjects[id];
		}

		/**
		 * @return value an object with the given id has for the given property name, undefined if id is unknown or property not defined
		 */
		getObjValue(id, property) {
			if (this.currentObjects[id]) { 
				return this.currentObjects[id][property];
			}
			return undefined;
		}

		// --- socket events --- //

		_initSocketEvents() {
			this.socket.on("update_config", (config) => {
				this.config = config;
			});
			// state was loaded. Start giving instructions
			this.socket.on("update_state", (state) => {
				// only react to this if some task was started
				if (!this.hasStarted) { return; } 
				// get the objects from the model, since the state might differ slightly
				// from the sent task (because of defaults and configuration restrictions). It's best to 
				// synchronize with the model to match the instruction with what is displayed.
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
						if (Object.keys(grippers[this.gripperId]["gripped"]).includes(this.currentTarget)) {
							// target was selected
							this.taskCompleted();	
						} else {
							if (++this.currentTries >= this.maxTries) {
								this.taskCompleted();
							} else {
								// automatically ungrip the piece
								this.socket.emit("grip", {"id": this.gripperId});
								// tell the participant they have to try again
								this._outputMsg("That was incorrect", "feedback");
								this.giveFeedback(true);
							}
						}
						
					} else {
						// the gripper has been moved (-> might trigger feedback)
						// save the new gripper position
						this.gripperTrace.push([Date.now(),
												grippers[this.gripperId].x,
												grippers[this.gripperId].y]);
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
		 * Load the first task and start listening to model updates
		 */
		start() {
			// introduction
			this.welcome();
			// start the task flow
			this.currentTask = -1;
			if (!this._loadTask()) {
				console.log("Error: No task could be loaded at IGView. Passed empty task object?");
				this.goodbye();
			}
		}

		/**
		 * User completed a task. Emit a message to the user, stop updating and try loading the next task.
		 */ 
		taskCompleted() {
			// abort pending messages
			this.abortAllMsgs();
			// pause feedback loop until a new task is started
			this.stopFeedbackTimeout();
			// emit global event for logger to catch
			document.dispatchEvent(new CustomEvent("logSegment", 
				{ detail: { "segmentTitle": this.currentTask,
							"additionalData": { "target": this.currentTarget, "incorrectAttempts": this.currentTries}}}));
			if (!this._loadTask()) {
				this.goodbye();
			}
		}

		/**
		 * If there is another task, post it to the model, then save the objects and target of this task.
		 * @return true if a task was loaded, false if no more tasks are available
		 */
		_loadTask() {
			// load the next (predefined) task
			let task = this.nextTask;
			// task is null if no tasks remain
			if (!task) { return false; }
			// reset the attempts
			this.currentTries = 0;
			// set the goal object
			this.currentTarget = task.target.toString();
			// remember the gripper start position
			this.gripperTrace = [[Date.now(), task.task.grippers[this.gripperId].x, task.task.grippers[this.gripperId].y]];

			// load the task into the model
			this.socket.emit("load_state", task.task);
			return true;
		}

		// --- User communication --- //

		/**
		 * Welcome the user, explain rules, etc.
		 */
		welcome() {
			// welcome the participant
			this._outputMsg("Welcome! I'm Matthew." +
				" Let's pick up some Pentomino pieces together." +
				" The first task is just for warming up before we get to the study");
			// explain the rules
			this._outputMsg("Move around using the arrow keys" +
				" and select an object using space or enter." +
				" You have 3 tries to get the correct piece");
		}

		/**
		 * Thank the user for participating, etc. Dispatch a "tasksCompleted" event.
		 */
		goodbye() {
			this._outputMsg("Thank you for participating. Have a nice day");
			document.dispatchEvent(new Event("tasksCompleted"));
		}

		/**
		 * Emit a full instruction, describing the target piece to the user according to the selected 
		 * algorithm.
		 */
		giveInstruction() {
			// use reference algorithm to generate an instruction, otherwise force feedback 
			let instr = this.referenceAlg ? this.referenceAlg() : this.feedbackAlg(true);
			this._outputMsg(instr, "instruction");
			// give feedback after a set interval, if user doesn't react
			this.startFeedbackTimeout(this.feedbackTimeInt);
		}

		/**
		 * If a feedback algorithm is set, react to the user's progress. Depending on the
		 * algorithm, this might be further information, correction or support.
		 * @param {if set to true, no additional checks will be made, default: false} force
		 */
		giveFeedback(force=false) {
			// try to contruct feedback - returns null if no feedback needed
			let feedback = this.feedbackAlg(force);
			if (feedback) {
				this._outputMsg(feedback, "feedback");
				// give feedback after a set interval, if user doesn't react
				this.startFeedbackTimeout(this.feedbackTimeInt);
			}
		}

		/**
		 * Deliver a message to the user.
		 * @param {string, message to send} msg
		 * @param {type of message, one of ["instruction", "feedback", "meta"], used for log event} type
		 */
		_outputMsg(msg, type="meta") {
			// get the audio: file name is msg in lower case, without spaces and with an .mp3 extension
//			let msgFile = `./resources/audio/${msg.toLowerCase().replaceAll(" ", "")}.mp3`;
//			// for now use dummy audio
//			//let msgFile = "./resources/audio/example_instruction.mp3";
//			let audio = new Audio(msgFile);
//			// keep the audio in the queue until it has been played, this way we have a
//			// reference to it in case we need to abort playing
//			this.msgQueue.push([msg, audio]);
//
//			// if there is no other message currently playing, start this message immediately
//			if (this.msgQueue.length == 1) {
//				// start playing the message as soon as audio is loaded sufficiently
//				audio.oncanplaythrough = function() {
//					// dispatch message event
//					document.dispatchEvent(new CustomEvent("emitMessage", 
//						{ detail: { "type": type, "content": msg, "duration": nextAudio.duration }}));
//					$("#instructions").text(msg);
//					audio.play();
//				};
//			}
//			let thisArg = this;
//			audio.onended = function() {
//				// update the timestamp of the last message delivered to the user
//				thisArg.lastMsg = Date.now();
//				// delete old gripper trace and start tracking again from the recordedlast position
//				thisArg.gripperTrace = thisArg.gripperTrace.slice(-1);
//				// delete the audio from the queue
//				thisArg.msgQueue = thisArg.msgQueue.slice(1);
//				// start the next waiting message
//				if (thisArg._hasPendingMsg()) {
//					// start playing the message as soon as audio is loaded sufficiently
//					let [nextMsg, nextAudio] = thisArg.msgQueue[0];
//					if (nextAudio.readyState >= 2) {
//						// dispatch message event
//						document.dispatchEvent(new CustomEvent("emitMessage", 
//							{ detail: { "type": type, "content": msg, "duration": nextAudio.duration }}));
//						$("#instructions").text(nextMsg);
//						nextAudio.play();
//					} else {
//						nextAudio.oncanplaythrough = function() {
//							// dispatch message event
//							document.dispatchEvent(new CustomEvent("emitMessage", 
//								{ detail: { "type": type, "content": msg, "duration": nextAudio.duration }}));
//							$("#instructions").text(nextMsg);
//							nextAudio.play();
//						};
//					}
//				}
//			}
			
			// WITHOUT AUDIO:
			// temporarily implemented as simply printing to the screen
			// dispatch message event
			document.dispatchEvent(new CustomEvent("emitMessage", 
				{ detail: { "type": type, "content": msg }}));
			$("#instructions").text(msg);
			this.lastMsg = Date.now();
			// delete old gripper trace and start tracking again from the recordedlast position
			this.gripperTrace = this.gripperTrace.slice(-1);
		}
		
		/**
		 * Check if the internal message queue contains pending messages.
		 * @return true if a message is currently playing or waiting to be played
		 */
		_hasPendingMsg() {
			return this.msgQueue.length > 0;
		}
		
		/**
		 * Stop any audio currently playing and delete waiting messages.
		 */
		abortAllMsgs() {
			if (this._hasPendingMsg()) {
				this.msgQueue[0][1].pause();
				this.msgQueue = new Array();
			}
		}

		/**
		 * Give feedback to the user after some time has elapsed. Stop the loop using stopFeedbackTimeout()
		 * @param {time to wait before feedback} delay
		 */
		startFeedbackTimeout(delay) {
			this.stopFeedbackTimeout();
			// start a timer: after set time of no interaction with the user, feedback message is given
			if (this.feedbackAlg) {
				let thisArg = this;
				this.feedbackTimeoutId = setTimeout(async function() {
					// pass argument true so _needFeedback is not checked
					thisArg.giveFeedback(true);
				}, delay);
			}
		}

		/**
		 * Stop giving feedback in regular time intervals
		 */
		stopFeedbackTimeout() {
			if (this.feedbackTimeoutId) { clearTimeout(this.feedbackTimeoutId); }
		}

		// --- Reference generation algorithms --- //

		// --- Incremental Algorithm by E. Reiter & R. Dale --- //

		/**
		 * Construct a reference using the incremental algorithm. 
		 * Algorithm adapted from E. Reiter & R. Dale (1992). See https://aclanthology.org/C92-1038.pdf or
		 * the documentation a description and the full source.
		 */
		IA() {
			// preference order
			// TODO: shapeAny
			let P = this.properties;
			// construct a contrast set: first copy all objects into a set
			let C = new Set(Object.values(this.currentObjects));
			// target piece. Named r here to better match the pseudocode by Reiter & Dale
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

				// check if enough properties have been collected to rule out all contrast objects
				if (C.size == 0) {
					// TODO: always add "shape-letter" here or not?
					return document._randomFromArray(this.instrStart) + " the " + this._verbalizeRE(L);
				}
			}
			// no expression that rules out all contrast objects was found
			console.log("IA: failure")
			return document._randomFromArray(this.instrStart) + " the " + this._verbalizeRE(L);
		}

		/**
		 * @param {property name} prop
		 * @param {value the target object has assigned to the given property} val
		 * @param {contrast set of objects to rule out by the given the property-value pair} contrastSet
		 * @return Array of contrast objects differing to val in the given property
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

		RDT() {
			// Mimicking a 'nested class' here for the notion of a domain - it's really just a function contructing an object
			this.Domain = class {
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
			return document._randomFromArray(this.instrStart) + " " + this.generateRDT();
		}

		/**
		 * Generate a new reference to the current target object, using the current referential space.
		 * (Figure 2: generate)
		 * @param {optional: referent or set of referents to generate a RE for, default: current target} t
		 * @return
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
		 * Restructure the referential space after a reference within D, using the properties of S,
		 * has been made
		 * @param {domain} D
		 * @param {set of property-value pairs} S
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
			this.RS.forEach(domain => {
				if (document.setEquals(domain.ground, Gp)) {
					domain.salience = this._getMaxSalience() + 1;
					return;
				}
			});
			// if no matching domain was found, create a new domain with maximum salience
			let newD = new this.Domain(Gp, Sp, this._getMaxSalience()+1, this._defaultPartition(Gp));
			this.RS.add(newD);
		}

		/**
		 * Create a partition tree structure. 
		 * Iterating throught the properties in the order defined by T,
		 * the set of objects ('ground' of the given domain D) is divided into subsets sharing some
		 * property value, until sets with only one entry each are left.
		 * Newly created domains are added to this instance's RS set.
		 * @param {Domain instance to be further partitioned} D
		 * @param {Array of property names in a preference order} T
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
							// the paper asks to create a default partition here, but this is not necessary
							// unless no more properties are left
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
		 * Create the default partition defined as: def(X) = ("id", X/R_id, new Set())
		 * where X/R_id denotes creating subsets with one element of X each.
		 * @param {set of objects to create a default partition for}
		 * @return partition array: ("id", subsets, focus)
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
		 * @param {SET? of objects to divide} ground
		 * @param {property name for division: each object in 'ground' should have this property} property
		 * @return The partition is realized as an object here, each value found for property maps to a set of objects
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
		 * @param {optional: referent or set of referents to generate a RE for, default: set containing current target} t
		 * @return most salient / specific domain from RS for the current target object
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
						// check if this domain is more salient or is smaller (= more specific) with equal salience
						if (domain.salience > bestDomain.salience) {
							bestDomain = domain;
						} else if (domain.salience == bestDomain.salience && domain.ground.size < bestDomain.ground.size) {
							bestDomain = domain;
						}
					}
				}
			});
			return bestDomain;
		}

// TODO: something wrong here. For positive feedback, "the ..." gets selected where "this one" etc would be more appropriate..
// The problem seems to be that i never update the focus of domains ...
		/**
		 * Find an underspecified domain matching the given domain
		 * Fig. 2 line 3 / underspecified domains defined in Table 1
		 * @param {set of target object(s)} t
		 * @param {most salient / specific domain containing t} D
		 * @param {property-value pairs describing t} S
		 * @return string, underspecified reference to t
		 */
		_matchUnderspecifiedDomain(t, D, S) {
			let plural = (t.size > 1);
			// the cases listed in Table 1 of the paper are checked in decreasing Giveness
			if (document.setEquals(D.partition[2], t)) {
				// case 1 and 2: Focus is {currentTarget}
				// TODO: what is the difference? with the best domain, msd(D) is always true?
				return plural ? "these ones" : "this one";
			}

			// find the partition in d that contains t
			let tPartition;
			for (let partition of Object.values(D.partition[1])) {
				if (document.isSuperset(partition, t)) {
					tPartition = partition;
					break;
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
				// two cases: either target is only partition out of focus or multiple particitions are out of focus
				for (let partition of Object.values(D.partition[1])) {
					D.partition[2].forEach(partitionInFocus => {
						// check whether the partition is NOT in focus AND NOT the target set -> case 6 / 7
						if (!document.setEquals(partition, partitionInFocus) && !document.setEquals(partition, t)) {
							return "another one";
						}
					});
				}
				// no 'out of focus' partition except t was found: case 4/5
				return "the other one";
			} else {
				return "a " + this._verbalizeRE(S, plural);
			}
			// failure case is emitted here since the last case ("a N") is used a default
		}

		// --- REG helper functions used by multiple algorithms --- //

		_findValue(obj, prop) {
			switch(prop) {
				//TODO: shapeAny
				case "shapeLetter":
					return obj.type;
				case "color":
					return obj.color;
				case "location": 
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
				case "hpos":
					// horizontal position relative to the gripper
					if (!this.getGripperX()) {
						return null;
					} else if (obj.x + obj.width <= this.getGripperX()) {
						return "left of";
					} else if (obj.x >= this.getGripperX()) {
						return "right of";
					} else {
						return null;
					}
				case "vpos":
					// vertical position relative to the gripper
					if (!this.getGripperY()) {
						return null;
					} else if (obj.y + obj.height <= this.getGripperY()) {
						return "above";
					} else if (obj.y >= this.getGripperY()) {
						return "below";
					} else {
						return null;
					}
				default:
					console.log(`Error at _findValue(): property ${prop} not implemented`);
					return null;
			}
		}

		/**
		 * Construct a natural language description from collected property-value pairs.
		 * @param {object mapping property names [shapeLetter, color, location] to values} propVals
		 * @param {optional: pass true to produce a plural form, default: false}
		 * @return string containing the values from propVals
		 */
		_verbalizeRE(propVals, plural=false) {
			// property "id" is simply ignored
			let color = "", shape = "", location = "", relLocationH = "", relLocationV = "";
			propVals.forEach(([prop, val]) => {
				switch(prop) {
					case "color":
						color = val;
						break;
					case "shapeLetter":
						shape = val;
						break;
					case "location":
						location = "in the " + val;
						break;
					case "hpos":
						relLocationH = val;
						break;
					case "vpos":
						relLocationV = val;
				}
			});
			// if no shape given, use a generic noun
			shape = shape ? shape : this.generalTypes[Math.floor(Math.random() * this.generalTypes.length)];
			// if two types of locations are used, connect them 
			let conj = location && (relLocationV || relLocationH) ? "of the board and " : "";
			// add the values in a natural-sounding order
			return `${color} ${shape}${plural ? "s" : ""} ${location} ${conj}${relLocationV} ${relLocationH}${(relLocationH || relLocationV) ? " the gripper" : ""}`;
		}

		/**
		 * Get the maximum value of salience any domain in RS has.
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
		 * Dummy feedback algorithm to use for algorithms that don't come with a feedback
		 * mechanism by default. Resorts to giving positive or negative signals when the user
		 * is moving. If the user doesn't act, the reference algorithm is called to re-produce
		 * a referring expression.
		 * @param {if set to true, no additional checks will be made, default: false} force
		 * @return natural language feedback expression or null
		 */
		simpleFeedback(force=false) {
			if (!force && !this._needFeedback()) {
				return null;
			}
			let negFeedback = ["Not this direction", "Not there", "No"];
			let posFeedback = ["Yes, this direction", "Yes, there", "Yeah"];
			// determine what kind of feedback to give
			let type;
			switch(this._lastDirectionToTarget()) {
				case 1:
					// moving towards target: positive feedback
					return document._randomFromArray(posFeedback);
				case -1:
					// moving away from target: negative feedback
					return document._randomFromArray(negFeedback);
				case 0:
					// no recent movement: repeat the RE
					return this.referenceAlg();
			}
		}
		
		/**
		 * Determines what direction in relation to the target the user has been moving recently.
		 * return 1: towards target, -1: away from target, 0: no movement in feedbackTimeInt/2
		 */
		_lastDirectionToTarget() {
			if (this.gripperTrace.length < 2 ||
				this.gripperTrace[this.gripperTrace.length-1][0] - this.gripperTrace[this.gripperTrace.length-2][0] > this.feedbackTimeInt/2) {
				// if the user has not moved in the last feedbackTimeInt/2 ms, no focus seems to be set
				return 0;
			}
			// check if distance to target has been reduced by last movement:
			let lastDist = document._vectorDist(this.gripperTrace[this.gripperTrace.length-2].slice(1), this.targetCoords);
			let currentDist = document._vectorDist(this.gripperTrace[this.gripperTrace.length-1].slice(1), this.targetCoords);
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
		 * Feedback algorithm from:
		 * Denis 2010: Generating Referring Expressions with Reference Domain Theory
		 * (as given in Figure 4)
		 * Feedback is emitted with respect to the current focus on objects from the most salient 
		 * domain containing the target. The internal referential space will be updated with each 
		 * generated feedback.
		 * @param {if set to true, no additional checks will be made, default: false} force
		 * @return natural language feedback expression or null
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
					let newD = new this.Domain(F, D.semanticDesc, D.salience+1, null);
					this._createPartitions(newD, ["hpos", "vpos"]);
				}
				return "Yeah. " + this.generateRDT();
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
		 * Selects from the given domain all objects in front / in moving direction of the gripper.
		 * In the original paper, a different setting is used and visible objects are objects in the same
		 * virtual room as the user. Here, all objects are always visible, so a different assumption is used:
		 * The user focuses on objects they move the gripper towards.
		 * @param {domain to filter for objects in focus} domain
		 * @return set of objects 'in focus'
		 */
		_getObjsInFocus(domain) {
			if (this.gripperTrace.length <= 1) {
				// if the user has not moved, no focus seems to be set
				return new Set();
			} 

			let inFocus = new Set(domain.ground);
			// determine the moving direction (computed using the last two logged locations)
			let horizontalDir = this.getGripperX(-1) - this.getGripperX(-2);
			let verticalDir = this.getGripperY(-1) - this.getGripperY(-2);

			if (horizontalDir == 0 && verticalDir == 0) {
				// if the user has not moved since last message, no focus seems to be set
				return new Set();
			}
			// if a direction is 0, no filters need to be applied
			// otherwise, remove any objects 'behind' the current gripper location (or at the same height/width)
			// filter for horizontal direction
			if (horizontalDir > 0) {
				inFocus.forEach(obj => {
					if (this.getObjValue(obj, "x") + this.getObjValue(obj, "width") - this.getGripperX() < 0) {
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
					if (this.getObjValue(obj, "y") + this.getObjValue(obj, "height") - this.getGripperY() < 0) {
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
		
		// --- Supervised exploration --- //
		/**
		 * Feedback to be used on its own.
		 * Produces instructions relative to the current gripper position.
		 * @param {if set to true, no additional checks will be made, default: false} force
		 * @return natural language feedback expression or null
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
			let justEnteredYRange = inYRange && this.gripperTrace.length > 1 && (this.getGripperY(-2) <= tThreshold || this.getGripperY(-2) >= bThreshold);

			if ((justEnteredXRange && inYRange) || justEnteredYRange && inXRange) {
				// instruct to grip if last user action brought the gripper close to the target
				return document._randomFromArray(this.instrStart) + " this object";
			} else if (justEnteredXRange) {
				// x axis is now correct, y axis not: give instruction for y direction
				return "Stop. " + document._randomFromArray(["Go", "Move"]) + " " + this._yFeedback();
			} else if (justEnteredYRange) {
				// x axis is now correct, y axis not: give instruction for y direction
				return "Stop. " + document._randomFromArray(["Go", "Move"]) + " " + this._xFeedback();
			} else if (force || this._needFeedback()) {
				// special case: instruction follower is ready to grip
				if (inXRange && inYRange) {
					return document._randomFromArray(this.instrStart) + " this object";
				}
				// give feedback if user made some progress or was idle for some time
				// check if the last step went into the right direction
				switch(this._lastDirectionToTarget()) {
					case 1:
						// moving towards target: give positive feedback
						return document._randomFromArray(["Yes, this direction", "Yes, there", "Yeah"]);
					case -1:
						// moving away from target: negative feedback + adjustment
						return "No. " + document._randomFromArray(["Go", "Move"]) + " " +
							((inXRange) ? this._yFeedback() : this._xFeedback());
					case 0:
						// no recent movement: give new adjustment
						return document._randomFromArray(["Go", "Move"]) + " " +
							((inXRange) ? this._yFeedback() : this._xFeedback());
					}
			} else {
				// no feedback triggered
				return null;
			}
		}
		
		/**
		 * @return feedback to the horizontal difference between gripper and target object
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
		 * @return feedback to the vertical difference between gripper and target object
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
		 * Check whether to give feedback to the user at the current time. The decision is
		 * based on the user's progress since the last message.
		 * @return bool, true if feedback should be emitted
		 */
		_needFeedback() {
			// no message has been given to the user yet, so no initial instruction either -> no feedback
			if (this.gripperTrace.length == 0) return false;
			// criteria for feedback:
			// 1. user moved the gripper a predefined distance since last communication
			// 2. no other messages in the queue
			return document._vectorDist(this.gripperTrace[this.gripperTrace.length-1].slice(1), this.gripperTrace[0].slice(1)) >= this.feedbackDistInt &&
				!this._hasPendingMsg();
		}

	}; // class IGView end
}); // on document ready end
