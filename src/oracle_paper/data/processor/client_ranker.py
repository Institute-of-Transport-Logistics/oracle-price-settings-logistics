from typing import Dict, Tuple
from collections import defaultdict

from bilevelpy.data.base_processor import EntityProcessor
from bilevelpy.data.core import MultiEntityDataset
from bilevelpy.core.columns import DataCol

from oracle_paper.core.columns import BilevelDataCol


class LinearClientRanker(EntityProcessor):
    r"""Sort and index clients by budget-to-weight ratio on each route.

    For each route $(i,j)$, clients are sorted in **descending** order of
    $b_{ij}^z / a_{ij}^z$ and assigned zero-based indices $z = 0, 1, 2,
    \dots$. This ranking is essential for the
    [`PrecendenceConstraint`][oracle_paper.constraints.precedence_constraint.PrecendenceConstraint]
    and all Lagrange multiplier calculations.

    Replaces the raw client entities (keyed by original client ID) with
    re-indexed entities keyed by $(i,j,z)$ tuples.
    """

    def process(self, dataset: MultiEntityDataset) -> None:
        """Rank clients and re-index entities by $(i,j,z)$.

        Args:
            dataset: Dataset with client routes, budgets, and weights
                (modified in-place).
        """
        client_routes = dataset[BilevelDataCol.CLIENT_ROUTE]
        budgets = dataset[BilevelDataCol.BUDGET]
        weights = dataset[BilevelDataCol.TRANSPORT_WEIGHT_CLIENT]


        route_buckets = defaultdict(list)
        for (c_id,), (i, j) in client_routes.items():
            route_buckets[(i, j)].append(c_id)

        # mapping from client key -> (i,j,z)
        math_keys: Dict[Tuple, tuple] = {}

        math_weights: Dict[Tuple, float] = {}
        math_budgets: Dict[Tuple, float] = {}
        math_ratios: Dict[Tuple, float] = {}
        math_client_ids: Dict[Tuple, int] = {}

        for (i, j), clients in route_buckets.items():
            client_ratios = []
            for c_id in clients:
                ratio = budgets[c_id] / weights[c_id]
                client_ratios.append((c_id, ratio))

            client_ratios.sort(key=lambda x: x[1], reverse=True)


            for z, (c_id, ratio) in enumerate(client_ratios):
                math_key = (i, j, z)

                math_keys[(c_id,)] = math_key

                math_weights[math_key] = weights[c_id]
                math_budgets[math_key] = budgets[c_id]
                math_ratios[math_key] = ratio
                math_client_ids[math_key] = z


        math_indices = [DataCol.START_NODE,
                                 DataCol.END_NODE,
                                 BilevelDataCol.CLIENT_ID_ROUTE]

        dataset.add_entity(BilevelDataCol.CLIENT_KEY, [BilevelDataCol.CLIENT_KEY], math_keys)

        dataset.add_entity(BilevelDataCol.TRANSPORT_WEIGHT_CLIENT, math_indices, math_weights)
        dataset.add_entity(BilevelDataCol.BUDGET, math_indices, math_budgets)
        dataset.add_entity(BilevelDataCol.CLIENT_RATIO, math_indices, math_ratios)

        dataset.add_entity(BilevelDataCol.CLIENT_ID_ROUTE, math_indices, math_client_ids)