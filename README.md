## - work in progress -

# GOLMI
## - General Objects in Language-driven Manipulation Interfaces -

*GOLMI* is a framework for creating abstract representations and interfaces to  *object manipulation* tasks.
It is built on Flask and Flask-SocketIO. 

#### Example Usages as a rendering library

Install golmi into your projects python environment. 

1. Download or clone golmi (and unpack it)
2. Go into the root folder and run `pip install .`

#### Example Usages as a standalone server

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

[slurk]: https://clp.ling.uni-potsdam.de/publications/Schlangen-2018.pdf
