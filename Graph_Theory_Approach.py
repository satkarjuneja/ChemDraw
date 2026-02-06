import subprocess
import json
import itertools
import networkx as nx
from rdkit import Chem



MAX_VALENCE = {
    "C": 4,
    "O":2,
    "N":3
}


def degree_of_unsaturation(C, H, N):
    DOU=int((2*C+2-H+N)/2)
    return (2*C + 2 - H) // 2



def generate_topologies(n_atoms, max_degree):
    """
    Uses geng to generate all connected, non-isomorphic graphs
    """
    
    cmd = ["/usr/local/bin/geng", "-c", f"-D{max_degree}", str(n_atoms)]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
    graphs = []
    for line in proc.stdout:
        G = nx.from_graph6_bytes(line.strip().encode())
        graphs.append(G)

    return graphs


def valid_bond_assignments(G, dou):
    """
    Enumerate all valid bond-order assignments for a topology
    """
    V = G.number_of_nodes()
    E = G.number_of_edges()

    rings = E - V + 1
    pi_needed = dou - rings

    if pi_needed < 0:
        return []

    edges = list(G.edges())

    valid = []

    for double_edges in itertools.combinations(edges, pi_needed):
        bond_order = {e: 1 for e in edges}
        for e in double_edges:
            bond_order[e] = 2

        valence = {i: 0 for i in G.nodes()}
        for (i, j), order in bond_order.items():
            valence[i] += order
            valence[j] += order

        if all(valence[i] <= 4 for i in valence):
            valid.append(bond_order)

    return valid



def graph_to_mol(G, bond_orders):
    mol = Chem.RWMol()

    for _ in G.nodes():
        mol.AddAtom(Chem.Atom("C"))

    for (i, j), order in bond_orders.items():
        if order == 1:
            mol.AddBond(i, j, Chem.BondType.SINGLE)
        elif order == 2:
            mol.AddBond(i, j, Chem.BondType.DOUBLE)

    mol = mol.GetMol()

    try:
        Chem.SanitizeMol(mol)
    except:
        return None

    return mol



def generate_isomers(C, H, N, outfile):
    dou = degree_of_unsaturation(C, H,N)

    max_degree = 4

    graphs = generate_topologies(C, max_degree)

    smiles_set = set()
    molecules = []

    for G in graphs:
        assignments = valid_bond_assignments(G, dou)

        for bond_orders in assignments:
            mol = graph_to_mol(G, bond_orders)
            if mol is None:
                continue

            smi = Chem.MolToSmiles(mol, canonical=True)
            if smi in smiles_set:
                continue

            smiles_set.add(smi)

            molecules.append(smi)

    with open(outfile, "w") as f:
        json.dump(molecules, f, indent=2)

    print(f"Generated {len(molecules)} isomers")



import sys
import re

X=sys.argv[1]

tokens = re.findall(r'([CHON])(\d*)', X)

c = 0
h = 0
o=0
n=0

for elem, num in tokens:
    count = int(num) if num else 1
    if elem == 'C':
        c = count
    elif elem == 'H':
        h = count
    elif elem=="O":
        o=count
    elif elem=="N":
        n=count


if __name__ == "__main__":
    generate_isomers(C=c, H=h,N=n, outfile="molecules.json")
    subprocess.run(["python", "Depicter.py"])

