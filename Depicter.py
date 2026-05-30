from rdkit import Chem
from rdkit.Chem import Draw
import json
import sys

PNG_PATH = sys.argv[1]

with open("molecules.json") as f:
    smiles_list = json.load(f)

mols = [Chem.MolFromSmiles(smi) for smi in smiles_list]

img = Draw.MolsToGridImage(mols, molsPerRow=4, subImgSize=(200, 200))

img.save(PNG_PATH)
print(f"Saved {PNG_PATH}")
