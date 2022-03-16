import os
import argparse
import random
from pathlib import Path
from flask import Flask, request, render_template, send_file

app = Flask(__name__)


def retrieve_image(folder):
    imgs = os.listdir(folder)
    return random.choice(imgs)

@app.route("/")
def home():
    folder = "static"
    img = retrieve_image(folder)
   
    return render_template("home.html", methods=["GET"], state_image=img, folder=folder)

@app.route('/', methods=['POST'])
def my_form_post():
    description = request.form['text']

    # do something else with description
    print(description)

    return home()

def create_app():
    return app


if __name__ == "__main__":
    app.run()