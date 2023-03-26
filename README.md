# GOLMI
## - General Objects in Language-driven Manipulation Interfaces -

*GOLMI* is a framework for creating abstract representations and interfaces to  *object manipulation* tasks.
It is built on Flask and Flask-SocketIO. 


## Install

### Quickstart:
* install [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
* cd into the root directory of this repository
* create a new environment with python 3.9
```
conda create -n golmi python=3.9
```

* activate the new environment
```
conda activate golmi
```

* install the requirements from `requirements.txt`

```
pip install -r requirements.txt
```

Now you can run `python run.py` and access the frontend at `http://127.0.0.1:5000/`

### Docker
You can also start a server using docker, simply run `bash run.sh`

### Example Usages as a rendering library

Install golmi into your projects python environment. 

1. Download or clone golmi (and unpack it)
2. Go into the root folder and run `pip install .`

### Example Usages as a standalone server

* building interactive (2D) interfaces for empirical studies involving e.g. the selection or moving around of objects
* reinforcement learning, e.g. with an agent producing commands from the abstract representation or images
* we intend to incorporate GOLMI into [slurk][slurk] for crowd-sourcing tasks

## Demo

The `/pentomino` endpoint offers a simple demo of a browser interface showing a board with Pentomino pieces. A user can manipulate a *'gripper'* to grip and move pieces. 

How to start the demo:

* (Activate your virtual environment, if using one)
* Run the server: `python run.py [-h] [--host HOST] [--port PORT]`. By default, it will run on `http://localhost:5000/`
* Navigate to  `http://127.0.0.1:5000/pentomino/` in a browser. 
* Press the 'Start' button to begin rendering. You can move the gripper around using the arrow keys and grip using Space or Enter. Use 'Stop' to stop rendering and freeze the current state.

[slurk]: https://clp.ling.uni-potsdam.de/publications/Schlangen-2018.pdf
