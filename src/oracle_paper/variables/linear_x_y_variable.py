from gurobipy import tupledict, GRB

from bilevelpy.models.meta import VariableMetaData
from bilevelpy.models.utils import get_nodes
from bilevelpy.models.vars.core import Variable
from bilevelpy.core.columns import DataCol
from oracle_paper.core.columns import BilevelDataCol


class LinearXYVariable(Variable):
    r"""Linearization variable $X_{ijkm}^z$ that reproduces the cubic term.

    $$X_{ijkm}^z \;\widehat{=}\; y_{ij}^z \cdot x_{ik} \cdot x_{jm}$$

    $$X_{ijkm}^z \in \{0,1\} \quad \forall i,j,k,m \in V, z \in M_{ij}$$

    Used in PS-HLP and PPC-HLP. The four node indices represent:
    origin $i$, destination $j$, first hub $k$, second hub $m$.
    $z$ is the client index on route $(i,j)$.

    Related:
    - [`LinearizationConstraint`][oracle_paper.constraints.linearization_constraint.LinearizationConstraint]
    - [`ClientDecisionVariable`][oracle_paper.variables.decision_variable.ClientDecisionVariable]
    """

    var_metadata = VariableMetaData(
        value="quadratic",
        display_name="Linearization variable",
        identifiers=[
            DataCol.START_NODE, DataCol.END_NODE,
            DataCol.START_NODE, DataCol.END_NODE,
            BilevelDataCol.CLIENT_ID_ROUTE,
        ],
    )

    def build(self, model: "BaseModel") -> tupledict:
        nodes = get_nodes(model)
        client_keys = (model.data[BilevelDataCol.CLIENT_ID_ROUTE])
        return model.model.addVars(
            ((i, j, k, l, z)
             for (i, j, z)in client_keys
                for k in nodes
                    for l in nodes),
            vtype=GRB.BINARY,
            name=str(self.var_metadata),
        )