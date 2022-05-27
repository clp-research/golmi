import argparse
import os.path

from app import register_experiments
from app.app import app, socketio

# --- GOLMi's server --- #
# author: clpresearch, Karla Friedrichs
# usage: python3 run.py [-h] [--host HOST] [--port PORT]
# Runs on host 127.0.0.1 and port 5000 per default

# --- command line arguments ---
parser = argparse.ArgumentParser(
    description="Run GOLMI's model API."
)

parser.add_argument(
    "--host", type=str, default="127.0.0.1",
    help="Adress to run the API on. (Default: %(default)s)"
)

parser.add_argument(
    "--port", type=str, default="5000",
    help="Port to run the API on. (Default: %(default)s)"
)

parser.add_argument(
    "-d", "--collect_dir", type=str, required=True,
    help="Path to the directory containing the states for the data collection."
)

parser.add_argument(
    "--debug", action="store_true", help="If True, show test buttons."
)

if __name__ == "__main__":
    args = parser.parse_args()
    collect_dir = args.collect_dir
    if not os.path.exists(collect_dir):
        raise Exception(f"Cannot find collect_dir at {collect_dir}")
    register_experiments.register_app(app)
    app.config["COLLECT_DIR"] = collect_dir
    app.config["UI_DEBUG"] = args.debug
    socketio.run(app, host=args.host, port=args.port)
