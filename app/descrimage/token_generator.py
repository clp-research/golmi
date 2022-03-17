import secrets
import string
import time

import socketio

from app.app import AUTH


class Generator:
    def __init__(self, address, auth):
        self.socket = socketio.Client()
        self.address = address
        self.auth = auth

    def callbacks(self):
        @self.socket.on("room_list")
        def get_rooms(data):
            self.taken_rooms = data

    def run(self):
        self.callbacks()
        self.socket.connect(self.address, auth={"password": self.auth})
        self.socket.emit("list_rooms")
        time.sleep(1)
        self.socket.disconnect()

    def generate_random_token(self):
        alphabet = string.ascii_letters + string.digits
        token = "".join(secrets.choice(alphabet) for _ in range(7))
        return token

    def generate(self):
        """
        generate a unique token
        """
        token = self.generate_random_token()
        while token in self.taken_rooms:
            token = self.generate_random_token()
        return {"receiver": f"{token}-1", "giver": f"{token}-2"}


if __name__ == "__main__":
    generator = Generator("http://localhost:5000", AUTH)
    generator.run()
    tokens = generator.generate()
    print("Tokens [instruction receiver == admin]:")
    for key, value in tokens.items():
        print(f"Instruction {key}:\t{value}")
