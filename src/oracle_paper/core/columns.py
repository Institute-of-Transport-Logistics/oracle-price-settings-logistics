"""Column identifiers for bilevel hub location datasets.

Extends [`DataCol`][bilevelpy.core.columns.DataCol] with additional
columns specific to bilevel problems: client routing keys, budgets,
Lagrange multipliers, and aggregated weights for recursive clients.
"""

from enum import StrEnum


class BilevelDataCol(StrEnum):
    """Extra column names used in bilevel hub location datasets.

    These columns sit alongside the standard
    [`DataCol`][bilevelpy.core.columns.DataCol] columns and carry the
    additional data that the bilevel models need: per-client budgets,
    transport weights, Lagrange multipliers, and aggregated keys for
    the recursive (PC-HLP) formulation.

    Attributes:
        CLIENT_KEY: Unique integer key assigned to each client.
        CLIENT_ID_ROUTE: Zero-based index $z$ of a client on route $(i,j)$.
        CLIENT_ROUTE: The $(i,j)$ route tuple the client belongs to.
        CLIENT_RATIO: Budget-to-weight ratio $b_{ij}^z / a_{ij}^z$.
        BUDGET: Client budget $b_{ij}^z$ (willingness to pay).
        TRANSPORT_WEIGHT_CLIENT: Client demand weight $a_{ij}^z$.
        LAGRANGE: Lagrange multiplier $\\lambda_{ij}^z$ for the PPC-HLP model.
        RECURSIVE_LAGRANGE: Lagrange multiplier after recursive merging (PC-HLP).
        CLIENT_KEYS: Mapping $(i,j,z) \\to$ list of original client keys that
            were merged into this aggregated client.
        SUMMED_LINEAR_WEIGHTS: Sum of $a_{ij}^z$ over all clients merged
            into an aggregated recursive client.
        SUMMED_BUDGETS: Sum of $b_{ij}^z$ over all clients merged
            into an aggregated recursive client.
    """

    CLIENT_KEY = "clientKey"
    CLIENT_ID_ROUTE = "clientID"
    CLIENT_ROUTE = "clientRoute"
    CLIENT_RATIO = "clientRatio"
    BUDGET = "budget"
    TRANSPORT_WEIGHT_CLIENT = "a"
    LAGRANGE = "lagrange"
    RECURSIVE_LAGRANGE = "recursive_lagrange"
    CLIENT_KEYS = "clientKeys"
    SUMMED_LINEAR_WEIGHTS = "summed_a"
    SUMMED_BUDGETS = "summed_b"