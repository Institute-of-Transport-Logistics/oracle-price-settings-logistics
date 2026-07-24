"""Variable metadata identifiers for the Oracle Paper benchmark UI.

Collects the [`VariableMetaData`][bilevelpy.models.meta.VariableMetaData]
references for all variable types used in the paper. The benchmark UI can
list and exclude variables from solution comparisons without needing to
import the full variable classes at startup.
"""

from oracle_paper.variables.linear_x_y_variable import LinearXYVariable
from oracle_paper.variables.recursive_linear_x_y_variable import (
    RecursiveLinearXYVariable,
)
from oracle_paper.variables.price_variable import PriceVariable
from oracle_paper.variables.decision_variable import ClientDecisionVariable
from oracle_paper.variables.recursive_decision_variable import (
    RecursiveClientDecisionVariable,
)


class BilevelVars:
    """Registry of [`VariableMetaData`][bilevelpy.models.meta.VariableMetaData]
    instances for the benchmark UI.

    Each attribute exposes the ``var_metadata`` of a variable class so the
    UI can render it (via ``display_name``) and filter it out of solution
    comparisons (via equality checks against extracted variables).

    Attributes:
        LINEAR_X_Y: Standard linearization variable $X_{ijkm}^z$.
        LINEAR_BILEVEL_X: Recursive (aggregated) linearization variable.
        PRICE: Price variable $p_{ij}$ (PS_HLP only).
        CLIENT_DECISION: Client decision variable $y_{ij}^z$.
        RECURSIVE_CLIENT_DECISION: Aggregated client decision for PC-HLP.
    """

    LINEAR_X_Y = LinearXYVariable.var_metadata
    LINEAR_BILEVEL_X = RecursiveLinearXYVariable.var_metadata
    PRICE = PriceVariable.var_metadata
    CLIENT_DECISION = ClientDecisionVariable.var_metadata
    RECURSIVE_CLIENT_DECISION = RecursiveClientDecisionVariable.var_metadata