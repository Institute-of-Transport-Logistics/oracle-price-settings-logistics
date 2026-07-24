from bilevelpy.solution.core import BaseModelSolution

from oracle_paper.solution.mixins.hub_location_mixin import HubLocationMixin
from oracle_paper.solution.mixins.inferred_pricing_mixin import InferredPricingMixin
from oracle_paper.solution.mixins.recursive_decision_mixin import RecursiveDecisionMixin
from oracle_paper.solution.mixins.linear_weight_mixin import LinearWeightMixin
from oracle_paper.solution.mixins.decision_mixin import DecisionMixin

from oracle_paper.solution.mixins.price_mixin import PriceMixin


class PC_HLPSolution(
    PriceMixin,
    DecisionMixin,
    HubLocationMixin,
    LinearWeightMixin,
    InferredPricingMixin,
    RecursiveDecisionMixin,
    BaseModelSolution,
):
    """Solution for the PC-HLP (Fast Lagrange) model.

    Since PC-HLP has no explicit price variable, price is inferred
    from the budget-to-weight ratio of the marginal client on each route.
    Recursive decisions are unrolled to the original client indices.

    Mixin composition:

    - [`PriceMixin`][oracle_paper.solution.mixins.PriceMixin] — price table
    - [`DecisionMixin`][oracle_paper.solution.mixins.DecisionMixin] — active routes
    - [`HubLocationMixin`][oracle_paper.solution.mixins.HubLocationMixin] — hub status
    - [`LinearWeightMixin`][oracle_paper.solution.mixins.LinearWeightMixin] — weights
    - [`InferredPricingMixin`][oracle_paper.solution.mixins.InferredPricingMixin] —
      computes prices from marginal clients
    - [`RecursiveDecisionMixin`][oracle_paper.solution.mixins.RecursiveDecisionMixin] —
      unrolls aggregated decisions to original client keys
    """

    pass


