import argparse
import os

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

if __name__ == "__main__":
    if {"GOLMI_HOST", "GOLMI_PORT"}.issubset(set(os.environ)):
        host = os.environ["GOLMI_HOST"]
        port = os.environ["GOLMI_PORT"]
    else:
        args = parser.parse_args()
        host = args.host
        port = args.port

    register_experiments.register_app(app)
    print(f"Started at {host}:{port}")
    socketio.run(app, host=host, port=port)
