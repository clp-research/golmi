from app import app, socketio
from flask import render_template, request, abort
import json
from time import time_ns
import os

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

@app.route("/save_log", methods=["POST"])
def save_log():
	if not request.data or not request.is_json:
		abort(400)
	json_data = request.json
	# as a filename that 
	# (1) can not be manipulated by a client
	# (2) has a negligible chance of collision
	# a simple timestamp is used
	filename = str(time_ns()/100) + ".json"
	# check if "data_collection" directory exists, create if necessary
	savepath = app.config["DATA_COLLECTION"]
	if not os.path.exists(savepath):
		os.mkdir(savepath)
	file = open(os.path.join(savepath, filename), encoding="utf-8", mode="w")
	file.write(json.dumps(json_data, indent=2))
	file.close
	return "0", 200
