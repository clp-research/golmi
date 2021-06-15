from flask import Flask, request
from flask_cors import CORS, cross_origin
from key_controller import KeyController
import requests
import json

# ------------------------------------------------------------------------------ #
# An example implementation of a Controller module. This API allows for user
# interaction via a keyboard. 
# ------------------------------------------------------------------------------ #

# --- define globals --- #

app = Flask(__name__)
# enable cross-origin requests 
# TODO: restrict sources
CORS(app)

key_controller = KeyController()
HOST = "127.0.0.1"
PORT = "5001"

# --- define routes --- # 

@app.route("/attach-model", methods=["POST"])
def attach_model():
	json_data = json.loads(request.data)
	key_controller.attach_model(json_data["url"])
	# In the future, the return value of attach_model() above could be used to inform
	# the client: False is returned if model was already attached
	return "0"

@app.route("/detach-model", methods=["POST"])
def detach_model():
	json_data = json.loads(request.data)
	key_controller.detach_model(json_data["url"])
	# In the future, the return value of detach_model() above could be used to inform
	# the client: False is returned if the requested model was not found
	return "0"

@app.route("/key-pressed/<int:key_code>", methods=["POST"])
def key_pressed(key_code):
	# attempt to process the key. False is returned if no function is assigned.
	if key_controller.key_pressed(key_code):
		return "0"
	return ("1", 404)

def selftest():
	with app.test_client() as c:
		# subscribe a model
		dummy_model = "127.0.0.1:5000"
		r_subscribe_model = c.post("/attach-model", data=json.dumps({"url": dummy_model}))
		assert int(r_subscribe_model.data) == 0
		# attempt to subscribe an already subscribed model
		r_subscribe_model2 = c.post("/attach-model", data=json.dumps({"url": dummy_model}))
		assert int(r_subscribe_model2.data) == 0

		# test keypress
		r_unassigned_keypress = c.post("/key-pressed/1")
		assert int(r_unassigned_keypress.data) == 1
		r_keypress_grip = c.post("/key-pressed/32")
		assert int(r_keypress_grip.data) == 0
		r_keypress_move = c.post("/key-pressed/37")
		assert int(r_keypress_move.data) == 0

		# unsubscribe a model
		r_unsubscribe_model = c.post("/detach-model", data=json.dumps({"url": dummy_model}))
		assert int(r_unsubscribe_model.data) == 0
		# attempt to unsubscribe a non-subscribed model
		r_unsubscribe_model2 = c.post("/detach-model", data=json.dumps({"url": dummy_model}))
		assert int(r_unsubscribe_model2.data) == 0

if __name__ == "__main__":
	selftest()
	app.run(host=HOST, port=PORT)