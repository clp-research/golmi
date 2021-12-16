from model.model import Model
from model.config import Config
from flask_socketio import emit, join_room, leave_room, close_room, rooms


class RoomManager:
    """
    Keeps track of and modifies rooms, the related models and joined users.
    """
    def __init__(self, socket, default_config_file):
        self.socket = socket
        self.default_config_file = default_config_file
        # list of clients in a room
        self.room_to_clients = dict()
        # room ids mapped to Model instances
        self.room_to_model = dict()

    def has_room(self, room_id):
        """
        @return True if a room with the given id exists, but False for
            'private' rooms (rooms that use the client's session id as a
            room id), as they don't have a model assigned.
        """
        return self.room_to_model.get(room_id) is not None

    def add_room(self, room_id, config_file=None):
        """
        Adds a room with a new model instance that has the default
        configuration.
        @param room_id identifier of the room for the new model instance
        @param config_file  optional name of file containing a model
            configuration in json format
        """
        if config_file is None:
            config_file = self.default_config_file
        new_model = Model(Config.from_json(config_file), self.socket, room_id)
        self.room_to_model[room_id] = new_model
        self.room_to_clients[room_id] = list()

    def remove_room(self, room_id):
        """
        Delete a room and kick any users left.
        """
        if self.room_to_model.get(room_id):
            self.room_to_model.pop(room_id)
        if self.room_to_clients.get(room_id):
            self.room_to_clients.pop(room_id)
        close_room(room_id)

    def get_model_of_room(self, room_id):
        """
        @return Model instance with the given id or None.
        """
        return self.room_to_model.get(room_id)

    def get_models_of_client(self, client_id):
        """
        @return List of models of all rooms a client joined.
        """
        return [self.get_model_of_room(room_id) for room_id in self.get_rooms_of_client(client_id)]

    def get_rooms_of_client(self, client_id, include_private=False):
        """
        @param client_id   identifier of the user, e.g., their session id
        @param include_private  whether to include the private channel of a
            client (is a room without a model)
        @return List of rooms a client has joined.
        """
        joined_rooms = rooms(client_id)
        if not include_private and client_id in joined_rooms:
            joined_rooms.remove(client_id)
        return joined_rooms

    def add_client_to_room(self, client_id, room_id):
        """
        If the given room exists, add the client to it.
        """
        # make sure the room exists
        if isinstance(self.room_to_clients.get(room_id), list):
            self.room_to_clients[room_id].append(client_id)
            # join the socketio room
            join_room(room_id, sid=client_id)
            # inform everyone in the room
            emit("joined_room",
                 {"room_id": room_id, "client_id": client_id},
                 room=room_id)

    def remove_client(self, client_id, delete_empty_room=True):
        """
        Remove client from all rooms they are in.
        @param client_id    identifier for the client, e.g., their session id
        @param delete_empty_room    remove rooms containing only the client
        """
        for room_id in self.get_rooms_of_client(client_id):
            self.remove_client_from_room(
                client_id, room_id, delete_empty_room=delete_empty_room
            )
        # delete the client's private channel
        close_room(client_id)

    def remove_client_from_room(self, client_id, room_id, delete_empty_room=True):
        """
        Make client leave a room, optionally empty rooms are deleted.
        @param client_id    identifier for the client, e.g., their session id
        @param room_id  identifier for the room
        @param delete_empty_room    remove rooms containing only the client
        """
        # remove client from internal room list
        if isinstance(self.room_to_clients.get(room_id), list) and \
                client_id in self.room_to_clients[room_id]:
            self.room_to_clients[room_id].remove(client_id)
        # leave socket room
        if room_id in rooms(client_id):
            leave_room(room_id, sid=client_id)
        # optional: delete a room with no clients left
        if delete_empty_room and len(self.room_to_clients[room_id]) == 0:
            self.remove_room(room_id)
