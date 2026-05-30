from rdkit import Chem
from rdkit.Chem import AllChem
import json
import sys


def render_3d(output_path: str, molecules_path: str = "molecules.json") -> int:
    with open(molecules_path) as f:
        smiles_list = json.load(f)

    writer = Chem.PDBWriter(output_path)
    count = 0

    for smi in smiles_list:
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            continue

        mol = Chem.AddHs(mol)

        if AllChem.EmbedMolecule(mol, AllChem.ETKDGv3()) != 0:
            continue

        if AllChem.MMFFHasAllMoleculeParams(mol):
            AllChem.MMFFOptimizeMolecule(mol)
        else:
            AllChem.UFFOptimizeMolecule(mol)

        writer.write(mol)
        count += 1

    writer.close()

    if count == 0:
        raise RuntimeError("No valid 3D molecules generated")

    print(f"Wrote {count} molecules to {output_path}")
    return count


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: depicter_3d.py <pdb_path>", file=sys.stderr)
        sys.exit(1)

    render_3d(sys.argv[1])
