from bilevelpy.models.constraints.core import Constraint
from oracle_paper.core.columns import BilevelDataCol
from oracle_paper.variables.decision_variable import ClientDecisionVariable


class PrecedenceConstraint(Constraint):
    r"""Precedence constraint defined in [`PPC-HLP`][oracle_paper.models.ppc_hlp]

    Only used in the [`PPC-HLP`][oracle_paper.models.ppc_hlp] model. The [`PC-HLP`][oracle_paper.models.pc_hlp] model avoids these
    constraints by merging customers.


    Requires:

    - [`ClientDecisionVariable`][oracle_paper.variables.decision_variable.ClientDecisionVariable]

    """

    required_vars = [ClientDecisionVariable]

    def build(self, model: "BaseModel", **kwargs):
        r"""
        Adds the following constraint to the model:

        $$
        y_{ij}^z \geq y_{ij}^{z+1} \quad \forall (i,j,z), (i,j,z+1) \in \Gamma_{ij}
        $$

        """
        data = model.data
        y = model.vars[ClientDecisionVariable]

        for (i, j, z) in data[BilevelDataCol.CLIENT_ID_ROUTE]:
            if (i, j, z + 1) in data[BilevelDataCol.CLIENT_ID_ROUTE]:
                model.add_constr(
                    y[i, j, z] >= y[i, j, z + 1],
                    name=f"precedence_{i}_{j}_{z}_{z + 1}"
                )