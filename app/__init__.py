from flask import Flask

DEFAULT_CONFIG_FILE = "DEFAULT_CONFIG_FILE"


class Experiment:
    """ We use this blueprint wrapper to display on the welcome page """

    def __init__(self, name, ref, blueprint, func_config=None):
        self.name = name
        self.ref = ref
        self.blueprint = blueprint
        self.func_config = func_config

    def register(self, app: Flask):
        app.register_blueprint(self.blueprint)

    def configure(self, app: Flask):
        if self.func_config is not None:
            self.func_config(app)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()


REGISTRY: list[Experiment] = []
