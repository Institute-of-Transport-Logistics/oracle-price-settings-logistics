from bilevelpy.models.constraints.core import Constraint
from bilevelpy.models.core import BaseModel
from bilevelpy.models.utils import get_nodes
from bilevelpy.models.vars.hlp_vars import AllocationVariable
from gurobipy import quicksum

from oracle_paper.core.columns import BilevelDataCol
from oracle_paper.variables.recursive_decision_variable import RecursiveClientDecisionVariable
from oracle_paper.variables.recursive_linear_x_y_variable import RecursiveLinearXYVariable


class RecursiveLinearizationConstraint(Constraint):
    r"""Recursive (merged-client) linearization for the PC-HLP model.

    Reproduces the cubic term:

    $$X_{ijkl}^z \;\widehat{=}\; y_{ij}^z \cdot x_{ik} \cdot x_{jl}$$

    Same structure as [LinearizationConstraint][oracle_paper.constraints.linearization_constraint.LinearizationConstraint]
    but operates on **aggregated** client keys from
    [`BilevelDataCol.CLIENT_KEY`][oracle_paper.core.columns.BilevelDataCol].



    Requires:
    - [`AllocationVariable`][bilevelpy.models.vars.hlp_vars.AllocationVariable]
    - [`RecursiveClientDecisionVariable`][oracle_paper.variables.recursive_decision_variable.RecursiveClientDecisionVariable]
    - [`RecursiveLinearXYVariable`][oracle_paper.variables.recursive_linear_x_y_variable.RecursiveLinearXYVariable]

    """

    required_vars = [
        AllocationVariable,
        RecursiveClientDecisionVariable,
        RecursiveLinearXYVariable,
    ]

    def build(self, model: "BaseModel", **kwargs):
        r"""Adds the following constraint to the model:

            $$y_{ij}^z = \sum_{k,l \in V} X_{ijkm}^z \quad \forall (i,j,z) \in K$$

            $$\sum_{l} X_{ijkm}^z \leq x_{ik} \quad \sum_{k} X_{ijkm}^z \leq x_{jl}$$

        """
        nodes = get_nodes(model)
        client_keys = [(i, j, z) for (i, j, z), _ in model.data[BilevelDataCol.CLIENT_KEYS].items()]

        x = model.vars[AllocationVariable]
        q = model.vars[RecursiveLinearXYVariable]
        y = model.vars[RecursiveClientDecisionVariable]

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
