import argparse
from app import app, socketio

# --- GOLMi's server --- # 
# author: clpresearch, Karla Friedrichs
# usage: python3 run.py [-h] [--host HOST] [--port PORT]
# Runs on host 127.0.0.1 and port 5000 per default

# --- command line arguments ---
parser = argparse.ArgumentParser(description="Run GOLMI's model API.")
parser.add_argument("--host", type=str, default="127.0.0.1",
                    help="Address to run the API on. Default: localhost.")
parser.add_argument("--port", type=str, default="5000",
                    help="Port to run the API on. Default: 5000.")
parser.add_argument("--test", action="store_true",
                    help="Pass this argument to perform some tests before the API is run.")

if __name__ == "__main__":
    args = parser.parse_args()
    print("Starting app on ", "{}:{}".format(args.host, args.port))
    socketio.run(app, host=args.host, port=args.port)
