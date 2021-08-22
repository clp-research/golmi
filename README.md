## - work in progress -

# GOLMI
## - General Objects in Language-driven Manipulation Interfaces -

*GOLMI* is a framework for creating abstract representations and interfaces to  *object manipulation* tasks.
It is built on Flask and Flask-SocketIO. 

#### Example Usages

* building interactive (2D) interfaces for empirical studies involving e.g. the selection or moving around of objects
* reinforcement learning, e.g. with an agent producing commands from the abstract representation or images
* we intend to incorporate GOLMI into [slurk][slurk] for crowd-sourcing tasks

## Demo

The folder `demo` holds a simple demo of a browser interface showing a board with Pentomino pieces. A user can manipulate a *'gripper'* to grip and move pieces. 

How to start the demo:

(0. Activate your virtual environment, if using one)
1. Install python dependencies: `pip install -r requirements.txt`
2. Run the server: `python run.py [-h] [--host HOST] [--port PORT] [--test]`. Per default, it will run on `http://localhost:5000/`
3. Navigate to  `http://localhost:5000/demo` in a browser. 
4. Press the 'Start' button to begin rendering. You can move the gripper around using the arrow keys and grip using Space or Enter. Use 'Stop' to stop rendering and freeze the current state.

## Architecture

GOLMI is realized as a model-view-controller (MVC) architecture. The tasks of each component and the communication between components is sketched out in the following block diagram:

![Image](./resources/img/block_diagram.png 'Block diagram of the MVC structure')

Communication between server and client is realized through SocketIO. The events exchanged are described below.

## Events


### View API

**/updates**
* POST: Endpoint for the model to send updates.  
The updates will be stored until another request to GET or DELETE is made. If an update arrives for one of the keys ('objs', 'grippers', 'config') while another for the same key is still pending, the data will be overwritten. 
*Request format:* Each update optionally has the keys 'objs', 'grippers' and/or 'config'. 'objs' and 'grippers' map to a dictionary of object identifiers and the corresponding object / gripper details. 'config' simply contains maps to true if the configuration was changed. This is because in most cases, the view needs to be reloaded completely at a configuration update.
*Example:* Here, an update was made to the gripper:
 ```{'grippers': {'1': {'type': 'gripper', 'x': 7.5, 'y': 5.5, 'width': 1, 'height': 1, 'rotation': 0, 'mirrored': 0, 'color': 'blue', 'gripped': {'2': {'type': 'F', 'x': 5, 'y': 3, 'width': 5, 'height': 5, 'rotation': 90, 'mirrored': 90, 'color': 'yellow'}}}}}```
* GET: Endpoint for the client-side view code to fetch any pending updates. A dictionary in the same form as described for POST is returned, summarizing any updates to make in a view. Internally, the updates are deleted.
* DELETE: Delete any stored updates. This can be used to clear the API storage when a new state is loaded.

### (GripperKey)Controller

*This is just one option for a controller module and has proven to be slower because of the additional network traffic. For local / client-side controller modules, see below.*

This example controller receives key events and requests gripper changes in attached models.

**/attach-model**
* POST: Endpoint to attach a model URL and a specific gripper to this controller. Multiple model-gripper pairs can be attached. No check is made whether the requested model and gripper exist!
*Request format:* Keys 'url' and 'id' are compulsory. URL is a string in the format 'HOST:PORT'. ID is the model's internal name of a gripper, as returned by the respective model API endpoints.
*Example:* {'url': '127.0.0.1:5000', 'id': '1'}
* DELETE: If a model URL and a gripper identifier are sent, the model-gripper pair is removed and will no longer be affected by keyboard events. If only a model URL is given, all grippers associated with this model are removed. If the requested model or model-gripper pair are not currently attached, status code 400 is returned.
*Example:* {'url': '127.0.0.1:5000'}

**/key-pressed/<int: key-code>**
* POST: Endpoint to send keyboard events to. If a function is assigned to the corresponding key code, changes will be requested to all subscribed grippers. Otherwise, status code 404 is returned.  *Example:* If the space bar was pressed, POST to /key-pressed/32 *Assigned functions*: 

| key code | key | assigned function |
| --- | --- | --- |
| 13 | enter | grip |
| 32 | space bar | grip |
| 37 | arrow left | move left|
| 38 |arrow up | move up |
| 39 | arrow right | move right |
| 40 | arrow down | move down |


### Model API

**/attach-view**
* POST: Send the URL of a view API that should be notified of model changes. When changes are made to the state or configuration, the model will attempt to send the updated data to an ```/updates``` endpoint. It is not checked whether a view actually resides at the given address. *Request format:* Key 'url' is compulsory. URL is a string in the format 'HOST:PORT'.
*Example:* {'url': '127.0.0.1:5002'}
* DELETE: Stop notifications to some view API. The URL will be removed from the model's view list, if present -- if the requested view was not currently attached, status code 400 is returned. *Request format:* Key 'url' is compulsory. URL is a string in the format 'HOST:PORT'.
*Example:* {'url': '127.0.0.1:5002'}

