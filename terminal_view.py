import argparse
import copy
from datetime import datetime
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

    def setup(self):
        self.call_backs()
        self.socket.connect(self.address, auth={"password": self.auth})

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
            self.object_grid = Grid.create_from_config(self.config)
            self.target_grid = Grid.create_from_config(self.config)

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
        self.object_grid.clear_grid()
        self.target_grid.clear_grid()

        for idn, dict_obj in self.state["objs"].items():
            o = Obj.from_dict(idn, dict_obj, self.config.type_config)
            # object constructor saves standard block matrix
            # replace it with the one received from the model
            o.block_matrix = dict_obj["block_matrix"]
            self.object_grid.add_obj(o)

        for idn, dict_obj in self.state["targets"].items():
            o = Obj.from_dict(idn, dict_obj, self.config.type_config)
            o.block_matrix = dict_obj["block_matrix"]
            self.target_grid.add_obj(o)
        print("OBJECTS\n")
        print(self.object_grid)
        # print("-"*(2*len(self.object_grid.grid) + 1))
        # print("TARGETS\n")
        # print(self.target_grid)

    def run(self):
        self.setup()
        self.socket.call("join", {"room_id": self.room})
        # self.socket.emit("random_init", {
        #     "n_objs": 10,
        #     "n_grippers": 1,
        #     "random_gr_position": False,
        #     "obj_area": "all",
        #     "target_area": "bottom"
        # })

    def disconnect(self):
        self.socket.emit("disconnect")
        self.socket.disconnect()

    def emit(self, *args, **kwargs):
        self.socket.emit(*args, **kwargs)

    def save_history(self):
        time_string = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
        filename = Path(f"{time_string}.pckl")
        with open(filename, "wb") as ofile:
            pickle.dump(self.history, ofile)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("room_id", action="store", help="room to join")
    args = parser.parse_args()

    client = PyClient("http://localhost:5000", AUTH, args.room_id)
    client.run()
    time.sleep(1)

    actions = {"plot": client.plot, "save": client.save_history}

    options = ", ".join(actions.keys())

    while True:
        command = input(f"Input: ({options})\n> ")
        if command in {"q", "exit"}:
            client.disconnect()
            break
        elif command in actions:
            f = actions[command]
            f()


if __name__ == "__main__":
    main()
