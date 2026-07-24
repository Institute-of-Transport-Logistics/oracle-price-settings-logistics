# An Oracle-based Approach for Price-setting Problems in Logistics

Reference implementation and computational artefacts for the paper
**“An Oracle-based Approach for Price-setting Problems in Logistics”**
(Pommerening et al., 2026).

The repository implements the Price-Setting Bilevel Hub Location Problem
(PS-BHLP) and the three approaches evaluated in the paper:

| Model | Description |
|---|---|
| `PS_BHLP` | Direct bilevel reference implementation using BilevelJuMP |
| `PS_HLP` | Compact single-level formulation |
| `PPC_HLP` | Precedence prize-collecting hub-location formulation |
| `PC_HLP` | Reduced prize-collecting hub-location formulation |

The Python implementations are built on top of
[BilevelPy](https://institute-of-transport-logistics.github.io/bilevelpy/).

## Installation

### Requirements

- Python 3.11–3.14
- Poetry
- Gurobi Optimizer 11.0 or newer
- a valid Gurobi licence

Install the project and its dependencies: 

```bash
poetry install
```

Verify:

```bash
poetry run python -c "from oracle_paper.models.ps_hlp import PS_HLP; print('Installation successful')"
```

### Julia (PS_BHLP only)

The **PS_BHLP** model needs Julia ≥ 1.10. Run `poetry run setup-julia` after installing
Julia, or follow the [full Julia setup guide](docs/installation.md#julia-setup-ps_bhlp-only).
The other three models work without Julia.

## Quick Example

The following is a small usage example. It demonstrates the model-building
workflow but does not reproduce the exact experimental configuration from the
paper.


```python
from bilevelpy.core.datasets import Dataset
from bilevelpy.data.builder import DatasetBuilder
from bilevelpy.data.loaders import HLPLoader
from bilevelpy.data.processor import HLPNodeSelector, HLPCostScaling
from bilevelpy.solver import ModelSolver
from oracle_paper.data.generator.bilevel_client_generator import BilevelClientGenerator
from oracle_paper.data.processor.client_ranker import LinearClientRanker
from oracle_paper.models.ps_hlp import PS_HLP

dataset = (
    DatasetBuilder()
    .pipe(HLPLoader(Dataset.CAB100))
    .pipe(HLPNodeSelector(n_nodes=10))
    .pipe(HLPCostScaling(scaling_factor=100))
    .pipe(BilevelClientGenerator(clients_per_route=5))
    .pipe(LinearClientRanker())
    .build()
)

model = PS_HLP(n_hubs=2, alpha=0.5, data=dataset)
solution = ModelSolver(model).solve()
print(solution)
```

## Reproducing the experiments

Start the interactive benchmarking tool with:

```bash
poetry run benchmark
```

![Benchmarking demo](docs/demo_benchmarking.gif)

Pre-computed results are in [`reproduce/benchmark_results/`](reproduce/benchmark_results/).
See the [reproduction guide](reproduce/guide_to_reproducing_paper.pdf) for full details.

The paper experiments use fixed instance-generation and solver parameters.
Changing the client generator, random seeds, cost scaling, or solver
configuration may produce results that differ from those reported in the
paper.

## Documentation

The full documentation contains the problem formulation, implemented solution
approaches, installation instructions, and API reference:
[docs](https://institute-of-transport-logistics.github.io/oracle-price-settings-logistics) 


## Citation

Citation metadata is available through
[`CITATION.cff`](CITATION.cff).

When using this repository, please cite both the software release and the
associated paper.

## License

This software is made available under the
[PolyForm Noncommercial License 1.0.0](LICENSE).

Commercial use requires separate permission from the rights holder.


