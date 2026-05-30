"""
Isomer Generator — geng backend, full bond types + heteroatoms
Supports: C, H, N, O, S, F, Cl, Br, P
Usage: python isomer_gen.py <formula> [outfile]
  e.g. python isomer_gen.py C6H6        -> benzene isomers
       python isomer_gen.py C2H5OH      -> ethanol isomers
       python isomer_gen.py C4H9N       -> butylamine isomers
"""

import subprocess
import json
import itertools
import sys
import re
import networkx as nx
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
from collections import Counter


# ----------------Valence config------------------

# Maximum total bond order (valence) each element can have
MAX_VALENCE = {
    "C": 4,
    "N": 3,
    "O": 2,
    "S": 6,  # S can be 2, 4, or 6; we cap at 6, RDKit sanitisation filters
    "P": 5,
    "F": 1,
    "Cl": 1,
    "Br": 1,
    "I": 1,
}

# Elements that can participate in multiple bonds (double/triple)
MULTIBOND_CAPABLE = {"C", "N", "O", "S", "P"}

# Halogens and other terminal atoms — always degree-1, single bond only
TERMINAL_ATOMS = {"F", "Cl", "Br", "I"}


# ---------------------------------------------------------------------------
# Formula parsing
# ---------------------------------------------------------------------------


def parse_formula(formula: str) -> dict[str, int]:
    """
    Parse a molecular formula string like C6H12O into a dict.
    Handles multi-char elements (Cl, Br) and implicit count-1.
    """
    pattern = r"([A-Z][a-z]?)(\d*)"
    counts: dict[str, int] = {}
    for elem, num in re.findall(pattern, formula):
        if elem not in MAX_VALENCE and elem != "H":
            raise ValueError(f"Unsupported element: {elem}")
        counts[elem] = counts.get(elem, 0) + (int(num) if num else 1)
    return counts


# ---------------------------------------------------------------------------
# Degree of unsaturation
# ---------------------------------------------------------------------------


def degree_of_unsaturation(formula: dict[str, int]) -> int:
    """
    DBE = (2C + 2 + N - H - X) / 2
    X = halogens (F, Cl, Br, I)
    S and P contribute 0 to this formula.
    Returns int; raises if result is non-integer (invalid formula).
    """
    C = formula.get("C", 0)
    H = formula.get("H", 0)
    N = formula.get("N", 0)
    X = sum(formula.get(x, 0) for x in ("F", "Cl", "Br", "I"))

    numerator = 2 * C + 2 + N - H - X
    if numerator % 2 != 0:
        raise ValueError(
            f"Formula has non-integer DBE ({numerator}/2) — invalid valence sum."
        )
    return numerator // 2


# --------------Topology generation via geng------------------


def generate_topologies(n_heavy: int, max_degree: int) -> list[nx.Graph]:
    """
    Call geng to produce all connected non-isomorphic graphs on n_heavy
    vertices with maximum degree max_degree. Returns list of NetworkX graphs.
    """
    cmd = ["geng", "-c", f"-D{max_degree}", str(n_heavy)]
    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True
        )
    except FileNotFoundError:
        raise RuntimeError("geng not found — install nauty and ensure geng is on PATH.")

    graphs = []
    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue
        G = nx.from_graph6_bytes(line.encode())
        graphs.append(G)
    proc.wait()
    return graphs


# -------------Atom-type assignment (heteroatom placement)-----------------


def assign_atom_types(G: nx.Graph, formula: dict[str, int]) -> list[dict[int, str]]:
    """
    Given a topology G and a formula, generate all distinct assignments of
    atom types (excluding H) to graph nodes, respecting:
      - correct element counts
      - degree of node <= max valence of element
      - terminal atoms (halogens) go only to degree-1 nodes

    Returns list of {node_id: element} dicts.
    """
    heavy = {k: v for k, v in formula.items() if k != "H"}
    nodes = list(G.nodes())
    degrees = dict(G.degree())

    # Build flat list of elements to assign, e.g. ['C','C','C','N','O']
    elements = []
    for elem, count in heavy.items():
        elements.extend([elem] * count)

    if len(elements) != len(nodes):
        return []  # formula doesn't match graph size

    seen: set[tuple] = set()
    results = []

    for perm in itertools.permutations(elements):
        assignment = dict(zip(nodes, perm))

        # Fast validity checks before canonicalising
        valid = True
        for node, elem in assignment.items():
            deg = degrees[node]
            # Degree can't exceed max valence (bond order >= 1 per edge)
            if deg > MAX_VALENCE[elem]:
                valid = False
                break
            # Terminal atoms must have degree 1
            if elem in TERMINAL_ATOMS and deg != 1:
                valid = False
                break
        if not valid:
            continue

        # Canonicalise to avoid duplicates from graph automorphisms:
        # sort assignment by node, hash the (elem, sorted_neighbour_elems) sequence
        canon_key = tuple(
            (assignment[n], tuple(sorted(assignment[nb] for nb in G.neighbors(n))))
            for n in sorted(nodes)
        )
        if canon_key in seen:
            continue
        seen.add(canon_key)
        results.append(assignment)

    return results


# ---------------Bond-order assignment-----------------


