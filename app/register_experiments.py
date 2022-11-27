from app import REGISTRY, Experiment
from app.welcome import welcome
from app.pentomino import pentomino
from app.slurk import slurk


def register_app(app):
    # The welcome page (will automatically list
    # all experiments appended to REGISTRY)
    REGISTRY.append(Experiment("Welcome", "/", welcome.welcome_bp))
    # The demo experiment (you can comment this out, if you dont need it)
    REGISTRY.append(
        Experiment(
            "slurk",
            "/slurk/",
            slurk.slurk,
            slurk.apply_config_to
        )
    )

    REGISTRY.append(
        Experiment(
            "Pentomino",
            "/pentomino/",
            pentomino.pentomino_bp,
            pentomino.apply_config_to
        )
    )
    # Your custom experiments come here (uncomment and adjust the next line)
    # REGISTRY.append(
    #     Experiment(
    #         "MyExp",
    #         "/myexp/",
    #         myexp.myexp_bp,
    #         myexp.apply_config_to
    #     )
    # )

    for experiment in REGISTRY:
        experiment.register(app)
        experiment.configure(app)
