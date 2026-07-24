from gurobipy import tupledict, GRB

from bilevelpy.models.meta import VariableMetaData
from bilevelpy.models.utils import get_nodes
from bilevelpy.models.vars.core import Variable
from bilevelpy.core.columns import DataCol

class PriceVariable(Variable):
    r"""Price variable for the PS-HLP (Big M) model.

    Continuous non-negative variable representing the price the leader
    (hub operator) charges for transport on route $(i,j)$:

    $$p_{ij} \geq 0 \quad \forall i,j \in V$$

    Works together with:
    - [`ClientDecisionVariable`][oracle_paper.variables.decision_variable.ClientDecisionVariable]
    - [`BigMConstraint`][oracle_paper.constraints.big_m_constraint.BigMConstraint]
    """

    var_metadata = VariableMetaData(
        value="p",
        display_name="Price",
        identifiers=[DataCol.START_NODE, DataCol.END_NODE],
    )

    def build(self, model: "BaseModel") -> tupledict:
        """Create $|V| \times |V|$ continuous non-negative Gurobi variables."""
        nodes = get_nodes(model)
        return model.model.addVars(
            nodes, nodes,
            vtype=GRB.CONTINUOUS,
            lb=0,
            name=str(self.var_metadata),
        )
