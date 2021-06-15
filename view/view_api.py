from flask import Flask, request
from flask_cors import CORS
from view_update_storage import ViewUpdateStorage
import requests

# --- define globals --- #

HOST = "127.0.0.1"
PORT = "5002"

# --- define routes --- # 

app = Flask(__name__)
# enable cross-origin requests 
# TODO: restrict sources
CORS(app)

updateStorage = ViewUpdateStorage()

@app.route("/updates", methods=["POST", "GET", "DELETE"])
def update():
	if request.method == "POST":
		# check what kind of update was sent
		if (b"gripper" in request.data):
			# -> forward to view
			view.store_update("gripper")
			#TODO what the fuck to return here?
			return "0"
		return "1"
	elif request.method == "GET":
		updates = updateStorage.get_updates()
		if len(updates) == 0:
			return dict(), 204 # no content 
		else:
			return updates
	elif request.method == "DELETE":
		updateStorage.clear()
		return "0"
	return "1", 405

def selftest():
	with app.test_client() as c:
	    pass

if __name__ == "__main__":
	selftest()
	app.run(host=HOST, port=PORT)