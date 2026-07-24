"""Optional Julia setup for the PS_BHLP model.

Run via::

    poetry run setup-julia

If Julia isn't found or package installation fails, the script prints a
warning and exits cleanly — the other models (PS_HLP, PC_HLP, PPC_HLP)
don't need Julia at all.
"""

from __future__ import annotations

import json
import subprocess

from oracle_paper._julia import find_julia

_REQUIRED_PACKAGES = ["JuMP", "Gurobi", "BilevelJuMP", "JSON"]


def main() -> None:
    print(":: Julia setup for PS_BHLP ::\n")

    julia = find_julia()
    if julia is None:
        print("Julia not found — skipping Julia package installation.")
        print("PS_HLP, PC_HLP, and PPC_HLP work without Julia.")
        print("To use PS_BHLP, install Julia ≥ 1.10 and re-run this step.")
        print("→ https://julialang.org/downloads/")
        return

    print(f"Julia found at: {julia}")

    packages_str = " ".join(_REQUIRED_PACKAGES)
    print(f"Installing packages: {packages_str}")

    julia_cmd = f'import Pkg; Pkg.add({json.dumps(_REQUIRED_PACKAGES)})'
    result = subprocess.run(
        [julia, "-e", julia_cmd],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("Done — PS_BHLP is ready to use.")
    else:
        print("Julia package installation failed. PS_BHLP won't work yet.")
        print("You can install the packages manually in the Julia REPL:")
        print(f"  import Pkg; Pkg.add({json.dumps(_REQUIRED_PACKAGES)})")
        if result.stderr:
            print(f"\nError details:\n{result.stderr}")


if __name__ == "__main__":
    main()
