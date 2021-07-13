## - work in progress -

# GOLMI
## - General Objects in Language-driven Manipulation Interfaces -

*GOLM* is a framework for creating abstract representations and interfaces to  *object manipulation* tasks. 

#### Example Usages

* building interactive (2D) interfaces for empirical studies involving e.g. the selection or moving around of objects
* reinforcement learning, e.g. with an agent producing commands from the abstract representation or images
* we intend to incorporate GOLMI into [slurk][slurk] for crowd-sourcing tasks

## Demo

The folder `demo` holds a simple demo of a browser interface showing a board with Pentomino pieces. A user can manipulate a *'gripper'* to grip and move pieces. 

How to start the demo:

1. Make sure the 2 server components are running. If running them locally, simple run `python3 model/model_api.py`, `python3 view/view_api.py in two different terminal tabs. If the components are running elsewhere, you need to update the URLs in `demo/js/pentoDemo.js`.
Note: Currently, unit tests are run at every startup. For these to work, the model API needs to be started **first**! The unit tests will be made optional via command line arguments soon.
2. Open `demo/pentoDemo.html` in a browser. 
3. Press the 'Start' button to begin rendering. You can move the gripper around using the arrow keys and grip using Space or Enter. Use 'Stop' to stop rendering and freeze the current state.

## Architecture

GOLMI is realized as a model-view-controller (MVC) architecture. The tasks of each component and the communication between components is sketched out in the following block diagram:

![Image](./resources/img/block_diagram.png 'Block diagram of the MVC structure')

## APIs

Each API can be run with

```python3 PATH_TO_API.py [-h] [--host HOST] [--port PORT] [--test]```

By default, the model API runs at ```127.0.0.1:5000```, the controller API runs at ```127.0.0.1:5001``` and the view API runs at ```127.0.0.1:5002```. You can easily run multiple instances of an API locally (e.g. for multiple views) by varying the port numbers.

An overview of the API endpoints followed by a more detailed explanation is given below.

![Image](./resources/img/API_endpoints.png 'Overview of the API endpoints')

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
* GET: Fetch the model's configuration. This currently only returns entries considered 'relevant' to views, while entries modifying the model logic are omitted. However, the endpoint could easily be modified to send the full configuration. The keys 'width', 'height' and 'type_config' are returned. 'width' is the number of blocks in horizontal dimension of the game environment / board. 'height' is the number of block in vertical dimension. 'type_config' is a map that defines available object types (e.g. the twelve letters for Pentomino) to block matrices defining an objects shape. The matrices contain 0s and 1s, where a 1 signifies the presence of a block.

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
* POST: Notify the model that gripper movement is to be started, specifying the gripper, the direction and optionally the speed. The model will periodically (frequency is defined in the configuration) attempt to move the gripper until a DELETE request is received. Listening views are notified at each change. The length of each step is defined by the 'speed' key, otherwise the default from the configuration is used. *Request format*: keys 'id', 'dx' and 'dy' are obligatory, 'speed' is optional. Values for 'dx' and 'dy' are usually -1, 0 or 1 to indicate the direction, but any float is possible. The step size could theoretically be modified with these parameters, but keep in mind that the values will be multiplied by the (default) speed in any case, so 'speed' should be used for this purpose. Speed should be a float > 0. *Example*: Start moving to the left: {'id': '1', 'dx': -1, 'dy': 0}
* DELETE: Stop some ongoing gripper movement. *Request format*: the key 'id' is obligatory. *Example*: {'id': '1'}

**/gripper/grip**
*(will soon be updated)*
* POST: Currently, a periodic gripping is started in analogy to the periodic movement, until DELETE is received. This will soon be changed back to a single grip / ungrip being performed with the specified gripper
* DELETE: to be removed
* GET: Returns a map: All grippers of the models are mapped to their gripped objects. The latter is a map again, the keys are the object identifiers, the values objects as specified for the ```/objects``` endpoint. 

## Extending and customizing the framework

### Creating an interface (client-side view)

One of the advantages of a MVC architecture is that different views can be defined to create different presentations of the same underlying data / model. 

A challenge we encountered during the implementation is that interfaces need to be run on the client side in many applications we envision for GOLMI. At the same time, if the model is run on a server (e.g. for 'multiplayer' settings), it has to notify the views of ongoing changes. Therefore, the current solution is having at least *two* remote APIs: the model API, where a controller can send requests to perform state changes, and the view API. The model now notifies the view API and the view API stores the latest updates. 

Each client-side interface has its own view API, and it now needs to periodically query the API for pending updates. Drawing an interface might be implemented as follows: For the initial drawing, the client-side view requests configuration, grippers and objects directly from the model API. After that, it repeatedly checks the view API. If changes happen to the model, the client-side view now obtains all necessary data from the view API and can apply them. The updates will then be automatically deleted at the view API (thus the need for a view API per interface).

### The controller situation

Depending on the set-up, changes to the model might be initiated from different sources: it could be a single player pressing keys in their interface, someone giving spoken instructions to an NLU system or a artificial agent following some algorithm. 

Each of these situations might require different controls, making the need for special controllers. In this repository, two types of controllers are provided, both processing key strokes: First, the Controller API receives requests specifying key events and triggers the appropriate functions at the model API. While this approach is faithful to the MVC architecture, it also brings additional network traffic and slows down the interactions. 

The second approach therefore is to let the controller reside at the client's machine. Instead of sending key events to the controller API, a local controller directly interprets the key codes and makes requests to the model API.

## Misc.

* **Coordinates**: (0,0) is the upper left corner, so y-coordinates increase towards the bottom, x-coordinates increase towards the right


[slurk]: https://clp.ling.uni-potsdam.de/publications/Schlangen-2018.pdf



