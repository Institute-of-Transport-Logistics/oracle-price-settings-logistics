import random
from typing import Dict, Tuple, List

from bilevelpy.data.base_processor import EntityProcessor
from bilevelpy.data.core import MultiEntityDataset
from bilevelpy.core.columns import DataCol

from oracle_paper.core.columns import BilevelDataCol

class BilevelClientGenerator(EntityProcessor):
    r"""Generate synthetic bilevel clients on each route.

    For every route $(i,j)$ with $i \neq j$, generates a random number of
    clients, each with a weight $a_{ij}^z$ (sampled from ``possible_weights``)
    and a budget $b_{ij}^z = c_{ij} \cdot a_{ij}^z \cdot \text{factor}$,
    where the factor is uniformly sampled from
    $[\text{min\_budget\_factor}, \text{max\_budget\_factor}]$.

    Args:
        clients_per_route: Number of clients per route (or max if
            ``random_count`` is ``True``).
        random_count: If ``True``, each route gets a random number of
            clients between 1 and ``clients_per_route``.
        min_budget_factor: Minimum multiplier for budget generation.
        max_budget_factor: Maximum multiplier for budget generation.
        possible_weights: List of possible client weights to sample from.
        seed: Random seed for reproducibility.
    """

    def __init__(
        self,
        clients_per_route: int,
        random_count: bool = False,
        min_budget_factor: float = 1.2,
        max_budget_factor: float = 1.8,
        possible_weights: List[float] = None,
        seed: int = 42,
    ):
        self.clients_per_route = clients_per_route
        self.random_count = random_count
        self.min_budget_factor = min_budget_factor
        self.max_budget_factor = max_budget_factor
        self.possible_weights = possible_weights or list(range(1,21))
        self.rng = random.Random(seed)

    def process(self, dataset: MultiEntityDataset) -> None:
        self._check_dataset(dataset)

        costs = dataset[DataCol.COST_NODE_TO_NODE]

        # Maps from ClientIndex to route (i,j)
        client_routes: Dict[Tuple, Tuple] = {}

        # Maps from ClientIndex to weight
        client_weights: Dict[Tuple, float] = {}

        # Maps from ClientIndex to budget
        client_budgets: Dict[Tuple, float] = {}

        client_counter = 0

        # Iterate over all possible routes (i, j)
        for (i, j), direct_cost in costs.items():
            if i == j: continue

            # Determine how many clients for this specific route
            num_clients = (self.rng.randint(1, self.clients_per_route)
                           if self.random_count else self.clients_per_route)

            for _ in range(num_clients):
                c_id = (client_counter,)

                # Assign Route
                client_routes[c_id] = (i, j)

                # Assign Random Weight
                weight = self.rng.choice(self.possible_weights)

                client_weights[c_id] = weight

                # Generate Budget: (Direct Cost * Weight) * Random Factor
                factor = self.rng.uniform(self.min_budget_factor, self.max_budget_factor)
                client_budgets[c_id] = round(direct_cost * weight * factor, 2)

                client_counter += 1


        dataset.add_entity(name= BilevelDataCol.CLIENT_ROUTE,
                           keys = [BilevelDataCol.CLIENT_KEY],
                           data_map= client_routes)

        dataset.add_entity(name = BilevelDataCol.TRANSPORT_WEIGHT_CLIENT,
                           keys = [BilevelDataCol.CLIENT_KEY],
                           data_map = client_weights)

        dataset.add_entity(name=BilevelDataCol.BUDGET,
                           keys = [BilevelDataCol.CLIENT_KEY],
                           data_map = client_budgets)

        # Also add a simple list of client IDs for iteration
        dataset.add_entity(name = BilevelDataCol.CLIENT_KEY,
                           keys = [BilevelDataCol.CLIENT_KEY],
                           data_map={(index,): index for index in range(client_counter)})

    def _check_dataset(self, dataset):
        if DataCol.NODE_ID not in dataset:
            raise AttributeError(f"{DataCol.NODE_ID.value} not found in dataset.")

        if DataCol.COST_NODE_TO_NODE not in dataset:
            raise AttributeError(f"{DataCol.COST_NODE_TO_NODE.value} not found in dataset.")

