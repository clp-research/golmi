from flask_cors import cross_origin
from flask import render_template, Blueprint

from app import REGISTRY

welcome_bp = Blueprint('welcome_bp', __name__,
                       template_folder='templates',
                       static_folder='static')


@cross_origin
@welcome_bp.route("/", methods=["GET"])
def welcome():
    return render_template("welcome.html", experiments=REGISTRY)
