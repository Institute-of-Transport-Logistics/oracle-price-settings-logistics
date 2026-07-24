from typing import Dict, Tuple

from oracle_paper.core.columns import BilevelDataCol
from oracle_paper.variables.decision_variable import ClientDecisionVariable
from oracle_paper.variables.price_variable import PriceVariable


class InferredPricingMixin:
    """Logic for models where price is not a Gurobi variable but is inferred
    post-solve from the active client decisions.

    Iterates over routes and finds the marginal (highest-index) client
    with $y_{ij}^z > 0.5$, then computes price as budget / weight.
    """

    def _register_custom_entities(self):
        """
        Hook called by BaseModelSolution.__init__.
        Ensures inferred prices are calculated and added to the dataset immediately.
        """
        # Call super in case other mixins also want to register things
        super()._register_custom_entities()
        self._compute_and_register_inferred_prices()

    def _compute_and_register_inferred_prices(self):
        """Calculates Price = Budget / Weight and stores it in the Solution Dataset."""

        # 1. Get access to the Decision Store (Y) and Input Data
        y_store = self._solution_data[ClientDecisionVariable]
        input_data = self._model.data

        # Validation for required Mixins
        if not hasattr(self, "_get_solution_weight"):
            raise AttributeError(
                f"'{self.__class__.__name__}' needs a Weight Mixin (e.g. LinearWeightMixin)."
            )

        price_map: Dict[Tuple[int, int], float] = {}

        # 2. Iterate through routes defined in the input budget
        # We use budget keys to define the valid (i, j) routes
        # Assuming budget keys are (i, j, z)
        all_routes = set((idx[0], idx[1]) for idx in input_data[BilevelDataCol.BUDGET])

        for i, j in all_routes:
            if i == j: continue

            # Get all client IDs for this route using EntityStore prefix filter: dataset[key](i, j)
            # This returns a dict {(i, j, z): value, ...}
            route_clients = input_data[BilevelDataCol.CLIENT_ID_ROUTE](i, j)

            # Sort IDs descending to find the "marginal" (highest index) client first
            sorted_zs = sorted([idx[2] for idx in route_clients.keys()], reverse=True)

            price = 0.0
            for z in sorted_zs:
                # Direct O(1) lookup in the solution EntityStore
                if y_store[i, j, z]  > 0.5:
                    budget = input_data[BilevelDataCol.BUDGET][i, j, z]
                    weight = self._get_solution_weight(i, j, z)
                    price = budget / weight
                    break  #

            price_map[(i, j)] = price

        # 3. Add the inferred pricing as a new EntityStore to the SOLUTION dataset
        # Now solution[BilevelVars.PRICE] works exactly like a Gurobi variable!
        self._solution_data.add_entity(
            name=PriceVariable.var_metadata,
            keys=PriceVariable.var_metadata.identifiers,
            data_map=price_map
        )
        self._dict_solution[PriceVariable.var_metadata] = price_map


