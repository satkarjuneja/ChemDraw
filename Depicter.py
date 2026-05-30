from rdkit import Chem
from rdkit.Chem import Draw
import json
import sys


def render_2d(png_path: str, molecules_path: str = "molecules.json") -> None:
    with open(molecules_path) as f:
        smiles_list = json.load(f)

    mols = [Chem.MolFromSmiles(smi) for smi in smiles_list]
    img = Draw.MolsToGridImage(mols, molsPerRow=4, subImgSize=(200, 200))
    img.save(png_path)
    print(f"Saved {png_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: Depicter.py <png_path>", file=sys.stderr)
        sys.exit(1)

    render_2d(sys.argv[1])
