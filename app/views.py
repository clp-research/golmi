from app import app
from flask import render_template, jsonify

# --- define routes --- # 

@app.route("/", methods=["GET"])
def index():
	"""
	Interactive interface.
	"""
	return render_template("index.html")

@app.route("/ba_tasks", methods=["GET"])
def tasks():
	"""
	Tasks for the interface in JSON format.
	"""
	# tasks are saved in JSON format in a server-side file
	file = open("./app/static/resources/tasks/ba_tasks.json", mode="r", encoding="utf-8")
	tasks = file.read()
	file.close()
	return jsonify(tasks)