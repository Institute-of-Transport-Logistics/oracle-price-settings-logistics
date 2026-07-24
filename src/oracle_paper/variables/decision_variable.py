from gurobipy import tupledict, GRB

from bilevelpy.models.meta import VariableMetaData
from bilevelpy.models.vars.core import Variable
from bilevelpy.core.columns import DataCol
from oracle_paper.core.columns import BilevelDataCol


class ClientDecisionVariable(Variable):
    r"""Client (follower) decision variable for bilevel hub location.

    Binary variable that captures whether client $z$ on route $(i,j)$
    accepts the price offered by the leader:

    $$y_{ij}^z \in \{0,1\} \quad \forall i,j \in V, z \in M_{ij}$$

    The client accepts if and only if their utility is non-negative:
    $a_{ij}^z p_{ij} - b_{ij}^z \geq 0$.

    The variable is indexed by ``(i, j, z)``: origin $i$, destination $j$,
    and client index $z$ on that route.
    """

    var_metadata = VariableMetaData(
        value="y",
        display_name="Decision of the client",
        identifiers=[
            DataCol.START_NODE,
            DataCol.END_NODE,
            BilevelDataCol.CLIENT_ID_ROUTE,
        ],
    )

    def build(self, model: "BaseModel") -> tupledict:
        """Create binary Gurobi variables over all client routes."""
        client_keys = model.data[BilevelDataCol.CLIENT_ID_ROUTE]
        return model.model.addVars(
            client_keys,
            vtype=GRB.BINARY,
            name=str(self.var_metadata),
        )

