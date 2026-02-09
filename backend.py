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


prev_PNG_FILE = None
prev_PDB_FILE =None
@app.route("/generate", methods=["POST"])
def generate():
    
    global prev_PNG_FILE
    # okay did have to fix this myself since every png has a unique uuid and i 
    # wanted to delete the previous png before making a new one had to make all this arrangement
    
    data = request.get_json()
    
    formula = data.get("formula")
    if not formula:
        return "No formula provided", 400
    if prev_PNG_FILE is not None and os.path.exists(prev_PNG_FILE):
        os.remove(prev_PNG_FILE)
    if prev_PDB_FILE is not None and os.path.exists(prev_PDB_FILE):
        os.remove(prev_PNG_FILE)


        
    # Generate a unique PNG per request this creates a unique uuid for the png 
    # so now multiple users can use this at the same time :)
    
    PNG_FILE = os.path.join(STATIC_DIR+"/2D", f"{uuid.uuid4().hex}.png")
    PDB_FILE = os.path.join(STATIC_DIR+"/3D", f"{uuid.uuid4().hex}.pdb")

    subprocess.run([sys.executable, "parser.py", formula, PNG_FILE,PDB_FILE], check=True)

    # Read PNG and convert to Base64
    with open(PNG_FILE, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")

    prev_PNG_FILE = PNG_FILE
    prev_PDB_FILE =PDB_FILE
    #Read JSON for 3D molecules Ideally could seprate the backend but :(
    JSON_FILE = os.path.join(STATIC_DIR, "3d_molecules.json")

    with open(JSON_FILE) as f:
        molecules = json.load(f)
    
    # Return JSON with Base64 image and the 3D JSON file
    return jsonify({
        "img": f"data:image/png;base64,{img_b64}",
        "molecules":molecules
        })


if __name__ == "__main__":

    app.run(debug=True, host="0.0.0.0", port=7860)