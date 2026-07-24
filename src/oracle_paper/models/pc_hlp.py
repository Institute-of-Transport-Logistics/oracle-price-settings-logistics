import gurobipy as gp
from gurobipy import GRB, quicksum

from bilevelpy.data.core import MultiEntityDataset
from bilevelpy.models.core import BaseModel, ModelMetaData
from bilevelpy.models.constraints.hlp_constraints import (
    NumberOfHubsConstraint, SingleAllocationConstraint, AssignmentRestrictionConstraint
)
from bilevelpy.models.utils import get_nodes, transport_cost_hlp
from bilevelpy.models.vars.hlp_vars import AllocationVariable
from bilevelpy.solution.solution_registry import SolutionRegistry

from oracle_paper.core.columns import BilevelDataCol
from oracle_paper.core.names import OraclePaperModelNames
from oracle_paper.variables.recursive_decision_variable import RecursiveClientDecisionVariable
from oracle_paper.variables.recursive_linear_x_y_variable import RecursiveLinearXYVariable
from oracle_paper.constraints.recursive_linearization_constraint import RecursiveLinearizationConstraint

from oracle_paper.solution.pc_hlp_solution import PC_HLPSolution


@SolutionRegistry.register_for(PC_HLPSolution)
class PC_HLP(BaseModel):
    r"""Fast Lagrange Model — recursive client-aggregated formulation.

    Unlike [PS_HLP][oracle_paper.models.ps_hlp.PS_HLP], this model uses
    **aggregated client keys** $(i,j,z)$ where $z$ indexes a *group* of
    original clients. Clients are grouped by route $(i,j)$, ranked, and
    Lagrange multipliers $\lambda_{ij}^z$ are computed recursively over
    segments. Price is **not** a Gurobi variable — it is inferred
    post-solve from the budget/weight ratio of the marginal client.

    **Variables:**

    | Symbol | Reproduces | Variable | Domain |
    |--------|------------|----------|--------|
    | $x_{ik}$ | — | [`AllocationVariable`][bilevelpy.models.vars.hlp_vars.AllocationVariable] | $\{0,1\}$ |
    | $y_{ij}^z$ | — | [`RecursiveClientDecisionVariable`][oracle_paper.variables.recursive_decision_variable.RecursiveClientDecisionVariable] | $\{0,1\}$ |
    | $X_{ijkm}^z$ | $y_{ij}^z \cdot x_{ik} \cdot x_{jm}$ | [`RecursiveLinearXYVariable`][oracle_paper.variables.recursive_linear_x_y_variable.RecursiveLinearXYVariable] | $\{0,1\}$ |

    **Constraints:**

    | Constraint | Reference |
    |------------|-----------|
    | HLP base | [NumberOfHubs][bilevelpy.models.constraints.hlp_constraints.NumberOfHubsConstraint], [SingleAllocation][bilevelpy.models.constraints.hlp_constraints.SingleAllocationConstraint], [AssignmentRestriction][bilevelpy.models.constraints.hlp_constraints.AssignmentRestrictionConstraint] |
    | $y = \sum X$, $X \leq x$ | [`RecursiveLinearizationConstraint`][oracle_paper.constraints.recursive_linearization_constraint.RecursiveLinearizationConstraint] |

    **Objective (maximizes Lagrange-adjusted profit):**

    $$\max \sum_{(i,j,z) \in K} \Bigl(
    \lambda_{ij}^z y_{ij}^z - a_{ij}^z \tilde{c}_{ij}(x) \Bigr)$$

    where $K$ is the set of aggregated client keys and $\lambda_{ij}^z$
    are the recursive Lagrange multipliers.

    Args:
        n_hubs: Number of hubs to open ($p$).
        alpha: Cost scaling factor ($\alpha$).
        data: Dataset with recursive Lagrange multipliers and grouped
            client keys.
    """

    model_metadata = OraclePaperModelNames.PC_HLP
    def __init__(
            self,
            n_hubs: int,
            alpha: float,
            data: MultiEntityDataset,
    ) -> None:
        super().__init__(data)

        self._n_hubs = n_hubs
        self._alpha = alpha

        vars = [AllocationVariable,
                RecursiveClientDecisionVariable,
                RecursiveLinearXYVariable]

        constraints = [
            NumberOfHubsConstraint,
            SingleAllocationConstraint,
            AssignmentRestrictionConstraint,
            RecursiveLinearizationConstraint,
        ]

        self.build(
            variables=vars,
            constraints=constraints,
            n_hubs=n_hubs,
        )

    def _set_objective(self, **kwargs) -> tuple[gp.LinExpr, int]:
        data = self.data

        y = self.vars[RecursiveClientDecisionVariable]
        a = data[BilevelDataCol.SUMMED_LINEAR_WEIGHTS]
        lagrange = data[BilevelDataCol.RECURSIVE_LAGRANGE]

        obj = quicksum(
            y[i, j, z] * lagrange[i, j, z]
            - a[i, j, z] * self.get_transport_cost_sum(i, j, z)
            for (i, j, z) in data[BilevelDataCol.CLIENT_KEYS]
        )

        return obj, GRB.MAXIMIZE

    def get_transport_cost_sum(self, i, j, z) -> gp.LinExpr:
        nodes = get_nodes(self)
        q = self.vars[RecursiveLinearXYVariable]
        return quicksum(
            q[i, j, k, m, z] * transport_cost_hlp(self, i, k, m, j, self._alpha)
            for k in nodes
            for m in nodes
        )

