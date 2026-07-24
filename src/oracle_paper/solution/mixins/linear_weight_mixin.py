r"""Mixin providing access to client transport weights $a_{ij}^z$."""

from oracle_paper.core.columns import BilevelDataCol


class LinearWeightMixin:
    """Provides the transport weight $a_{ij}^z$ for a given client route.

    Used by
    [`InferredPricingMixin`][oracle_paper.solution.mixins.InferredPricingMixin]
    to compute the implied price from active client decisions.
    """

    def _get_solution_weight(self, i: int, j: int, z: int) -> float:
        """Return the transport weight $a_{ij}^z$ for client $(i,j,z)$."""
        a = self._model.data[BilevelDataCol.TRANSPORT_WEIGHT_CLIENT]
        return a[i, j, z]