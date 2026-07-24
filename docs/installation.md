# Installation

## Prerequisites

- Python 3.11+
- [BilevelPy](https://pypi.org/project/bilevelpy/) installed
- Gurobi 11+ with a valid license (`GRB_LICENSE_FILE` must be set)

## Install via Poetry

```bash
git clone https://github.com/Institute-of-Transport-Logistics/oracle-price-settings-logistics.git
cd oracle-price-settings-logistics
poetry install
```

## Verify

```bash
python -c "from oracle_paper.models.ps_hlp import PS_HLP; print('OK')"
```

## Julia setup (PS_BHLP only)

The **PS_BHLP** model generates its MIP formulation via
[BilevelJuMP](https://github.com/joaquimg/BilevelJuMP.jl) in Julia.
Julia is **not** required for the other models (PS_HLP, PC_HLP, PPC_HLP).

### 1. Install Julia

Download and install **Julia 1.10 LTS** from [julialang.org/downloads](https://julialang.org/downloads/).

On Windows, enable the *"Add Julia to PATH"* checkbox during installation.
If you forget, the model auto-detects common install directories:

- `%LOCALAPPDATA%\Programs\Julia-*`
- `C:\Program Files\Julia-*`

### 2. Install Julia packages

```bash
poetry run setup-julia
```

This one-liner checks for Julia and installs JuMP, Gurobi, BilevelJuMP,
and JSON. If Julia isn't around the script just warns you and moves on
— PS_HLP, PC_HLP, and PPC_HLP don't need it anyway.

**Manual alternative** — open a Julia REPL and run:

```julia
import Pkg
Pkg.add(["JuMP", "Gurobi", "BilevelJuMP", "JSON"])
```

### 3. Gurobi license

Julia must see the same Gurobi license as Python. If your
`GRB_LICENSE_FILE` environment variable is already set globally,
Julia picks it up automatically. Otherwise, set it before running
any PS_BHLP benchmark:

```bash
set GRB_LICENSE_FILE=C:\path\to\gurobi.lic   # Windows
export GRB_LICENSE_FILE=/path/to/gurobi.lic   # Linux / macOS
```

### 4. Quick smoke test

```bash
python src/oracle_paper/examples/ps_bhlp.py
```

Expected output: a small instance (3 nodes, 2 hubs, 2 clients per route)
solves in a few seconds and prints solver metadata.