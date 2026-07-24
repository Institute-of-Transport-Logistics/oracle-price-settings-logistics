from bilevelpy.solution.core import BaseModelSolution

from oracle_paper.solution.mixins.hub_location_mixin import HubLocationMixin
from oracle_paper.solution.mixins.decision_mixin import DecisionMixin
from oracle_paper.solution.mixins.price_mixin import PriceMixin


class PS_HLPSolution(
    PriceMixin,
    DecisionMixin,
    HubLocationMixin,
    BaseModelSolution,
):
    """Solution for the PS-HLP (Big M) model.

    Unlike the Lagrange-based models, PS-HLP has price as an explicit
    Gurobi variable, so no inference is needed. The price values are
    extracted directly from the solver.

    Mixin composition:

    - [`PriceMixin`][oracle_paper.solution.mixins.PriceMixin] — price table
    - [`DecisionMixin`][oracle_paper.solution.mixins.DecisionMixin] — active routes
    - [`HubLocationMixin`][oracle_paper.solution.mixins.HubLocationMixin] — hub status
    - [`BaseModelSolution`][bilevelpy.solution.core.BaseModelSolution] —
      base variable extraction
    """

    pass