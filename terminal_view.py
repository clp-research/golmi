import socketio
import time

from app.app import AUTH

from model.grid import Grid
from model.config import Config
from model.obj import Obj


class PyClient:
    def __init__(self, address, auth):
        self.socket = socketio.Client()
        self.address = address
        self.auth = auth

    def setup(self):
        self.call_backs()
        self.socket.connect(self.address, auth={"password": self.auth})

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
            for idn, dict_obj in data["objs"].items():
                o = Obj.from_dict(idn, dict_obj, self.config.type_config)
                # object constructor saves standard block matrix
                # replace it with the one received from the model
                o.block_matrix = dict_obj["block_matrix"]
                self.object_grid.add_obj(o)

            for idn, dict_obj in data["targets"].items():
                o = Obj.from_dict(idn, dict_obj, self.config.type_config)
                o.block_matrix = dict_obj["block_matrix"]
                self.target_grid.add_obj(o)

    def plot(self):
        print("OBJECTS\n")
        print(self.object_grid)
        print("-"*(2*len(self.object_grid.grid) + 1))
        print("TARGETS\n")
        print(self.target_grid)

    def run(self):
        self.setup()
        self.socket.call("join", {"room_id": "test_room_id"})
        self.socket.emit("random_init", {
            "n_objs": 10,
            "n_grippers": 1,
            "random_gr_position": False,
            "obj_area": "all",
            "target_area": "bottom"
        })

    def emit(self, *args, **kwargs):
        self.socket.emit(*args, **kwargs)


if __name__ == "__main__":
    client = PyClient("http://localhost:5000", AUTH)
    client.run()
    time.sleep(1)
    client.plot()
