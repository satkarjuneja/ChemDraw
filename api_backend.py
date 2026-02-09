from flask import Flask, request, Response
import subprocess
import uuid

app = Flask(__name__)

@app.route("/s", methods=["POST"])
def generate_smiles_csv():
    data = request.get_json()
    formula = data.get("formula")
    if not formula:
        return "No formula provided", 400

    output_file = f"/tmp/{uuid.uuid4().hex}.txt"
    subprocess.run(["python", "parser.py", formula, output_file], check=True)

    # Read SMILES
    with open(output_file) as f:
        smiles_list = [line.strip() for line in f if line.strip()]

    # Build CSV content
    csv_content = "SMILES\n" + "\n".join(smiles_list)

    # Return CSV as response
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={formula}.csv"}
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
