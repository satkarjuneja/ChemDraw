import json
import sys


def split_pdb(pdb_file: str, output_path: str = "static/3d_molecules.json") -> None:
    print("I am being called")

    current = []
    molecules = []

    with open(pdb_file) as f:
        for line in f:
            current.append(line)
            if line.strip() == "END":
                molecules.append(
                    {"id": f"mol_{len(molecules) + 1}", "pdb": "".join(current)}
                )
                current = []

    with open(output_path, "w") as out:
        json.dump(molecules, out, indent=2)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: PDB_Splitter.py <pdb_path>", file=sys.stderr)
        sys.exit(1)

    split_pdb(sys.argv[1])
