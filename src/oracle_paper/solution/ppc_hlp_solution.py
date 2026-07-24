from bilevelpy.solution.core import BaseModelSolution
from oracle_paper.solution.mixins.hub_location_mixin import HubLocationMixin
from oracle_paper.solution.mixins.inferred_pricing_mixin import InferredPricingMixin
from oracle_paper.solution.mixins.linear_weight_mixin import LinearWeightMixin
from oracle_paper.solution.mixins.decision_mixin import DecisionMixin

from oracle_paper.solution.mixins.price_mixin import PriceMixin


class PPC_HLPSolution(
    PriceMixin,
    DecisionMixin,
    HubLocationMixin,
    LinearWeightMixin,
    InferredPricingMixin,
    BaseModelSolution,
):
    """Solution for the PPC-HLP (Lagrange) model.

    Like PC-HLP, price is inferred post-solve from the marginal client
    on each route. No recursive unrolling is needed here — PPC-HLP uses
    flat (non-aggregated) client indices.

    Mixin composition:

    - [`PriceMixin`][oracle_paper.solution.mixins.PriceMixin] — price table
    - [`DecisionMixin`][oracle_paper.solution.mixins.DecisionMixin] — active routes
    - [`HubLocationMixin`][oracle_paper.solution.mixins.HubLocationMixin] — hub status
    - [`LinearWeightMixin`][oracle_paper.solution.mixins.LinearWeightMixin] — weights
    - [`InferredPricingMixin`][oracle_paper.solution.mixins.InferredPricingMixin] —
      computes prices from marginal clients
    """

    pass