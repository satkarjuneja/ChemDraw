from rdkit import Chem
from rdkit.Chem import Draw
import json

with open("molecules.json") as f:
    smiles_list = json.load(f)

mols = [Chem.MolFromSmiles(smi) for smi in smiles_list]

img = Draw.MolsToGridImage(
    mols,             
    molsPerRow=3,       
    subImgSize=(200,200)
)

img.save("static/molecules_grid.png")
print("Saved molecules_grid.png")
