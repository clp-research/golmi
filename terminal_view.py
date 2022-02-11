import argparse
import multiprocessing
import socketio as so
import time


from app import register_experiments
from app.app import app, socketio, AUTH


def argparser():
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
    return parser.parse_args()


def run_server(host, port):
    register_experiments.register_app(app)
    socketio.run(app, host=host, port=port)


if __name__ == "__main__":
    args = argparser()

    # run server on other subprocess
    subproc = multiprocessing.Process(target=run_server, args=(args.host, args.port))
    subproc.start()

    sio = so.Client()
    
    time.sleep(1)

    sio.connect("http://localhost:5000", auth={"password":AUTH})
    

    subproc.terminate()