def assign_bond_orders(
    G: nx.Graph, atom_types: dict[int, str], dbe: int
) -> list[dict[tuple, int]]:
    """
    Assign bond orders (1, 2, 3) to edges consistent with:
      - total pi bonds == dbe - ring_count  (pi from bonds only)
      - per-atom valence sum <= MAX_VALENCE[elem]
      - terminal atoms only get order-1 bonds
      - atoms not in MULTIBOND_CAPABLE only get order-1 bonds

    Returns list of {(i,j): order} dicts.
    """
    edges = list(G.edges())
    V = G.number_of_nodes()
    E = G.number_of_edges()
    ring_count = E - V + 1  # for connected graph
    pi_needed = dbe - ring_count

    if pi_needed < 0:
        return []

    # Which edges can carry extra pi bonds?
    eligible = [
        e
        for e in edges
        if atom_types[e[0]] in MULTIBOND_CAPABLE
        and atom_types[e[1]] in MULTIBOND_CAPABLE
    ]

    results = []

    # We need to distribute pi_needed pi-electrons across eligible edges.
    # Each edge can get +1 (double) or +2 (triple) above single.
    # Generate all (edge, extra) combinations that sum to pi_needed.
    # Represent as: choose a multiset of (edge, delta) with delta in {1,2}.

    def _distribute(edges_left, pi_left, current):
        if pi_left == 0:
            yield dict(current)
            return
        if not edges_left or pi_left < 0:
            return
        e = edges_left[0]
        rest = edges_left[1:]
        # skip this edge (delta=0)
        yield from _distribute(rest, pi_left, current)
        # double bond (delta=1)
        if pi_left >= 1:
            yield from _distribute(rest, pi_left - 1, current + [(e, 2)])
        # triple bond (delta=2)
        if pi_left >= 2:
            yield from _distribute(rest, pi_left - 2, current + [(e, 3)])

    for partial in _distribute(eligible, pi_needed, []):
        bond_order = {e: 1 for e in edges}
        for e, order in partial.items():
            bond_order[e] = order

        # Validate per-atom valence
        valence: dict[int, int] = {n: 0 for n in G.nodes()}
        for (i, j), order in bond_order.items():
            valence[i] += order
            valence[j] += order

        valid = all(valence[n] <= MAX_VALENCE[atom_types[n]] for n in G.nodes())
        if valid:
            results.append(bond_order)

    return results


# ---------------Build RDKit mol + hydrogen validation--------------------

BOND_TYPE_MAP = {
    1: Chem.BondType.SINGLE,
    2: Chem.BondType.DOUBLE,
    3: Chem.BondType.TRIPLE,
}


def build_mol(
    G: nx.Graph,
    atom_types: dict[int, str],
    bond_orders: dict[tuple, int],
    expected_H: int,
) -> Chem.Mol | None:
    """
    Build an RDKit molecule, sanitise it, and check the implicit H count
    matches the formula. Returns None if invalid.
    """
    rw = Chem.RWMol()
    node_to_idx: dict[int, int] = {}

    for node in sorted(G.nodes()):
        idx = rw.AddAtom(Chem.Atom(atom_types[node]))
        node_to_idx[node] = idx

    for (i, j), order in bond_orders.items():
        rw.AddBond(node_to_idx[i], node_to_idx[j], BOND_TYPE_MAP[order])

    mol = rw.GetMol()
    try:
        Chem.SanitizeMol(mol)
    except Exception:
        return None

    # Check hydrogen count matches formula
    mol_with_H = Chem.AddHs(mol)
    actual_H = sum(1 for a in mol_with_H.GetAtoms() if a.GetAtomicNum() == 1)
    if actual_H != expected_H:
        return None

    return mol


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------


def generate_isomers(formula_str: str, outfile: str = "molecules.json"):
    formula = parse_formula(formula_str)
    print(f"Formula: {formula}")

    expected_H = formula.get("H", 0)
    n_heavy = sum(v for k, v in formula.items() if k != "H")

    if n_heavy == 0:
        print("No heavy atoms.")
        return

    try:
        dbe = degree_of_unsaturation(formula)
    except ValueError as e:
        print(f"Error: {e}")
        return

    print(f"Heavy atoms: {n_heavy}, DBE: {dbe}")

    # Max degree = max valence of any heavy element (cap at 4 for geng,
    # since geng -D controls graph degree not bond order)
    max_graph_degree = min(
        max(MAX_VALENCE[e] for e in formula if e != "H"),
        4,  # geng's -D is graph degree (number of neighbours)
    )

    print(f"Generating topologies (max graph degree {max_graph_degree})...")
    graphs = generate_topologies(n_heavy, max_graph_degree)
    print(f"  {len(graphs)} topologies")

    smiles_set: set[str] = set()
    molecules: list[str] = []

    for G in graphs:
        for atom_assignment in assign_atom_types(G, formula):
            for bond_order_map in assign_bond_orders(G, atom_assignment, dbe):
                mol = build_mol(G, atom_assignment, bond_order_map, expected_H)
                if mol is None:
                    continue
                smi = Chem.MolToSmiles(mol, canonical=True)
                if smi in smiles_set:
                    continue
                smiles_set.add(smi)
                molecules.append(smi)

    with open(outfile, "w") as f:
        json.dump(molecules, f, indent=2)

    print(f"\nGenerated {len(molecules)} unique isomers -> {outfile}")


# -----------Input-------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python isomer_gen.py <formula> [outfile]")
        print("  e.g. python isomer_gen.py C4H10O")
        sys.exit(1)

    formula_input = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "molecules.json"

    generate_isomers(formula_input, output_file)
