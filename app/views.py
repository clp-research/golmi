from app import app
from flask import render_template, request, abort
import json
from time import time_ns
import os

# directory to store logs to
LOG_DIR = app.config["RECORDINGS"]
# directory that stores publicly available logs for replays
# for now, just use the log storage
REPLAY_DIR = app.config["RECORDINGS"]

# --- define routes --- #


@app.route("/", methods=["GET"])
def index():
    """
    Interactive interface.
    """
    return render_template("index.html")


@app.route("/demo", methods=["GET"])
def demo():
    return render_template("demo.html")


@app.route("/pento_fractions/record", methods=["GET"])
def pento_fractions_record():
    return render_template("pento_fractions/pento_fractions_record.html")


@app.route("/pento_fractions/replay", methods=["GET"])
def pento_fractions_replay():
    return render_template("pento_fractions/pento_fractions_replay.html")


@app.route("/logs", methods=["POST"])
def post_logs():
    if not request.data or not request.is_json:
        abort(400)
    json_data = request.json
    # as a filename that
    # (1) can not be manipulated by a client
    # (2) has a negligible chance of collision
    # a simple timestamp is used
    filename = str(time_ns()) + ".json"
    # check if "data_collection" directory exists, create if necessary
    if not os.path.exists(LOG_DIR):
        os.mkdir(LOG_DIR)
    file = open(os.path.join(LOG_DIR, filename), encoding="utf-8", mode="w")
    file.write(json.dumps(json_data, indent=2))
    file.close()
    return "0", 200


@app.route("/logs/<string:logfile>", methods=["GET"])
def get_logs(logfile):
    """Retrieve a log in json format.

    @param logfile  name of the log file to retrieve
    """
    # Protection against directory traversal attacks:
    # Compare the user input against a whitelist of permitted file names. We
    # assume all files in the directory are accessible here
    if logfile in os.listdir(REPLAY_DIR):
        # send the content
        with open(os.path.join(REPLAY_DIR, logfile), encoding="utf-8") as f:
            tasks = f.read()
        return json.loads(tasks)
    else:
        # Return "not found" because resource does not exist or is out of range
        # for this endpoint (stays hidden from unauthorized users)
        abort(404)
