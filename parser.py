import sys
import re
import subprocess
from pathlib import Path


def validate_formula(formula: str) -> dict:
    """
    Validate and parse chemical formula.
    
    Args:
        formula: Chemical formula string, e.g., "C6H6"
    
    Returns:
        Dictionary: {"C": 6, "H": 6, "N": 0, "O": 0}
    
    Raises:
        ValueError: If formula is invalid or too large
    """
    # Type check
    if not isinstance(formula, str):
        raise ValueError(f"Formula must be string, got {type(formula).__name__}")
    
    # Empty check
    if not formula.strip():
        raise ValueError("Formula cannot be empty")
    
    # Whitelist regex: only C, H, N, O with optional digits
    pattern = r'^[CHNO]\d*([CHNO]\d*)*$'
    
    if not re.fullmatch(pattern, formula):
        raise ValueError(
            f"Invalid formula: {formula}. "
            f"Use only C, H, N, O with optional counts (e.g., C6H6, CH4)"
        )
    
    # Parse formula
    tokens = re.findall(r'([CHNO])(\d*)', formula)
    atoms = {"C": 0, "H": 0, "N": 0, "O": 0}
    
    for element, count_str in tokens:
        count = int(count_str) if count_str else 1
        
        if count > 1000:
            raise ValueError(
                f"Element {element} has count {count} (max 1000)"
            )
        
        atoms[element] += count
    
    # Total atom limit (prevents DoS)
    total_atoms = sum(atoms.values())
    if total_atoms > 50:
        raise ValueError(
            f"Formula too large: {total_atoms} atoms (max 50)"
        )
    
    return atoms


def run_algorithm(formula: str, timeout: int = 30) -> None:
    """
    Run molecule generation algorithm with timeout.
    
    Args:
        formula: Validated formula string
        timeout: Maximum seconds (prevents hangs)
    
    Raises:
        TimeoutError: If generation exceeds timeout
        subprocess.CalledProcessError: If algorithm fails
    """
    
    # Determine algorithm
    if re.search(r'[NO]', formula):
        script = "Matrix_Generation.py"
    else:
        script = "Graph_Theory_Approach.py"
    
    # Check script exists
    if not Path(script).exists():
        raise FileNotFoundError(f"Script not found: {script}")
    
    try:
        result = subprocess.run(
            [sys.executable, script, formula],
            timeout=timeout,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Unknown error"
            raise subprocess.CalledProcessError(
                result.returncode, script, output=error_msg
            )
    
    except subprocess.TimeoutExpired:
        raise TimeoutError(
            f"Algorithm timeout after {timeout}s. Formula too complex."
        )


# Main entry point
if __name__ == "__main__":
    try:
        if len(sys.argv) < 4:
            raise ValueError("Usage: parser.py <formula> <png_path> <pdb_path>")
        
        formula = sys.argv[1]
        png_path = sys.argv[2]
        pdb_path = sys.argv[3]
        
        # Validate formula
        atoms = validate_formula(formula)
        print(f"✔ Formula validated: {formula}")
        
        # Run algorithm
        print("Generating isomers...")
        run_algorithm(formula, timeout=30)
        print(f"✔ Generated molecules.json")
        
        # Render 2D
        subprocess.run(["python", "Depicter.py", png_path], check=True)
        print(f"✔ Rendered 2D: {png_path}")
        
        # Render 3D
        subprocess.run(["python", "3D_Depicter.py", pdb_path], check=True)
        print(f"✔ Rendered 3D: {pdb_path}")
        
    except ValueError as e:
        print(f"❌ Validation Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    except TimeoutError as e:
        print(f"❌ Timeout: {e}", file=sys.stderr)
        sys.exit(2)
    
    except subprocess.CalledProcessError as e:
        print(f"❌ Process Error: {e.output}", file=sys.stderr)
        sys.exit(1)
    
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)

    subprocess.run(["python","templates/PDB_Splitter.py",pdb_path])