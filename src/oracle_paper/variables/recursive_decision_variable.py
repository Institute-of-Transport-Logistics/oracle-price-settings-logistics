from gurobipy import tupledict, GRB

from bilevelpy.models.meta import VariableMetaData
from bilevelpy.models.vars.core import Variable
from bilevelpy.core.columns import DataCol
from oracle_paper.core.columns import BilevelDataCol


class RecursiveClientDecisionVariable(Variable):
    r"""Aggregated client decision variable for the PC-HLP model.

    $$y_{ij}^z \in \{0,1\} \quad \forall (i,j,z) \in K$$

    where $K$ is the set of **grouped** client keys. Unlike the flat
    [`ClientDecisionVariable`][oracle_paper.variables.decision_variable.ClientDecisionVariable],
    this variable indexes *aggregated* clients — $z$ represents a merged
    group of original clients. Keys are read from
    [`BilevelDataCol.CLIENT_KEYS`][oracle_paper.core.columns.BilevelDataCol].
    """

    var_metadata = VariableMetaData(
        value="recursive_y",
        display_name="Recursive Decision of the client",
        identifiers=[DataCol.START_NODE,
                     DataCol.END_NODE,
                     BilevelDataCol.CLIENT_ID_ROUTE]
    )

    def build(self, model: "BaseModel") -> tupledict:
        client_keys = [(i,j,z) for (i, j, z), keys in model
                                                                .data[BilevelDataCol.CLIENT_KEYS].items()]

        return model.model.addVars(
              client_keys,
              vtype=GRB.BINARY,
              name=str(self.var_metadata),
          )