**/config**
* POST: *not yet implemented.* Endpoint to send a configuration in JSON format to the model
* GET: Fetch the model's configuration. This currently returns the keys 'width', 'height', 'actions', 'rotation_step', 'colors' and 'type_config'. The following table summarizes the configuration parameters:

| parameter | type | description | example |
| --- | --- | --- | --- |
|width|int| number of blocks in horizontal dimension of the game environment / board | 20 | 
|height|int| number of blocks in vertical dimension | 20 | 
|actions|array / list of str|types of manipulation allowed by the model| \["move", "rotate", "flip"\]| 
|rotation_step|int|angle change for a single rotation action|90| 
|colors|array / list of str|available object colors| \["red", "black", "blue"\] |
|type_config| map: str -> list of lists / array of arrays|map that defines available object types (e.g. the twelve letters for Pentomino) to block matrices defining an object's shape. The matrices contain 0s and 1s, where a 1 signifies the presence of a block| {	"F": [ [0,0,0,0,0], [0,1,1,0,0], [0,0,1,1,0], [0,0,1,0,0], [0,0,0,0,0] ], "I": [ [0,0,1,0,0], [0,0,1,0,0], [0,0,1,0,0], [0,0,1,0,0], [0,0,1,0,0]]}

**/state**
* POST: Initialize a new model state. One of more grippers and one or more objects can be defined. The model will attempt to parse the data, overwrites its internal state and notifies any listening view. *Request format:* The keys 'objs' and 'grippers' must be defined and assigned a (possibly empty) map. Both the object and gripper map match object ids to object info. Obligatory and optional keys for object and gripper entries are summarized in the table below. *Example:* ```{
		"grippers": {
			"1": {
				"x": 5.5,
				"y": 5.5,
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
	}```

|Object class | optional? | key | possible values |
| --- | --- | --- | --- |
|**objs** | no | 'type' | string: type name, must be specified in type_config in the configuration |
| | no | 'x' | float: should be within the interface dimensions |
| | no | 'y' | float: should be within the interface dimensions |
| | no | 'width' | float: horizontal size of the object in blocks |
| | no | 'height' | float: horizontal size of the object in blocks |
| | yes | 'color' | string: defined CSS color string |
| | yes | 'rotation' | int: 0-359 angle of the object with respect to the base position defined in type_config |
| | yes |  'mirrored' | bool: true if the object is flipped once with respect to the base position defined in type_config. Might not have a visible effect depending on the shape |
|**grippers** | no | 'x' | float: should be within the interface dimensions |
| | no | 'y' | float: should be within the interface dimensions |
| | yes | 'gripped' | id of the gripped object or null if no object is gripped |
| | yes | 'color' | string: defined CSS color string |
| | yes | 'width' | float: horizontal size of the object in blocks |
| | yes | 'height' | float: horizontal size of the object in blocks |

* DELETE: Reset the model to an empty state (i.e. without any grippers or objects). Subscribed views will be notified.

**/objects**
* GET: Returns all objects in the model. The identifier of each object is assigned a map that specifies the keys 'type', 'x', 'y', 'width', 'height', 'rotation', 'mirrored' and 'color'.

**/gripper**
* GET: Returns all grippers in the model. The identifier of each gripper is assigned a map that specifies the same keys as for object plus 'gripped'. 'gripped' maps to null or the object identifier and details of a gripped object (same keys as given at the /objects endpoint). 'type' is always 'gripper' here.

**/gripper/position**
* POST: Notify the model that gripper movement is to be started, specifying the gripper, the direction and optionally the step size. Listening views are notified at each change. The length of each step is defined by the 'step_size' key, otherwise the default from the configuration is used. *Request format*: keys 'id', 'dx' and 'dy' are obligatory, 'step_size' and 'loop' are optional. Values for 'dx' and 'dy' are usually -1, 0 or 1 to indicate the direction, but any float is possible. The step size could theoretically be modified with these parameters, but keep in mind that the values will be multiplied by the (default) step size in any case, so 'step_size' should be used for this purpose. Step size should be a float > 0. 'loop' is a Boolean signifying whether the movement should be executed as a continuous or one-time action (more details in 'One-time vs. looped gripper actions'). *Example*: Start moving to the left: {'id': '1', 'dx': -1, 'dy': 0}
* DELETE: Stop some ongoing gripper movement (if a looped movement was started before). *Request format*: the key 'id' is obligatory. *Example*: {'id': '1'}

