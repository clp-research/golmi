from app import REGISTRY, Experiment
from app.welcome import welcome
from app.descrimage import descrimage

def register_app(app):
    # The welcome page (will automatically list
    # all experiments appended to REGISTRY)
    REGISTRY.append(Experiment("Welcome", "/", welcome.welcome_bp))
    # Your custom experiments come here (uncomment and adjust the next line)
    REGISTRY.append(
        Experiment(
            "Descrimage",
            "/descrimage/",
            descrimage.descrimage_bp,
            descrimage.apply_config_to
        )
    )

    for experiment in REGISTRY:
        experiment.register(app)
        experiment.configure(app)
