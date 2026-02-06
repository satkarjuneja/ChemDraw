# from flask import Flask, request, send_file
from flask import Flask, request, send_file, render_template

import subprocess

import sys

import os

from flask_cors import CORS



app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


CORS(app)  # allow frontend requests from another origin if needed



# fixed PNG path

PNG_FILE = os.path.join(os.getcwd(), "molecules_grid.png")



@app.route("/generate", methods=["POST"])

def generate():

    data = request.get_json()

    formula = data.get("formula")

    if not formula:

        return "No formula provided", 400



    # run your existing Matrix_Generation.py script with formula and PNG_FILE as output


    subprocess.run([sys.executable, "Matrix_Generation.py", formula, PNG_FILE], check=True)


    subprocess.run([sys.executable, "Graph_Theory_Approach.py", formula, PNG_FILE], check=True)



    # return a simple response (frontend will reload the <img>)

    return "OK", 200



# optional: serve the PNG (if frontend wants direct URL)

@app.route("/molecules_grid.png", methods=["GET"])

def serve_png():

    if not os.path.exists(PNG_FILE):

        return "PNG not found", 404

    return send_file(PNG_FILE, mimetype="image/png")





if __name__ == "__main__":

    app.run(debug=True, host="0.0.0.0", port=7860)