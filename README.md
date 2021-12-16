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

The `/demo` endpoint offers a simple demo of a browser interface showing a board with Pentomino pieces. A user can manipulate a *'gripper'* to grip and move pieces. 

How to start the demo:

0. (Activate your virtual environment, if using one)
1. Install python dependencies: `pip install -r requirements.txt`
2. Run the server: `python run.py [-h] [--host HOST] [--port PORT]`. By default, it will run on `http://localhost:5000/`
3. Navigate to  `http://localhost:5000/demo` in a browser. 
4. Press the 'Start' button to begin rendering. You can move the gripper around using the arrow keys and grip using Space or Enter. Use 'Stop' to stop rendering and freeze the current state.

For an example of a more complex GOLMI-based interface, see https://github.com/kfriedrichs/golm/tree/ba

## Architecture

GOLMI roughly follows a model-view-controller (MVC) architecture. The tasks of each component and the communication between components is sketched out in the following block diagram:

![Image](./resources/img/MVC_architecture.png 'Block diagram of the MVC structure')

Communication between server and client is realized through SocketIO. The events exchanged are described in the *Events* section below.

## Served endpoints
In addition to the websocket communication between client and server, GOLMI is still a Flask
app processing http requests, which is used to serve interface pages and save 
log data to the server.

The following endpoints are served (see `app/views.py`):

**/** 
* GET: index page, might be the main page for projects building on GOLMI, this repository just serves a placeholder page

**/demo**
* GET: simple demo of a Pentomino interface featuring two objects and a gripper

**/save_log**
* POST: send json-formatted data to log. Data will be saved in the server-side directory `app/static/resources/data_collection`, creating a file with a timestamp as the file name.


## Events 
### client -> server

| event name | source/trigger | data | action |
| --- | --- | --- | --- |
| connect | client connects to server | --- | Assign client to a room / model instance, emit *update_config* and *update_state* to client. |
| disconnect | client disconnects from server | --- | The model associated to
the disconnecting client is deleted on the server to free the memory. |
| load_state | client | state in json format | Initialize model in client's room with sent state. |
| load_config | client | configuration in json format | Model in client's room
loads the configuration. |
| reset_state | client | --- | Resets the current state, i.e. deletes all 
objects and grippers. Leaves the config unchanged. |
| add_gripper | client | optional: gripper id | Add gripper to model if it doesn't exist. If no id was sent, use the client's session id. Emit *attach_gripper* to client |
| remove_gripper | client | optional: gripper id | Delete gripper from model if it exists. If no id was sent, use the client's session id. |
| move | client | params: {"id": str, "dx": int, "dy": int \[, "loop": bool\]}| Start continuous movement or move once with the specified gripper (see *One-time vs. looped gripper actions*). dx and dy must be ints. dx is the x direction (negative = leftwards), dy the y direction (negative = upwards). |
| stop_move | client | params: {"id": str}| Stop continuous movement of the specified gripper. |
| rotate | client | params: {"id": str, "direction": int, \[, "loop": bool, "step_size": int/float\]}| Start continuous rotation or rotate once a gripped object of the specified gripper (see *One-time vs. looped gripper actions*). Negative direction for leftwards, positive direction for rightwards rotation. |
| stop_rotate | client | params: {"id": str}| Stop continuous rotation of the specified gripper. |
| flip | client | params: {"id": str, \[, "loop": bool\]}| Start continuously mirroring or one-time mirroring of a object gripped by the specified gripper (see *One-time vs. looped gripper actions*). Objects are *always flipped along the horizontal axis*. |
| stop_flip | client | params: {"id": str}| Stop continuous mirroring of the specified gripper. |
| grip | client | params: {"id": str \[, "loop": bool\]}| Start continuously gripping or grip once with the specified gripper (see *One-time vs. looped gripper actions*). |
| stop_grip | client | params: {"id": str}| Stop continuous gripping of the specified gripper. |

### server -> client

| event name | source/trigger | data | details / possible actions |
| --- | --- | --- | --- |
| update_config | server | configuration in json format | Client is informed about changes in the model configuration. E.g. a View module might want to re-render the interface. |
| update_state | server | state in json format | Client is informed about an entirely new model state. E.g. a View module might want to re-render the interface. |
| update_grippers | server | map: {gripper-id: gripper} in json format | Client is informed about gripper changes. A json dictionary of all grippers (not just the one associated to the client) is sent, including gripper properties (position etc.) and, if an object is gripped, a map {object-id: object}. |
| update_objs | server | map: {object-id: object} in json format | Client is informed about object changes. A json dictionary of all objects is sent, including relevant object properties (position etc.). |
| attach_gripper | server | gripper id | E.g. used by Controller module to learn the id of a gripper it controls in some socket connection. The id is then used to send gripper changes (*move* etc.). |

### Configuration format

