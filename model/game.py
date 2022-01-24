"""
Game class:
    - holds players and their roles
    - initializes model once enough players are there
    - makes sure players only receive updates according to their roles
    - attaches grippers
"""
import random

from model.config import Config
from model.game_config import GameConfig
from model.model import Model


class Game(Model):
    def __init__(self, model_config: Config, socket, room,
                 game_config: GameConfig):
        super().__init__(model_config, socket, room)
        self.game_config = game_config
        self.player_roles = dict() # map player to role
        self.player_grippers = dict() # map player to gripper

        self.unassigned_roles = list()
        self.init_unassigned_roles()

        self._has_started = False

    def has_started(self):
        return self._has_started

    def get_number_of_players(self):
        return len(self.player_roles)

    def get_players(self):
        return self.player_roles.keys()

    def get_players_with_role(self, role):
        return [player for player, player_role in self.player_roles.items() if player_role == role]

    def has_enough_players(self):
        return self.get_number_of_players() >= self.game_config.n_players

    def init_unassigned_roles(self):
        for role, count in self.game_config.role_counts.items():
            self.unassigned_roles.extend([role] * count)

    def assign_role_by_name(self, player_id, role_name: str):
        if not self.game_config.is_valid_role_name(role_name):
            raise ValueError(f"Attempting to use unknown role '{role_name}'")
        self._assign_role(player_id,
                          self.game_config.get_role_by_name(role_name))

    def assign_random_role(self, player_id):
        """
        Assign the player a random remaining role.
        """
        if len(self.unassigned_roles) == 0:
            raise RuntimeError("No unassigned roles left")
        random_role = random.choice(self.unassigned_roles)
        self._assign_role(player_id, random_role)

    def _assign_role(self, player_id, role):
        if role not in self.unassigned_roles:
            raise RuntimeError(f"No registrations for role {role} left")
        # Remove any older registration
        if self.player_roles.get(player_id) is not None:
            self.remove_player(player_id)
        self.player_roles[player_id] = role
        self.unassigned_roles.remove(role)

    def get_unassigned_roles(self):
        return self.unassigned_roles

    def add_player(self, player_sid, role_name: str, start_once_full=True):
        """
        Add a player to the game. If the role requires it, assign a gripper
        @param player_sid   socket session id of the player
        @param role_name role name, must be known to GameConfig
        @param start_once_full  Automatically start the game if the required
            number of players is present
        """
        if role_name == "random":
            self.assign_random_role(player_sid)
        else:
            self.assign_role_by_name(player_sid, role_name)
        self._notify_views_privately("update_config",
                                     self.config.to_dict(),
                                     player_sid)
        if start_once_full and self.has_enough_players():
            self.start()

    # TODO: should the game stop if a player leaves?
    def remove_player(self, player_id):
        """
        Remove an associated gripper as well.
        """
        if player_id in self.player_roles:
            # add the now missing role back to the list of unassigned roles
            self.unassigned_roles.append(self.player_roles[player_id])
            self.player_roles.pop(player_id)
        if player_id in self.player_grippers:
            self.remove_gr(self.player_grippers[player_id])
            self.player_grippers.pop(player_id)

    def add_required_grippers(self):
        """
        Add a gripper for each role that requires one and notify the players.
        """
        for player_id, role in self.player_roles.items():
            if GameConfig.role_requires_gripper(role):
                gripper_id = player_id
                self.add_gr(gripper_id)
                self.player_grippers[player_id] = gripper_id
                # notify the socket clients via their private channel
                self._notify_views_privately("attach_gripper",
                                             gripper_id,
                                             player_id)

    def start(self):
        """
        Load a random new model state.
        """
        self.set_random_state(self.game_config.n_objs,
                              0,  # no grippers are generated yet
                              area_block=self.game_config.area_block,
                              area_target=self.game_config.area_target,
                              create_targets=self.game_config.create_targets,
                              random_gr_position=self.game_config.random_gr_position)
        self.add_required_grippers()
        self._has_started = True

    # --- Communicating with views --- #

    def _notify_views(self, event_name, data):
        """
        Notify all listening views of model events (usually data updates)
        @param event_name 	event type (str), e.g. "update_grippers"
        @param data 	serializable data to send to listeners
        """
        # deconstruct update_state into its update components
        if event_name == "update_state":
            self._notify_views("update_objs", data["objs"])
            self._notify_views("update_targets", data["targets"])
            self._notify_views("update_grippers", data["grippers"])
        else:
            skip_sids = self._get_skipped_sids(event_name)
            self.socket.emit(event_name, data, room=self.room, skip_sid=skip_sids)

    def _get_skipped_sids(self, event_name):
        skipped_sids = list()
        skipped_roles = GameConfig.get_roles_ignoring_event(event_name)
        for role in skipped_roles:
            skipped_sids.extend(self.get_players_with_role(role))
        return skipped_sids

    def _notify_views_privately(self, event_name, data, client_sid):
        """
        Notify all listening views of model events (usually data updates)
        @param event_name 	event type (str), e.g. "update_grippers"
        @param data 	serializable data to send to listeners
        @param client_sid   socket session id of the client, is used as a
            private channel name
        """
        self.socket.emit(event_name, data, room=client_sid)
