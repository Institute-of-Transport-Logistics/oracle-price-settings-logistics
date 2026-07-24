from gurobipy import tupledict, GRB

from bilevelpy.models.meta import VariableMetaData
from bilevelpy.models.utils import get_nodes
from bilevelpy.models.vars.core import Variable
from bilevelpy.core.columns import DataCol
from oracle_paper.core.columns import BilevelDataCol


class RecursiveLinearXYVariable(Variable):
    r"""Recursive linearization variable for the PC-HLP model.

    Reproduces the cubic term for merged (aggregated) clients:

    $$X_{ijkm}^z \;\widehat{=}\; y_{ij}^z \cdot x_{ik} \cdot x_{jm}$$

    $$X_{ijkm}^z \in \{0,1\} \quad \forall (i,j,z) \in K$$

    Same structure as
    [`LinearXYVariable`][oracle_paper.variables.linear_x_y_variable.LinearXYVariable]
    but uses aggregated client keys from
    [`BilevelDataCol.CLIENT_KEYS`][oracle_paper.core.columns.BilevelDataCol].

    Related:
    - [`RecursiveLinearizationConstraint`][oracle_paper.constraints.recursive_linearization_constraint.RecursiveLinearizationConstraint]
    """

    var_metadata = VariableMetaData(
        value="recursive_quadratic",
        display_name="Recursive Linearization variable",
        identifiers=[
            DataCol.START_NODE, DataCol.END_NODE,
            DataCol.START_NODE, DataCol.END_NODE,
            BilevelDataCol.CLIENT_ID_ROUTE,
        ],
    )

    def build(self, model: "BaseModel") -> tupledict:
        nodes = get_nodes(model)
        client_keys = [(i,j,z) for (i, j, z), keys in model
                                                                .data[BilevelDataCol.CLIENT_KEYS].items()]
        return model.model.addVars(
            ((i, j, k, l, z)
             for (i, j, z)in client_keys
                for k in nodes
                    for l in nodes),
            vtype=GRB.BINARY,
            name=str(self.var_metadata),
        )