| parameter | type | description | example |
| --- | --- | --- | --- |
|width|int| number of blocks in horizontal dimension of the game environment / board | 20 | 
|height|int| number of blocks in vertical dimension | 20 |
|actions|array / list of str|types of manipulation allowed by the model| \["move", "rotate", "flip"\]| 
|snap_to_grid | bool | true to lock objects to the nearest block at gripper release| false |
|prevent_overlap | bool | true to prohibit any action that would lead to objects overlapping | true |
| move_step | float | step size for object movement, must be higher than 0 and evenly divide the interval between 0 and 1 | 0.25 |
|rotation_step|int|angle change for a single rotation action|90| 
| action_interval | float | frequency of repeating looped actions in seconds, a smaller number smoothes movements but also increases network traffic | 0.1 |
| verbose | bool | true to print additional (debug-) information to the server console after model changes, such as the object grid | false |
| lock_on_target | bool | true to lock objects once they align on the grid with a matching target object | false |
|colors|array / list of str|available object colors, can be color names, e.g., "red", or hex codes, e.g., "#ff0000" | \["red", "black", "blue"\] |
|type_config| map: str -> list of lists / array of arrays|map that defines available object types (e.g. the twelve letters for Pentomino) to block matrices defining an object's shape. The matrices contain 0s and 1s, where a 1 signifies the presence of a block. Block matrices should be square to support rotation. Type names cannot start with an underscore. | {	"F": [ [0,0,0,0,0], [0,1,1,0,0], [0,0,1,1,0], [0,0,1,0,0], [0,0,0,0,0] ], "I": [ [0,0,1,0,0], [0,0,1,0,0], [0,0,1,0,0], [0,0,1,0,0], [0,0,1,0,0]]}

_A note on **colors**_: To Golmi, colors are just strings assigned to objects, but the default is using hex codes. 
The color attribute assigned to objects on the server side is the same as the attribute sent to clients upon
object updates. If a client-side component needs *color names* (and doesn't want to convert the codes itself),
there are easy ways to ensure Golmi is sending names:
    * when using random state initialization: send to Golmi a Config that uses color names
    * without random state initialization: use color names in the pre-generated states you send to Golmi

### State format
The following is an example state, including one gripper and two objects.
```
{
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
}
```

The table below provides details on the object / gripper properties:

| Object class | optional? | key | possible values |
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

## Building an application with GOLMI

### Connection

The first step on the client side is connecting to the server, which might happen in a single statement such as `var socket = io("http://" + MODEL_ADRESS, {auth: PASSWORD })`. (the default password is ` GiveMeTheBigBluePasswordOnTheLeft`and should be changed to restrict access). This triggers a *connect* event on the model side and the app will send an *update_state* and *update_config* event back.

### Creating an interface (client-side view)

Often, applications require some sort of graphic interface which visualizes the model state. For this, a View components needs react to relevant events emitted by the model to stay in sync. It can interpret the state and update data format and translate the updates to the interface. A basic View is provided in `app/static/js/views/View.js`. Drawing functions are stubs, but subscription to socket events and calling the appropriate functions is implemented. 

In the example View, rendering is split into three parts, *background, objects* and *gripper*, in order to minimize re-drawing. It is expected that the background rarely changes, while objects might be manipulated often and the gripper is constantly moved around. The child class `LayerView` implements this idea by drawing on 3 separate, stacked canvas.

### Controllers

Depending on the setup, changes to the model might be initiated from different sources: it could be a single player pressing keys in their interface, someone giving spoken instructions to an NLU system or a artificial agent following some algorithm. 
Each of these situations might require different controls, making the need for special controllers.
 
##### LocalKeyController
As an example, `LocalKeyController.js` is provided. It interprets keyboard events on the client side and translates the key codes into gripper manipulation events sent to the model. The assigned keys are listed below:

| key code | key | assigned function |
| --- | --- | --- |
| 13 | enter | grip |
| 32 | space bar | grip |
| 37 | arrow left | move left|
| 38 | arrow up | move up |
| 39 | arrow right | move right |
| 40 | arrow down | move down |
| 65 | A | rotate left|
| 68 | D | rotate right |
| 83 | S | flip |
| 87 | W | flip |

`LocalKeyController` possesses the function `attachModel()` that needs to be called once to associate a socket connection to the Controller.
Once the model sends an 'attach_gripper' event with the assigned gripper id, the controller uses this id
in subsequent action requests. However, the class is also able to connect to multiple models at once, (but only to one
gripper per model), each would be sent the action requesting events.

### *One-time* vs. *looped* gripper actions
For all gripper actions (move, rotate, flip, grip) there are two versions that can be used, determined by the event's `loop` parameter: firstly, for a *one-time* action, the model is requested to execute the action exactly once, e.g. move the gripper one unit or flip the gripped object. Secondly, a *looped* action will repeatedly attempt to execute the action until the appropriate *stop* (e.g. *stop_move*) event is sent. The loop interval is modified by the configuration.

What type of action to use depends on the setting. It is the job of the controller to send either type of action request.

For instance, in the use case of keyboard controls (as in our ```LocalKeyController```), there are two options: requesting a one-time action every time a key is pressed or starting a loop once a key is pressed down and stopping it once the key is released. Deciding between the two comes down to estimating user behavior and trying to reduce messages between controller and model accordingly.

## Misc.

* **Coordinates**: (0,0) is the upper left corner, so y-coordinates increase towards the bottom, x-coordinates increase towards the right

## Tests
To run all tests:
```
$ python -m unittest
```

To test only parts:
```
$ python -m unittest -k test_socketio
$ python -m unittest -k test_flask_endpoints
```

## Troubleshooting

* The logging class LView.js was named LogView.js before because some adblockers would not load the skript trying to save you from evil data collection. If you encounter similar problems, try turning off the adblock for this site or rename the LogView class into something less suspicious.


[slurk]: https://clp.ling.uni-potsdam.de/publications/Schlangen-2018.pdf
