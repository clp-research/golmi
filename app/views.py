from app import app
from flask import render_template

# --- define routes --- # 

@app.route("/", methods=["GET"])
def index():
	return render_template("index.html")

@app.route("/demo", methods=["GET"])
def demo():
	return render_template("demo.html")