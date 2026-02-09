from rdkit import Chem
from rdkit.Chem import AllChem
import json
import sys

OUTPUT_PATH = sys.argv[1]

with open("molecules.json") as f:
    smiles_list = json.load(f)

writer = Chem.PDBWriter(OUTPUT_PATH)
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

print(f"Wrote {count} molecules to {OUTPUT_PATH}")
