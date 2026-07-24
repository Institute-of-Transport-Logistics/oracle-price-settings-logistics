from bilevelpy.models.constraints.core import Constraint
from bilevelpy.models.utils import get_nodes
from oracle_paper.core.columns import BilevelDataCol
from oracle_paper.variables.decision_variable import ClientDecisionVariable
from oracle_paper.variables.price_variable import PriceVariable


class BigMConstraint(Constraint):
    r"""

    Implements the following Big M constraints defined in [`PS-HLP`][oracle_paper.models.ps_hlp]:


    Requires:

    - [`PriceVariable`][oracle_paper.variables.price_variable.PriceVariable]:
      $p_{ij} \geq 0$

    - [`ClientDecisionVariable`][oracle_paper.variables.decision_variable.ClientDecisionVariable]:
      $y_{ij}^z \in \{0,1\}$

    """

    required_vars = [PriceVariable, ClientDecisionVariable]

    def build(self, model: "BaseModel", **kwargs):
        r"""
        Adds the following constraints to the model:

        $$a_{ij}^z p_{ij} - b_{ij}^z \leq M(1 - y_{ij}^z)
        \quad \forall i,j \in V, z \in \Gamma_{ij}$$

        $$P := \max_{i,j \in V} \frac{b_{ij}^1}{a_{ij}^1} + 1$$

        $$M := \max_{i,j,z} a_{ij}^z \cdot P - \min_{i,j,z} b_{ij}^z$$

        $$p_{ij} \leq P \quad \forall i,j \in V$$
        
        """
        nodes = get_nodes(model)
        data = model.data

        p = model.vars[PriceVariable]
        y = model.vars[ClientDecisionVariable]

        ratios = data[BilevelDataCol.CLIENT_RATIO]
        a = data[BilevelDataCol.TRANSPORT_WEIGHT_CLIENT]
        b = data[BilevelDataCol.BUDGET]

        P = max(ratios.values) + 1
        M = max(a.values) * P - min(b.values)

        for i in nodes:
            for j in nodes:
                model.add_constr(p[i, j] <= P, name=f"p_bound_{i}_{j}")

        for (i, j, z) in data[BilevelDataCol.CLIENT_ID_ROUTE]:
            model.add_constr(
                a[i, j, z] * p[i, j] - b[i, j, z] <= M * (1 - y[i, j, z]),
                name=f"bigM_{i}_{j}_{z}"
            )