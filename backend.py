# No i Donot have time to write the backend myself
from flask import Flask, request, send_file, render_template

import subprocess

import sys

import os

from flask_cors import CORS



app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


CORS(app)




STATIC_DIR = os.path.join(os.getcwd(), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
PNG_FILE = os.path.join(STATIC_DIR, "molecules_grid.png")



@app.route("/generate", methods=["POST"])

def generate():

    data = request.get_json()

    formula = data.get("formula")

    if not formula:

        return "No formula provided", 400





    # subprocess.run([sys.executable, "Matrix_Generation.py", formula, PNG_FILE], check=True)


    subprocess.run([sys.executable, "Graph_Theory_Approach.py", formula, PNG_FILE], check=True)




    return "OK", 200




@app.route("/molecules_grid.png", methods=["GET"])

def serve_png():

    if not os.path.exists(PNG_FILE):

        return "PNG not found", 404

    return send_file(PNG_FILE, mimetype="image/png")





if __name__ == "__main__":

    app.run(debug=True, host="0.0.0.0", port=7860)