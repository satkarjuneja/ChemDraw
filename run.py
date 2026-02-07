from rdkit import Chem
from rdkit.Chem import Draw, Descriptors, rdMolDescriptors
from joblib import load
import json
import numpy as np

model = load("my_model.joblib")

def featurize(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None

    features = [
        Descriptors.MolWt(mol),
        Descriptors.MolLogP(mol),
        Descriptors.TPSA(mol),
        Descriptors.NumHDonors(mol),
        Descriptors.NumHAcceptors(mol),
        Descriptors.NumRotatableBonds(mol),
        Descriptors.FractionCSP3(mol),
        Descriptors.RingCount(mol),
        Descriptors.HeavyAtomCount(mol),
        Descriptors.MolMR(mol),
        rdMolDescriptors.CalcHallKierAlpha(mol),
        Descriptors.TPSA(mol)/Descriptors.MolWt(mol),
        Descriptors.MolMR(mol)/Descriptors.HeavyAtomCount(mol)
    ]

    num_aromatic_atoms = sum(1 for atom in mol.GetAtoms() if atom.GetIsAromatic())
    frac_aromatic_atoms = num_aromatic_atoms / mol.GetNumHeavyAtoms() if mol.GetNumHeavyAtoms() > 0 else 0
    num_aromatic_rings = rdMolDescriptors.CalcNumAromaticRings(mol)

    features.extend([num_aromatic_atoms, frac_aromatic_atoms, num_aromatic_rings])
    return features

with open("molecules.json") as f:
    data = json.load(f)

if isinstance(data[0], str):
    data = [{"smiles": s} for s in data]

X = []
valid_entries = []
for entry in data:
    fp = featurize(entry["smiles"])
    if fp is not None:
        X.append(fp)
        valid_entries.append(entry)

X = np.array(X)
preds = model.predict(X)

for entry, pred in zip(valid_entries, preds):
    entry["pred"] = pred

sorted_entries = sorted(valid_entries, key=lambda x: x["pred"], reverse=True)

for entry in sorted_entries:
    print(entry["smiles"], entry["pred"])

mols = [Chem.MolFromSmiles(entry["smiles"]) for entry in sorted_entries]

img = Draw.MolsToGridImage(
    mols,
    molsPerRow=3,
    subImgSize=(200,200)
)

img.save("static/molecules_grid.png")
print("Saved molecules_grid.png")
