import json
import sys

print("I am being called")

PDB_FILE = sys.argv[1]

current = []
molecules = []

with open(PDB_FILE) as f:
    for line in f:
        current.append(line)
        if line.strip() == "END":
            molecules.append(
                {"id": f"mol_{len(molecules) + 1}", "pdb": "".join(current)}
            )
            current = []

with open("static/3d_molecules.json", "w") as out:
    json.dump(molecules, out, indent=2)
