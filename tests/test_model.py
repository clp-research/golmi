from pathlib import Path
import unittest

from model.model import Model
from model.config import Config
from app.app import app, DEFAULT_CONFIG_FILE


class FakeSocket:
    """
    we are not testing socket connection here
    and do not need a real socket
    """
    def emit(self, *args, **kwargs):
        pass


class Test(unittest.TestCase):
    """
    tests on model
    """
    config = Path(app.config[DEFAULT_CONFIG_FILE])

    def get_model(self):
        return Model(
            Config.from_json(self.config),
            FakeSocket(),
            "TestRoom"
        )

    def test_add_gripper(self):
        model = self.get_model()
        model.add_gr(100)

        # model should have one gripper
        self.assertEqual(len(model.state.grippers), 1)

    def test_remove_gripper(self):
        model = self.get_model()
        model.add_gr(100)

        model.remove_gr(100)
        self.assertEqual(len(model.state.grippers), 0)

    def test_start_gripping(self):
        model = self.get_model()
        model.add_gr(100)

        model.start_gripping(100)

        # a gripping loop should be present in the
        # running_loops dictionary of the model
        # and has a value which is not None
        self.assertTrue(
            model.running_loops["grip"][100] is not None
        )

    def test_stop_gripping(self):
        model = self.get_model()
        model.add_gr(100)

        model.start_gripping(100)
        model.stop_gripping(100)

        # a gripping loop should be present in the
        # running_loops dictionary of the model
        # and has a value which is None
        self.assertTrue(
            model.running_loops["grip"][100] is None
        )
