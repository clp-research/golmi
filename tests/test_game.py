import unittest

from model.config import Config
from model.game import Game
from model.game_config import GameConfig
from app import DEFAULT_CONFIG_FILE
from app.app import app, socketio, AUTH
from app.pentomino_game import DEFAULT_GAME_CONFIG_FILE

app.config[DEFAULT_CONFIG_FILE] = (
    "app/pentomino/static/resources/config/pentomino_config.json"
)
app.config[DEFAULT_GAME_CONFIG_FILE] = (
    "app/pentomino_game/static/resources/game_config/pentomino_game_config.json"
)


class GameConfigTest(unittest.TestCase):
    def setUp(self):
        self.game_config = GameConfig(
            4,  # number of players
            10,  # number of objects
            {"IG": 1, "IF": 2, "OBSERVER":1},  # role counts
            area_block="all",
            area_target="all",
            create_targets=False,
            random_gr_position=False
        )

    def test_is_valid_role(self):
        for valid_role in ["IG", "IF", "OBSERVER"]:
            self.assertTrue(self.game_config.is_valid_role(valid_role))
        for invalid_role in ["HACKER"]:
            self.assertFalse(self.game_config.is_valid_role(invalid_role))

    def test_set_roles(self):
        # make sure an error is thrown when trying to use an invalid role here
        invalid_counts = {"IG": 10, "HACKER": 1}

        self.assertRaises(KeyError,
                          self.game_config.set_role_counts,
                          invalid_counts)

    # TODO
    def test_get_roles_ignoring_event(self):
        pass

    # TODO
    def test_role_requires_gripper(self):
        pass


class GameTest(unittest.TestCase):
    def setUp(self):
        self.config = Config.from_json(app.config[DEFAULT_CONFIG_FILE])
        self.game_config = GameConfig.from_json(app.config[DEFAULT_GAME_CONFIG_FILE])
        self.room = "test_room"
        self.socket = socketio.test_client(
            app,
            flask_test_client=app.test_client(),
            auth={"password": AUTH}
        )

        self.game = Game(self.config, self.socket, self.room, self.game_config)

    def test_has_started(self):
        self.assertFalse(self.game.has_started())

    def test_autostart(self):
        # add required no. of players
        self.game.add_player("player1", "IG", start_once_full=True)

        self.assertFalse(self.game.has_started())

        self.game.add_player("player2", "IF", start_once_full=True)

        self.assertTrue(self.game.has_started())

    def test_get_players(self):
        player_id = "player1"
        self.game.add_player(player_id, "IG")

        self.assertEqual(self.game.get_number_of_players(), 1)
        self.assertIn(player_id, self.game.get_players())

    def test_get_players_with_role(self):
        player_id = "player1"
        player_role = "IG"
        invalid_role = "HACKER"
        self.game.add_player(player_id, player_role)

        self.assertIn(player_id, self.game.get_players_with_role(player_role))
        self.assertListEqual(list(),
                             self.game.get_players_with_role(invalid_role))

    def test_unassigned_roles(self):
        unassigned_roles = ["IG", "IF"]

        self.assertListEqual(unassigned_roles, self.game.unassigned_roles)

        # use add_player function to assign someone to a role
        player1_role = "IG"
        self.game.add_player("player1", player1_role)
        unassigned_roles.remove(player1_role)

        self.assertListEqual(unassigned_roles, self.game.unassigned_roles)

        # use assign_role function to assign someone to a role
        player2_role = "IF"
        self.game.assign_role("player2", player2_role)
        unassigned_roles.remove(player2_role)

        self.assertListEqual(unassigned_roles, self.game.unassigned_roles)

    def test_add_player(self):
        player_id = "player1"
        player_role = "IG"
        self.game.add_player(player_id, player_role)

        self.assertIn(player_id, self.game.player_roles)
        self.assertEqual(player_role, self.game.player_roles[player_id])

    def test_remove_player(self):
        player_id = "player1"
        player_role = "IG"
        self.game.add_player(player_id, player_role)
        self.game.remove_player(player_id)

        self.assertNotIn(player_id, self.game.player_roles)
        # make sure the player's role was added back to the unassigned
        self.assertIn(player_role, self.game.unassigned_roles)

    def test_add_required_grippers(self):
        player_with_gripper = "with_gripper"
        player_without_gripper = "without_gripper"
        role_with_gripper = "IF"
        role_without_gripper = "IG"
        self.game.add_player(player_with_gripper, role_with_gripper)
        self.game.add_player(player_without_gripper, role_without_gripper)
        self.game.add_required_grippers()

        self.assertIn(player_with_gripper, self.game.player_grippers)
        self.assertNotIn(player_without_gripper, self.game.player_grippers)

    def test_get_skipped_sids(self):
        event_name = "update_grippers"
        skipped_role = "IG"
        skipped_players = ["IG1"]
        non_skipped_role = "IF"
        non_skipped_player = "IF1"
        for player in skipped_players:
            self.game.add_player(player, skipped_role)
        self.game.add_player(non_skipped_player, non_skipped_role)
        skipped_sids = self.game._get_skipped_sids(event_name)

        self.assertListEqual(skipped_players, skipped_sids)
