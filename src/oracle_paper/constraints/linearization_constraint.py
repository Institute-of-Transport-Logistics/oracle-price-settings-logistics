from bilevelpy.models.constraints.core import Constraint
from bilevelpy.models.utils import get_nodes
from bilevelpy.models.vars.hlp_vars import AllocationVariable
from gurobipy import quicksum

from oracle_paper.core.columns import BilevelDataCol
from oracle_paper.variables.decision_variable import ClientDecisionVariable
from oracle_paper.variables.linear_x_y_variable import LinearXYVariable

class LinearizationConstraint(Constraint):
    r"""

    Implements the linearization from Section 5.1 of the paper, which
    replaces the cubic term with binary variables:

    $$X_{ijkl}^z \;\widehat{=}\; y_{ij}^z \cdot x_{ik} \cdot x_{jl}$$

    Used in both [`PS-HLP`][oracle_paper.models.ps_hlp] and [`PPC-HLP`][oracle_paper.models.ppc_hlp] .

    Requires:
    - [`AllocationVariable`][bilevelpy.models.vars.hlp_vars.AllocationVariable]
    - [`ClientDecisionVariable`][oracle_paper.variables.decision_variable.ClientDecisionVariable]
    - [`LinearXYVariable`][oracle_paper.variables.linear_x_y_variable.LinearXYVariable]
    """

    required_vars = [AllocationVariable, ClientDecisionVariable, LinearXYVariable]

    def build(self, model: "BaseModel", **kwargs):
        r"""

        Adds the following constraints to the model:

        $$y_{ij}^z = \sum_{k \in V} \sum_{l \in V}
        X_{ijkm}^z \quad \forall i,j \in V, z \in \Gamma_{ij}$$

        $$\sum_{l \in V} X_{ijkm}^z \leq x_{ik}
        \quad \forall i,j,k \in V, z \in \Gamma_{ij}$$

        $$\sum_{k \in V} X_{ijkm}^z \leq x_{jl}
        \quad \forall i,j,l \in V, z \in \Gamma_{ij}$$

        """

        nodes = get_nodes(model)
        client_keys = (model.data[BilevelDataCol.CLIENT_ID_ROUTE])

        x = model.vars[AllocationVariable]
        q = model.vars[LinearXYVariable]
        y = model.vars[ClientDecisionVariable]

        for (i, j, z) in client_keys:
            model.add_constr(
                quicksum(q[i, j, k, l, z] for k in nodes for l in nodes) == y[i, j, z],
                name=f"lin_y_{i}_{j}_{z}"
            )
            for k in nodes:
                model.add_constr(
                    quicksum(q[i, j, k, l, z] for l in nodes) <= x[i, k],
                    name=f"lin_x1_{i}_{j}_{z}_{k}"
                )
            for l in nodes:
                model.add_constr(
                    quicksum(q[i, j, k, l, z] for k in nodes) <= x[j, l],
                    name=f"lin_x2_{i}_{j}_{z}_{l}"
                )
