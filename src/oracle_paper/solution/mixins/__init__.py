"""Solution mixins that add tables and derived quantities to solution reports."""

from oracle_paper.solution.mixins.decision_mixin import DecisionMixin
from oracle_paper.solution.mixins.hub_location_mixin import HubLocationMixin
from oracle_paper.solution.mixins.inferred_pricing_mixin import InferredPricingMixin
from oracle_paper.solution.mixins.linear_weight_mixin import LinearWeightMixin
from oracle_paper.solution.mixins.price_mixin import PriceMixin
from oracle_paper.solution.mixins.recursive_decision_mixin import RecursiveDecisionMixin

__all__ = [
    "DecisionMixin",
    "HubLocationMixin",
    "InferredPricingMixin",
    "LinearWeightMixin",
    "PriceMixin",
    "RecursiveDecisionMixin",
]