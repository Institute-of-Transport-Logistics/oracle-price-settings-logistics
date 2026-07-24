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
from oracle_paper.variables.decision_variable import ClientDecisionVariable
from oracle_paper.variables.linear_x_y_variable import LinearXYVariable
from oracle_paper.constraints.linearization_constraint import LinearizationConstraint
from oracle_paper.constraints.precedence_constraint import PrecedenceConstraint

from oracle_paper.solution.ppc_hlp_solution import PPC_HLPSolution


@SolutionRegistry.register_for(PPC_HLPSolution)
class PPC_HLP(BaseModel):
    r"""Lagrange Model — standard Lagrange multiplier decomposition.

    Uses Lagrange multipliers $\lambda_{ij}^z$ to decompose the bilevel
    problem. Price is inferred post-solve (no price variable). Includes
    a precedence constraint ordering client decisions.

    **Variables:**

    | Symbol | Reproduces | Variable | Domain |
    |--------|------------|----------|--------|
    | $x_{ik}$ | — | [`AllocationVariable`][bilevelpy.models.vars.hlp_vars.AllocationVariable] | $\{0,1\}$ |
    | $y_{ij}^z$ | — | [`ClientDecisionVariable`][oracle_paper.variables.decision_variable.ClientDecisionVariable] | $\{0,1\}$ |
    | $X_{ijkm}^z$ | $y_{ij}^z \cdot x_{ik} \cdot x_{jm}$ | [`LinearXYVariable`][oracle_paper.variables.linear_x_y_variable.LinearXYVariable] | $\{0,1\}$ |

    **Constraints:**

    | Constraint | Reference |
    |------------|-----------|
    | HLP base | [NumberOfHubs][bilevelpy.models.constraints.hlp_constraints.NumberOfHubsConstraint], [SingleAllocation][bilevelpy.models.constraints.hlp_constraints.SingleAllocationConstraint], [AssignmentRestriction][bilevelpy.models.constraints.hlp_constraints.AssignmentRestrictionConstraint] |
    | $y = \sum X$, $X \leq x$ | [`LinearizationConstraint`][oracle_paper.constraints.linearization_constraint.LinearizationConstraint] |
    | $y_{ij}^z \geq y_{ij}^{z+1}$ | [`PrecendenceConstraint`][oracle_paper.constraints.precedence_constraint.PrecendenceConstraint] |

    **Objective (maximizes Lagrange-adjusted profit):**

    $$\max \sum_{(i,j,z) \in M} \Bigl(
    \lambda_{ij}^z y_{ij}^z - a_{ij}^z \tilde{c}_{ij}(x) \Bigr)$$

    **Precedence constraint:**

    $$y_{ij}^z \geq y_{ij}^{z+1} \quad \forall (i,j,z),(i,j,z+1) \in M$$

    Ensures clients on the same route are accepted in ranked order
    (highest budget/weight ratio first).

    Args:
        n_hubs: Number of hubs to open ($p$).
        alpha: Cost scaling factor ($\alpha$).
        data: Dataset with Lagrange multipliers and client data.
    """

    model_metadata = OraclePaperModelNames.PPC_HLP
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
                    ClientDecisionVariable,
                    LinearXYVariable]

        constraints = [
            NumberOfHubsConstraint,
            SingleAllocationConstraint,
            AssignmentRestrictionConstraint,
            LinearizationConstraint,
            PrecedenceConstraint,
        ]

        self.build(
            variables=vars,
            constraints=constraints,
            n_hubs=n_hubs,
        )

    def _set_objective(self, **kwargs) -> tuple[gp.LinExpr, int]:
        data = self.data

        y = self.vars[ClientDecisionVariable]

        a = data[BilevelDataCol.TRANSPORT_WEIGHT_CLIENT]
        lagrange = data[BilevelDataCol.LAGRANGE]

        obj = quicksum(
            y[i, j, z] * lagrange[i, j, z]
            - a[i, j, z] * self.get_transport_cost_sum(i, j, z)
            for (i, j, z) in data[BilevelDataCol.CLIENT_ID_ROUTE]
        )

        return obj, GRB.MAXIMIZE

    def get_transport_cost_sum(self, i, j, z) -> gp.LinExpr:
        nodes = get_nodes(self)
        q = self.vars[LinearXYVariable]
        return quicksum(
            q[i, j, k, m, z] * transport_cost_hlp(self, i, k, m, j, self._alpha)
            for k in nodes
            for m in nodes
        )

