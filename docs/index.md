# Oracle Paper

Documentation of the implemented code for the paper:
*"An Oracle-based Approach for Price-setting Problems in Logistics"*
(N. Pommerening, M. Hügging, D. Henke, C. Buchheim, U. Clausen, 2026).



Built on top of [BilevelPy](https://github.com/Institute-of-Transport-Logistics/bilevelpy/).

## Quick Navigation

| Section | Description                                                                                     |
|---------|-------------------------------------------------------------------------------------------------|
| [Problem Formulation](problem.md) | The PS-BHLP model: leader, follower, and full bilevel formulation                               |
| [Solution Approaches](approaches.md) | Three approaches: Big-M, Lagrange, and Fast                                                     |
| [API Reference](reference/) | Auto-generated documentation for every module, class, and function  with reference to the paper |

---

## Solution Approaches at a Glance

All three approaches solve the **same** bilevel price-setting problem.
They differ in **how** with large performance gaps.

| Paper Name | Code Convention | Code | Method                                                                                 | Speed |
|------------|-----------------|------|----------------------------------------------------------------------------------------|-------|
| **PS-HLP** | Big M | [`PS_HLP`](reference/src/oracle_paper/models/ps_hlp.md) | Compact single-level formulation from Section 2, linearized as described in Section 5. | Slowest |
| **PPC-HLP** | Lagrange | [`PPC_HLP`](reference/src/oracle_paper/models/ppc_hlp.md) | Lagrangian decomposition with precedence constraints                                   | Faster |
| **PC-HLP** | Fast Lagrange | [`PC_HLP`](reference/src/oracle_paper/models/pc_hlp.md) | Lagrangian with merged customers — no precedence (Lemma 3)                             | **Fastest** |

See [Solution Approaches](approaches.md) for the full methodology,
theoretical results, and computational benchmarks.

---

## Variables


| Notation | Reproduces | Code Name | API Reference                                                                                            | Used In |
|----------|------------|-----------|----------------------------------------------------------------------------------------------------------|---------|
| $x_{ik}$ | — | `AllocationVariable` | [bilevelpy.core](https://institute-of-transport-logistics.github.io/bilevelpy/reference/bilevelpy/models/vars/#bilevelpy.models.vars.AllocationVariable)| All models |
| $p_{ij}$ | — | `PriceVariable` | [`PriceVariable`](reference/src/oracle_paper/variables/price_variable.md)                                | PS-HLP |
| $y_{ij}^z$ | — | `ClientDecisionVariable` | [`ClientDecisionVariable`](reference/src/oracle_paper/variables/decision_variable.md)                    | PS-HLP, PPC-HLP |
| $\bar{y}_{ij}^z$ | — | `RecursiveClientDecisionVariable` | [`RecursiveClientDecisionVariable`](reference/src/oracle_paper/variables/recursive_decision_variable.md) | PC-HLP (merged clients) |
| $X_{ijkm}^z$ | $y_{ij}^z \cdot x_{ik} \cdot x_{jm}$ | `LinearXYVariable` | [`LinearXYVariable`](reference/src/oracle_paper/variables/linear_x_y_variable.md)                        | PS-HLP, PPC-HLP |
| $X_{ijkm}^z$ | $y_{ij}^z \cdot x_{ik} \cdot x_{jm}$ | `RecursiveLinearXYVariable` | [`RecursiveLinearXYVariable`](reference/src/oracle_paper/variables/recursive_linear_x_y_variable.md)     | PC-HLP (merged clients) |

---

## Constraints


| Constraint | Code                                                                                                                                                                  | Used In | Description               |
|------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|---------------------------|
| Exactly $\kappa$ hubs | [`NumberOfHubsConstraint`](https://institute-of-transport-logistics.github.io/bilevelpy/reference/bilevelpy/models/vars/#bilevelpy.models.vars.AllocationVariable)    | All models | *(bilevelpy core)*        |
| Single allocation | [`SingleAllocationConstraint`](https://institute-of-transport-logistics.github.io/bilevelpy/reference/bilevelpy/models/vars/#bilevelpy.models.vars.AllocationVariable) | All models | *(bilevelpy core)*        |
| Assignment restriction | [`AssignmentRestrictionConstraint`](https://institute-of-transport-logistics.github.io/bilevelpy/reference/bilevelpy/models/vars/#bilevelpy.models.vars.AllocationVariable) | All models | *(bilevelpy core)*        |
| $y = \sum X$, $X \leq x$ | [`LinearizationConstraint`](reference/src/oracle_paper/constraints/linearization_constraint.md)                                                                       | PS-HLP, PPC-HLP | Section 5.1 linearization |
| Big-M coupling | [`BigMConstraint`](reference/src/oracle_paper/constraints/big_m_constraint.md)                                                                                        | PS-HLP | Section 2 - PS-HLP        |
| Precedence $y^z \geq y^{z+1}$ | [`PrecedenceConstraint`](reference/src/oracle_paper/constraints/precedence_constraint.md)                                                                             | PPC-HLP | Section 3                 |
| Recursive linearization | [`RecursiveLinearizationConstraint`](reference/src/oracle_paper/constraints/recursive_linearization_constraint.md)                                                    | PC-HLP | Section 5.1 linearization  |

---

## Quick Example

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