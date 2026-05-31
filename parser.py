import sys
import re
import subprocess
from pathlib import Path

ALLOWED_ELEMENTS = {"C", "H", "N", "O", "S", "P", "F", "Cl", "Br", "I"}
ELEMENT_PATTERN = re.compile(r"(Cl|Br|[CHNOSPFI])(\d*)")


def validate_formula(formula: str) -> dict:
    """
    Validate and parse chemical formula.

    Args:
        formula: Chemical formula string, e.g., "C6H6"

    Returns:
        Dictionary of element counts.

    Raises:
        ValueError: If formula is invalid or too large
    """
    # Type check
    if not isinstance(formula, str):
        raise ValueError(f"Formula must be string, got {type(formula).__name__}")

    # Empty check
    if not formula.strip():
        raise ValueError("Formula cannot be empty")

    atoms = {elem: 0 for elem in ALLOWED_ELEMENTS}
    pos = 0
    for match in ELEMENT_PATTERN.finditer(formula):
        if match.start() != pos:
            raise ValueError(
                f"Invalid formula: {formula}. "
                f"Use only {', '.join(sorted(ALLOWED_ELEMENTS))} with optional counts "
                f"(e.g., C6H6, C2H5Cl)"
            )
        element, count_str = match.groups()
        if element not in ALLOWED_ELEMENTS:
            raise ValueError(
                f"Invalid formula: {formula}. "
                f"Use only {', '.join(sorted(ALLOWED_ELEMENTS))} with optional counts "
                f"(e.g., C6H6, C2H5Cl)"
            )

        count = int(count_str) if count_str else 1
        if count > 1000:
            raise ValueError(f"Element {element} has count {count} (max 1000)")

        atoms[element] += count
        pos = match.end()

    if pos != len(formula):
        raise ValueError(
            f"Invalid formula: {formula}. "
            f"Use only {', '.join(sorted(ALLOWED_ELEMENTS))} with optional counts "
            f"(e.g., C6H6, C2H5Cl)"
        )

    # Total atom limit (prevents DoS)
    total_atoms = sum(atoms.values())
    if total_atoms > 50:
        raise ValueError(f"Formula too large: {total_atoms} atoms (max 50)")

    from generator import degree_of_unsaturation

    dbe = degree_of_unsaturation(atoms)
    if dbe < 0:
        raise ValueError(f"Invalid formula: {formula}. Negative DBE ({dbe}).")

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

    # Algorithm
    script = "generator.py"

    # Check script exists
    if not Path(script).exists():
        raise FileNotFoundError(f"Script not found: {script}")

    try:
        result = subprocess.run(
            [sys.executable, script, formula],
            timeout=timeout,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Unknown error"
            raise subprocess.CalledProcessError(
                result.returncode, script, output=error_msg
            )

    except subprocess.TimeoutExpired:
        raise TimeoutError(f"Algorithm timeout after {timeout}s. Formula too complex.")


def run_pipeline(
    formula: str,
    png_path: str | None,
    pdb_path: str | None,
    timeout: int = 30,
    render_2d: bool = True,
    render_3d: bool = True,
) -> None:
    # Validate formula
    validate_formula(formula)
    print(f"✔ Formula validated: {formula}")

    if render_2d and not png_path:
        raise ValueError("png_path is required when render_2d is True")
    if render_3d and not pdb_path:
        raise ValueError("pdb_path is required when render_3d is True")

    # Run algorithm
    print("Generating isomers...")
    run_algorithm(formula, timeout=timeout)
    print("✔ Generated molecules.json")

    # Render 2D
    if render_2d:
        from Depicter import render_2d

        render_2d(png_path)
        print(f"✔ Rendered 2D: {png_path}")

    # Render 3D
    if render_3d:
        from depicter_3d import render_3d

        render_3d(pdb_path)
        print(f"✔ Rendered 3D: {pdb_path}")

        from templates.PDB_Splitter import split_pdb

        split_pdb(pdb_path)


# Main entry point
if __name__ == "__main__":
    try:
        if len(sys.argv) < 4:
            raise ValueError("Usage: parser.py <formula> <png_path> <pdb_path>")

        formula = sys.argv[1]
        png_path = sys.argv[2]
        pdb_path = sys.argv[3]

        run_pipeline(formula, png_path, pdb_path, timeout=30)

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
