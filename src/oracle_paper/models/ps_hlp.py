import gurobipy as gp
from gurobipy import GRB, quicksum

from bilevelpy.models.core import BaseModel, ModelMetaData
from bilevelpy.data.core import MultiEntityDataset
from bilevelpy.models.constraints.hlp_constraints import (NumberOfHubsConstraint, SingleAllocationConstraint, AssignmentRestrictionConstraint)
from bilevelpy.models.utils import get_nodes, transport_cost_hlp
from bilevelpy.models.vars.hlp_vars import AllocationVariable
from bilevelpy.solution.solution_registry import SolutionRegistry


from oracle_paper.core.names import OraclePaperModelNames
from oracle_paper.solution.ps_hlp_solution import PS_HLPSolution
from oracle_paper.core.columns import BilevelDataCol
from oracle_paper.variables.decision_variable import ClientDecisionVariable
from oracle_paper.variables.linear_x_y_variable import LinearXYVariable
from oracle_paper.variables.price_variable import PriceVariable
from oracle_paper.constraints.big_m_constraint import BigMConstraint
from oracle_paper.constraints.linearization_constraint import LinearizationConstraint

@SolutionRegistry.register_for(PS_HLPSolution)
class PS_HLP(BaseModel):
    r"""Price-Setting Hub Location Problem with Big-M linearization.

    The leader (hub operator) sets prices $p_{ij}$ and allocates hubs
    $x_{ik}$. The follower (clients) chooses routes $y_{ij}^z$ to
    maximize their utility.

    **Variables:**

    | Symbol | Reproduces | Variable | Domain |
    |--------|------------|----------|--------|
    | $x_{ik}$ | — | [`AllocationVariable`][bilevelpy.models.vars.hlp_vars.AllocationVariable] | $\{0,1\}$ |
    | $y_{ij}^z$ | — | [`ClientDecisionVariable`][oracle_paper.variables.decision_variable.ClientDecisionVariable] | $\{0,1\}$ |
    | $X_{ijkm}^z$ | $y_{ij}^z \cdot x_{ik} \cdot x_{jm}$ | [`LinearXYVariable`][oracle_paper.variables.linear_x_y_variable.LinearXYVariable] | $\{0,1\}$ |
    | $p_{ij}$ | — | [`PriceVariable`][oracle_paper.variables.price_variable.PriceVariable] | $\mathbb{R}_{\geq 0}$ |

    **Constraints:**

    | Constraint | Reference |
    |------------|-----------|
    | Exactly $p$ hubs open | [`NumberOfHubsConstraint`][bilevelpy.models.constraints.hlp_constraints.NumberOfHubsConstraint] |
    | Each node to one hub | [`SingleAllocationConstraint`][bilevelpy.models.constraints.hlp_constraints.SingleAllocationConstraint] |
    | Only assigned to open hubs | [`AssignmentRestrictionConstraint`][bilevelpy.models.constraints.hlp_constraints.AssignmentRestrictionConstraint] |
    | $y = \sum X$, $X \leq x$ | [`LinearizationConstraint`][oracle_paper.constraints.linearization_constraint.LinearizationConstraint] |
    | Price-revenue coupling | [`BigMConstraint`][oracle_paper.constraints.big_m_constraint.BigMConstraint] |

    **Objective (leader maximizes profit):**

    $$\max \sum_{i,j \in V} \sum_{z \in M_{ij}} a_{ij}^z \;
    y_{ij}^z \bigl(p_{ij} - \tilde{c}_{ij}(x)\bigr)$$

    where $\tilde{c}_{ij}(x) = \sum_{k,m \in V}
    X_{ijkm}^z \bigl(\alpha\, c_{ik} + \alpha\, c_{km} + c_{mj}\bigr)$
    is the transport cost through hubs $k,m$.

    **Big-M constraint (couples price and decision):**

    $$a_{ij}^z p_{ij} - b_{ij}^z \leq M(1 - y_{ij}^z)$$

    $$P := \max_{i,j} \frac{b_{ij}^1}{a_{ij}^1} + 1, \qquad
    M := \max_{i,j,z} a_{ij}^z \cdot P - \min_{i,j,z} b_{ij}^z$$

    $$p_{ij} \leq P \quad \forall i,j \in V$$

    Args:
        n_hubs: Number of hubs to open ($p$).
        alpha: Cost scaling factor ($\alpha$).
        data: Dataset with client weights, budgets, and transport costs.
    """
    model_metadata = OraclePaperModelNames.PS_HLP
    def __init__(
        self,
        n_hubs: int,
        alpha: float,
        data: MultiEntityDataset,
    ) -> None:
        super().__init__(data)
        self._n_hubs = n_hubs
        self._alpha = alpha

        vars = [
            AllocationVariable,
            ClientDecisionVariable,
            LinearXYVariable,
            PriceVariable,
        ]

        constraints = [
            NumberOfHubsConstraint,
            SingleAllocationConstraint,
            AssignmentRestrictionConstraint,
            LinearizationConstraint,
            BigMConstraint,
        ]

        self.build(
            variables=vars,
            constraints=constraints,
            n_hubs=n_hubs,
        )

    def _set_objective(self, **kwargs) -> tuple[gp.LinExpr, int]:
        data = self.data
        p = self.vars[PriceVariable]
        y = self.vars[ClientDecisionVariable]
        a = data[BilevelDataCol.TRANSPORT_WEIGHT_CLIENT]

        obj = quicksum(
            a[i, j, z]
            * y[i, j, z]
            * (p[i, j] - self.get_transport_cost_sum(i, j, z))
            for (i, j, z) in data[BilevelDataCol.CLIENT_ID_ROUTE]
        )

        return obj, GRB.MAXIMIZE

    def get_transport_cost_sum(self, i, j, z) -> gp.LinExpr:
        r"""Compute the transport cost $\tilde{c}_{ij}(x)$ for a route.

        $$\tilde{c}_{ij}(x) = \sum_{k \in V} \sum_{m \in V}
        X_{ijkm}^z \bigl(\alpha c_{ik} + \alpha c_{km} + c_{mj}\bigr)$$
        """
        nodes = get_nodes(self)
        q = self.vars[LinearXYVariable]
        return quicksum(
            q[i, j, k, m, z]
            * transport_cost_hlp(self, i, k, m, j, self._alpha)
            for k in nodes
            for m in nodes
        )