**/gripper/grip**
* POST: Attempt to grip with a specified gripper, of ungrip if it is already holding some object. *Request format*: 'id' is obligatory, 'loop' is optional. 'id' specifies the gripper to use. 'loop' is a Boolean signifying whether the gripping should be executed as a continuous or one-time action (more details in 'One-time vs. looped gripper actions'). *Example*: {'id': '1', 'loop':true}
* DELETE: Stop some ongoing gripping action (if a looped gripping was started before): *Request format*: 'id' is obligatory. *Example*: {'id': '1'}
* GET: Returns a map: All grippers of the models are mapped to their gripped objects. The latter is a map again, the keys are the object identifiers, the values objects as specified for the ```/objects``` endpoint. 

**/gripper/rotate**
* POST: Attempt to rotate the object held by a specified gripper to the left or right. *Request format*: 'id' and 'direction' are obligatory, 'step_size' and 'loop' are optional. 'id' specifies the gripper to use. 'direction' should be -1 for leftwards movement and 1 for rightwards movement. The turning angle is determined by the model's configuration, unless step_size is used. 'step_size' denotes the turning angle in degrees, so it should be an int > 0 and < 360. Note that views might not be able to depict all angles. 'loop' is a Boolean signifying whether the rotation should be executed as a continuous or one-time action (more details in 'One-time vs. looped gripper actions'). *Example*: {'id': '1', 'direction': -1, 'step_size': 90, 'loop': true}
* DELETE: Stop some ongoing rotation action (if a looped rotation was started before): *Request format*: 'id' is obligatory. *Example*: {'id': '1'}

**/gripper/flip**
* POST: Attempt to flip/mirror the object held by a specified gripper. *Request format*: 'id' is obligatory, 'loop' is optional. 'id' specifies the gripper to use. 'loop' is a Boolean signifying whether the flipping should be executed as a continuous or one-time action (more details in 'One-time vs. looped gripper actions'). *Example*: {'id': '1'}
* DELETE: Stop some ongoing flipping action (if a looped flip was started before): *Request format*: 'id' is obligatory. *Example*: {'id': '1'}


## Extending and customizing the framework

### Creating an interface (client-side view)

One of the advantages of a MVC architecture is that different views can be defined to create different presentations of the same underlying data / model. 

A challenge we encountered during the implementation is that interfaces need to be run on the client side in many applications we envision for GOLMI. At the same time, if the model is run on a server (e.g. for 'multiplayer' settings), it has to notify the views of ongoing changes. Therefore, the current solution is having at least *two* remote APIs: the model API, where a controller can send requests to perform state changes, and the view API. The model now notifies the view API and the view API stores the latest updates. 

Each client-side interface has its own view API, and it now needs to periodically query the API for pending updates. Drawing an interface might be implemented as follows: For the initial drawing, the client-side view requests configuration, grippers and objects directly from the model API. After that, it repeatedly checks the view API. If changes happen to the model, the client-side view now obtains all necessary data from the view API and can apply them. The updates will then be automatically deleted at the view API (thus the need for a view API per interface).

### The controller situation

Depending on the set-up, changes to the model might be initiated from different sources: it could be a single player pressing keys in their interface, someone giving spoken instructions to an NLU system or a artificial agent following some algorithm. 

Each of these situations might require different controls, making the need for special controllers. In this repository, two types of controllers are provided, both processing key strokes: 

First, the controller API receives requests specifying key events and triggers the appropriate functions at the model API. While this approach is faithful to the MVC architecture, it also brings additional network traffic and slows down the interactions. A small demo of what requests to send the controller API from the client-side interface can be found in ```demo/js/controller/APIKeyController.js```

The second approach therefore is to let the controller reside at the client's machine. Instead of sending key events to the controller API, a local controller directly interprets the key codes and makes requests to the model API. This variant is included in the ```demo/pentoDemo.html``` interface. The relevant controller class is defined in ```demo/js/controller/LocalKeyController.js```


### *One-time* vs. *looped* gripper actions
For all gripper actions (move, rotate, flip, grip) there are two versions that can be used: firstly, for a *one-time* action, simply make a POST request to the appropriate endpoint. The model is requested to execute the action exactly once, e.g. move the gripper one unit or flip the gripped object. Secondly, a *looped* action is triggered by POSTing to the endpoint with the JSON data containing the key *loop* set to *true*. The model will repeatedly attempt to execute the action until the loop is interrupted by a DELETE request to the same endpoint. The loop duration is modified by the configuration.

What type of action to use depends on the setting. It is the job of the controller to send either type of action request.

For instance, in the use case of keyboard controls (as in our ```KeyController```s), there are two options: requesting a one-time action every time a key is pressed or starting a loop once a key is pressed down and stopping it once the key is released. Deciding between the two comes down to estimating user behavior and trying to reduce messages between controller and model accordingly.

In our example, we expect users to prefer continuous actions (holding the key down) for moving the gripper around and rotating a gripped object, while gripping and flipping objects seem to be typical one-time actions.

## Misc.

* **Coordinates**: (0,0) is the upper left corner, so y-coordinates increase towards the bottom, x-coordinates increase towards the right


[slurk]: https://clp.ling.uni-potsdam.de/publications/Schlangen-2018.pdf
