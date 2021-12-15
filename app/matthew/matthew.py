from app import app
from flask_cors import cross_origin
from flask import render_template, Blueprint, abort
import json
import os
from app import DEFAULT_CONFIG_FILE

DATA_COLLECTION = "matthew_DATA_COLLECTION"
TASKS = "matthew_TASKS"
AUDIO = "matthew_AUDIO"


def apply_config_to(app):
    """ define global config parameters """
    app.config[DEFAULT_CONFIG_FILE] = "app/matthew/static/resources/config/pentomino_config.json"
    app.config[DATA_COLLECTION] = "app/matthew/static/resources/data_collection"
    app.config[AUDIO] = "app/matthew/static/resources/audio"


matthew_bp = Blueprint('matthew_bp', __name__,
                       template_folder='templates',
                       static_folder='static',
                       url_prefix="/matthew")


@cross_origin
@matthew_bp.route("/", methods=["GET"])
def matthew():
    return render_template("matthew.html")


@cross_origin
@matthew_bp.route("/get_tasks/<string:taskname>", methods=["GET"])
def tasks(taskname):
    """Func: tasks
    Retrieve tasks in json format.

    Params:
    taskname - name of the task set to load, one of: ['ba_tasks']
    """
    # tasks are saved in JSON format in a server-side file
    savepath = "app/matthew/static/resources/tasks"
    if taskname == "ba_tasks":
        file = open(os.path.join(savepath, "ba_tasks.json"), mode="r", encoding="utf-8")
        tasks = file.read()
        file.close()
        return json.dumps(tasks)
    else:  # Not Found
        abort(404)
