import argparse
import csv
import json
import math
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import matplotlib.pyplot as plt


DEFAULT_FORMULAS = [
    "H2O",
    "CH4",
    "C2H6",
    "C2H6O",
    "CH5N",
    "C2H7N",
    "C3H8",
    "C3H6O",
    "C3H8O",
    "C2H5NO",
    "C2H5NO2",
    "C4H10",
    "C4H8",
    "C4H10O",
    "C4H8O2",
    "C3H9N",
    "C3H9NO",
    "C3H7NO2",
    "C5H12",
    "C5H10",
    "C5H12O",
    "C5H10O2",
    "C4H11N",
    "C4H11NO",
    "C6H14",
    "C6H12",
    "C6H6",
    "C6H12O",
    "C7H16",
    "C7H14",
    "C7H16O",
]


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    idx = max(0, math.ceil(p * len(ordered)) - 1)
    return ordered[idx]


def run_once(
    codebase: Path, formula: str, timeout: float
) -> tuple[float | None, str | None]:
    with tempfile.TemporaryDirectory() as temp_dir:
        png_path = Path(temp_dir) / "out.png"
        pdb_path = Path(temp_dir) / "out.pdb"
        t0 = time.perf_counter()
        try:
            subprocess.run(
                [sys.executable, "parser.py", formula, str(png_path), str(pdb_path)],
                cwd=codebase,
                timeout=timeout,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
        except subprocess.TimeoutExpired:
            return None, "timeout"
        except subprocess.CalledProcessError as exc:
            message = (exc.stderr or "").strip()
            return None, message or "error"
        return time.perf_counter() - t0, None


def benchmark_codebase(
    codebase: Path,
    formulas: list[str],
    repeats: int,
    timeout: float,
    stop_after_timeouts: int,
    label: str,
) -> dict[str, dict[str, object]]:
    results: dict[str, dict[str, object]] = {}
    total = len(formulas)
    for index, formula in enumerate(formulas, start=1):
        formula_prefix = f"[{label} {index}/{total}]"
        times: list[float] = []
        timeouts = 0
        errors = 0
        runs = 0
        for run_index in range(1, repeats + 1):
            print(f"{formula_prefix} {formula} run {run_index}/{repeats}...")
            runs += 1
            elapsed, err = run_once(codebase, formula, timeout)
            if elapsed is None:
                if err == "timeout":
                    timeouts += 1
                    print(f"{formula_prefix} {formula} timed out ({timeouts})")
                    if timeouts >= stop_after_timeouts:
                        break
                else:
                    errors += 1
                    print(f"{formula_prefix} {formula} error: {err}")
            else:
                times.append(elapsed)
                print(f"{formula_prefix} {formula} ok: {elapsed:.2f}s")
        results[formula] = {
            "runs": runs,
            "successes": len(times),
            "timeouts": timeouts,
            "errors": errors,
            "times": times,
            "median": statistics.median(times) if times else None,
            "p95": percentile(times, 0.95) if times else None,
        }
    return results


def write_results_csv(
    path: Path, results_by_label: dict[str, dict[str, dict[str, object]]]
) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "label",
                "formula",
                "runs",
                "successes",
                "timeouts",
                "errors",
                "median_s",
                "p95_s",
            ]
        )
        for label, results in results_by_label.items():
            for formula, data in results.items():
                writer.writerow(
                    [
                        label,
                        formula,
                        data["runs"],
                        data["successes"],
                        data["timeouts"],
                        data["errors"],
                        data["median"],
                        data["p95"],
                    ]
                )


def plot_results(
    formulas: list[str],
    old_results: dict[str, dict[str, object]],
    new_results: dict[str, dict[str, object]],
    timeout: float,
    output_path: Path,
    logy: bool,
) -> None:
    def median_or_timeout(
        results: dict[str, dict[str, object]],
    ) -> tuple[list[float], set[int]]:
        values = []
        timed_out = set()
        for idx, formula in enumerate(formulas):
            median = results[formula]["median"]
            if median is None:
                values.append(timeout)
                timed_out.add(idx)
            else:
                values.append(float(median))
        return values, timed_out

    old_vals, old_timeouts = median_or_timeout(old_results)
    new_vals, new_timeouts = median_or_timeout(new_results)

    fig, ax = plt.subplots(figsize=(14, 6))
    x = range(len(formulas))
    width = 0.4
    old_bars = ax.bar([i - width / 2 for i in x], old_vals, width, label="old")
    new_bars = ax.bar([i + width / 2 for i in x], new_vals, width, label="new")

    for idx in old_timeouts:
        old_bars.patches[idx].set_hatch("//")
        old_bars.patches[idx].set_facecolor("#c0c0c0")
    for idx in new_timeouts:
        new_bars.patches[idx].set_hatch("//")
        new_bars.patches[idx].set_facecolor("#c0c0c0")

    ax.set_xticks(list(x))
    ax.set_xticklabels(formulas, rotation=45, ha="right")
    ax.set_ylabel("Median seconds (timeout capped)")
    ax.set_title(f"Pipeline performance (timeout={timeout}s)")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    if logy:
        ax.set_yscale("log")

    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def load_formulas(path: Path | None) -> list[str]:
    if path is None:
        return list(DEFAULT_FORMULAS)
    formulas = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            formulas.append(line)
    return formulas


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark pipeline performance.")
    parser.add_argument("--old", type=Path, default=Path(__file__).parent / "chem-old")
    parser.add_argument("--new", type=Path, default=Path(__file__).parent / "chem-new")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--stop-after-timeouts", type=int, default=1)
    parser.add_argument("--formula-file", type=Path)
    parser.add_argument(
        "--plot", type=Path, default=Path(__file__).parent / "benchmark.png"
    )
    parser.add_argument(
        "--csv", type=Path, default=Path(__file__).parent / "benchmark.csv"
    )
    parser.add_argument(
        "--json", type=Path, default=Path(__file__).parent / "benchmark.json"
    )
    parser.add_argument("--logy", action="store_true")
    args = parser.parse_args()

    formulas = load_formulas(args.formula_file)

    if not args.old.exists() or not args.new.exists():
        print("Old/new codebase path does not exist.", file=sys.stderr)
        return 2

    old_results = benchmark_codebase(
        args.old, formulas, args.repeats, args.timeout, args.stop_after_timeouts, "old"
    )
    new_results = benchmark_codebase(
        args.new, formulas, args.repeats, args.timeout, args.stop_after_timeouts, "new"
    )

    args.csv.parent.mkdir(parents=True, exist_ok=True)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    write_results_csv(args.csv, {"old": old_results, "new": new_results})

    combined = {"old": old_results, "new": new_results}
    args.json.write_text(json.dumps(combined, indent=2))

    plot_results(formulas, old_results, new_results, args.timeout, args.plot, args.logy)
    print(f"Saved plot to {args.plot}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
