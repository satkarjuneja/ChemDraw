from rdkit import Chem
import sys


def adjacency_to_smiles(A, atoms):
    emol = Chem.RWMol()
    for a in atoms:
        emol.AddAtom(Chem.Atom(a))

    n = len(atoms)
    for i in range(n):
        for j in range(i + 1, n):
            bond = A[i][j]
            if bond == 0:
                continue
            elif bond == 1:
                emol.AddBond(i, j, Chem.BondType.SINGLE)
            elif bond == 2:
                emol.AddBond(i, j, Chem.BondType.DOUBLE)
            elif bond == 3:
                emol.AddBond(i, j, Chem.BondType.TRIPLE)
    mol = emol.GetMol()
    return Chem.MolToSmiles(mol, canonical=True)


import re

X = sys.argv[1]
tokens = re.findall(r"([CHON])(\d*)", X)

c = 0
h = 0
o = 0
n = 0

for elem, num in tokens:
    count = int(num) if num else 1
    if elem == "C":
        c = count
    elif elem == "H":
        h = count
    elif elem == "O":
        o = count
    elif elem == "N":
        n = count

print(c, h)

DOU = int((2 * c + 2 - h + n) / 2)
atoms = []

for i in range(c):
    atoms.append("C")
for i in range(o):
    atoms.append("O")
for i in range(n):
    atoms.append("N")


import itertools
import numpy as np


def generate_all_structures(atoms, max_valence, DOU):
    n = len(atoms)
    num_edges = n * (n - 1) // 2
    rows, cols = np.triu_indices(n, 1)
    matrices = []

    if DOU >= 2:
        bond_orders = [0, 1, 2, 3]
    elif DOU == 1:
        bond_orders = [0, 1, 2]
    else:
        bond_orders = [0, 1]

    for bits in itertools.product(bond_orders, repeat=num_edges):
        valid = True
        deg = [0] * n

        # Early valence pruning
        for i, j, b in zip(rows, cols, bits):
            deg[i] += b
            deg[j] += b
            if deg[i] > max_valence[atoms[i]] or deg[j] > max_valence[atoms[j]]:
                valid = False
                break

        if not valid:
            continue

        # Build adjacency matrix
        A = np.zeros((n, n), dtype=int)
        A[rows, cols] = bits
        A += A.T

        # Connectivity check
        visited = set()
        stack = [0]
        while stack:
            node = stack.pop()
            if node not in visited:
                visited.add(node)
                stack.extend(j for j in range(n) if A[node, j] > 0 and j not in visited)

        if len(visited) < n:
            continue

        matrices.append(A.tolist())

    return matrices


# calling of function which generates adjacency matrices
max_valence = {"C": 4, "O": 2, "N": 3}
matrices = generate_all_structures(atoms, max_valence, DOU)
print(f"Found {len(matrices)} unique structures\n")


unique_smiles = set()

for A in matrices:
    smi = adjacency_to_smiles(A, atoms)
    # convert adjacency matrices into SMILE form and SMILE into mol to check for rings and unsaturation
    mol = Chem.MolFromSmiles(smi)

    num_rings = mol.GetRingInfo().NumRings()
    num_pi_bonds = sum(1 for bond in mol.GetBonds() if bond.GetBondTypeAsDouble() > 2)
    num_pi_bonds += sum(1 for bond in mol.GetBonds() if bond.GetBondTypeAsDouble() > 1)
    # num_pi_bonds_2 = sum(1 for bond in mol.GetBonds() if bond.GetBondTypeAsTriple() > 1)

    DOUG = num_pi_bonds + num_rings
    if DOUG == DOU:
        unique_smiles.add(smi)


print(f"Unique molecules after deduplication: {len(unique_smiles)}")
print(unique_smiles)


import json


smiles_list = list(unique_smiles)

with open("molecules.json", "w") as f:
    json.dump(smiles_list, f, indent=2)

print("Saved to molecules.json")
