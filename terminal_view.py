import argparse
import copy
from datetime import datetime
import json
from pathlib import Path
import pickle
import socketio
import time

from app.app import AUTH

from model.grid import Grid
from model.config import Config
from model.obj import Obj


class PyClient:
    def __init__(self, address, auth, room):
        self.socket = socketio.Client()
        self.address = address
        self.auth = auth
        self.room = room
        self.history = list()

    def save(self):
        if len(self.history) == 0 or self.state != self.history[-1]:
            self.history.append(copy.deepcopy(self.state))

    def call_backs(self):
        @self.socket.on("joined_room")
        def receive(data):
            pass

        @self.socket.on("update_config")
        def update_config(data):
            self.config = Config.from_dict(data)

        @self.socket.on("update_state")
        def update_state(data):
            self.state = data
            self.save()

        @self.socket.on("update_objs")
        def update_objs(data):
            self.state["objs"] = data
            self.save()

        @self.socket.on("update_grippers")
        def update_grippers(data):
            self.state["grippers"] = data

            for gripper in data.values():
                if gripper["gripped"] != None:
                    for idn, obj in gripper["gripped"].items():
                        self.state["objs"][idn] = obj

            self.save()

    def plot(self):
        object_grid = Grid.create_from_config(self.config)
        target_grid = Grid.create_from_config(self.config)

        for idn, dict_obj in self.state["objs"].items():
            o = Obj.from_dict(idn, dict_obj, self.config.type_config)
            # object constructor saves standard block matrix
            # replace it with the one received from the model
            o.block_matrix = dict_obj["block_matrix"]
            object_grid.add_obj(o)

        for idn, dict_obj in self.state["targets"].items():
            o = Obj.from_dict(idn, dict_obj, self.config.type_config)
            o.block_matrix = dict_obj["block_matrix"]
            target_grid.add_obj(o)
        # print("OBJECTS\n")
        print(object_grid)
        # print("-"*(2*len(self.object_grid.grid) + 1))
        # print("TARGETS\n")
        # print(target_grid)

    def run(self):
        self.call_backs()
        self.socket.connect(self.address, auth={"password": self.auth})
        self.socket.call("join", {"room_id": self.room})

    def random_init(self, random_config):
        self.socket.emit("random_init", random_config)

    def load_config(self, config):
        self.socket.emit("load_config", config)

    def update_config(self, config):
        self.socket.emit("update_config", config)

    def disconnect(self):
        self.socket.emit("disconnect")
        self.socket.disconnect()

    def emit(self, *args, **kwargs):
        self.socket.emit(*args, **kwargs)

    def save_history(self):
        time_string = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
        filename = Path(f"{time_string}.pckl")
        with open(filename, "wb") as ofile:
            to_save = {"states": self.history, "config": self.config.to_dict()}
            pickle.dump(to_save, ofile)


def main():
    # get arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("room_id", action="store", help="room to join")
    subparsers = parser.add_subparsers(dest="subparser")
    
    # monitor option
    monitor = subparsers.add_parser(
        "monitor",
        help="monitor room"
    )

    # random init
    random_init = subparsers.add_parser(
        "random-init",
        help="load configuration from file"
    )
    random_init.add_argument("path", action="store")

    # update config
    update_config = subparsers.add_parser(
        "update-config",
        help="load configuration from file"
    )
    update_config.add_argument("path", action="store")

    # load_config
    load_config = subparsers.add_parser(
        "load-config",
        help="load configuration from file"
    )
    load_config.add_argument("path", action="store")

    args = parser.parse_args()

    # start client
    client = PyClient("http://localhost:5000", AUTH, args.room_id)
    client.run()
    time.sleep(1)

    actions = {
        "plot": client.plot,
        "save": client.save_history,
    }

    options = ", ".join(actions.keys())

    arg_actions = {
        "load-config": client.load_config,
        "update-config": client.update_config,
        "random-init": client.random_init,
    }

    if args.subparser == "monitor":
        while True:
            command = input(f"Options: {options}, exit\n> ")

            # close terminal view
            if command in {"q", "exit"}:
                client.disconnect()
                break

            # input without argument
            elif command in actions:
                f = actions[command]
                f()

    elif args.subparser in arg_actions.keys():
        with open(Path(args.path), "r", encoding="utf-8") as infile:
            config = json.load(infile)

        print(args.subparser)
        function = arg_actions[args.subparser]
        time.sleep(1)
        function(config)
        time.sleep(1)
        client.disconnect()


if __name__ == "__main__":
    main()
