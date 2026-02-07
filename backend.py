# No i Do not have time to write the backend myself

from flask import Flask, request, send_file, render_template
from flask import jsonify
import subprocess

import sys

import os

from flask_cors import CORS

import base64
import json
import io
import uuid


app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


CORS(app)



STATIC_DIR = os.path.join(os.getcwd(), "static")
os.makedirs(STATIC_DIR, exist_ok=True)


prev_png_file = None

@app.route("/generate", methods=["POST"])
def generate():
    
    global prev_png_file
    # okay did have to fix this myself since every png has a unique uuid and i 
    # wanted to delete the previous png before making a new one had to make all this arrangement
    
    data = request.get_json()
    
    formula = data.get("formula")
    if not formula:
        return "No formula provided", 400
    if prev_png_file is not None and os.path.exists(prev_png_file):
        os.remove(prev_png_file)

        
    # Generate a unique PNG per request this creates a unique uuid for the png 
    # so now multiple users can use this at the same time :)
    
    png_file = os.path.join(STATIC_DIR, f"{uuid.uuid4().hex}.png")

    subprocess.run([sys.executable, "Graph_Theory_Approach.py", formula, png_file], check=True)

    # Read PNG and convert to Base64
    with open(png_file, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")

    prev_png_file = png_file
    
    # Return JSON with Base64 image
    return jsonify({"img": f"data:image/png;base64,{img_b64}"})


if __name__ == "__main__":

    app.run(debug=True, host="0.0.0.0", port=7860)