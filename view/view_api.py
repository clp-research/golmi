from flask import Flask, request
from flask_cors import CORS
from view_update_storage import ViewUpdateStorage
import requests
import json

# --- define globals --- #

HOST = "127.0.0.1"
PORT = "5002"

app = Flask(__name__)
# enable cross-origin requests 
# TODO: restrict sources
CORS(app)

update_storage = ViewUpdateStorage()

# --- define routes --- # 

@app.route("/updates", methods=["POST", "GET", "DELETE"])
def updates():
	# store new updates
	if request.method == "POST":
		if not request.data:
			return "1", 400
		else:
			json_data = json.loads(request.data)
		# Attempt to store updates. Return BAD REQUEST if something went wrong
		return "0" if update_storage.store_update(json_data) else ("1", 400)
	# return stored updates. Delete updates after this
	elif request.method == "GET":
		updates = update_storage.get_updates()
		update_storage.clear()
		return updates
	# clear any stored updates
	elif request.method == "DELETE":
		update_storage.clear()
		return "0"
	return "1", 405

def selftest():
	with app.test_client() as c:
		# clear the storage
		clear_storage = c.delete("/updates")
		assert clear_storage.status == "200 OK"

		# post an update
		post_new_update = c.post("/updates", data=json.dumps({"grippers": ["4", "2"], "objs": ["1"]}))
		assert post_new_update.status == "200 OK"
	    # Make sure the updates are correctly stored
		assert update_storage.get_updates()["grippers"] == ["4", "2"] and \
			update_storage.get_updates()["objs"] == ["1"] and \
			update_storage.get_updates()["config"] == False
		# post another update and make sure the old updates are still there
		post_new_update2 = c.post("/updates", data=json.dumps({"objs": ["1", "2"], "config": True}))
		assert post_new_update2.status == "200 OK"
	    # Make sure the updates are correctly stored
		assert update_storage.get_updates()["grippers"] == ["4", "2"] and \
			update_storage.get_updates()["objs"] == ["1", "2"] and \
			update_storage.get_updates()["config"] == True

		# get pending updates
		get_updates = c.get("/updates")
		assert get_updates.status == "200 OK"
		assert json.loads(get_updates.data) == {"grippers": ["4", "2"], "objs": ["1", "2"], "config": True}
		# make sure the updates were deleted
		assert update_storage.get_updates() == {"grippers": list(), "objs": list(), "config": False}
if __name__ == "__main__":
	selftest()
	app.run(host=HOST, port=PORT)