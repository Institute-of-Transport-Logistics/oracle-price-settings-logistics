"""Tests for oracle_paper.data.generator.bilevel_client_generator.BilevelClientGenerator."""

import random

import pytest

from bilevelpy.core.columns import DataCol
from bilevelpy.core.datasets import Dataset
from bilevelpy.data.builder import DatasetBuilder
from bilevelpy.data.loaders import HLPLoader
from bilevelpy.data.processor import HLPNodeSelector, HLPCostScaling

from oracle_paper.core.columns import BilevelDataCol
from oracle_paper.data.generator.bilevel_client_generator import BilevelClientGenerator


def build_hlp_dataset(n_nodes: int, seed: int = 42):
    """Minimal HLP dataset with nodes and costs, no clients yet."""
    return (
        DatasetBuilder()
        .pipe(HLPLoader(Dataset.CAB100))
        .pipe(HLPNodeSelector(n_nodes=n_nodes, random_nodes=False, seed=seed))
        .pipe(HLPCostScaling(scaling_factor=100))
        .build()
    )


@pytest.mark.parametrize(
    "n_nodes, n_clients_route, random_nodes, random_n_clients, min_budget_fac, max_budget_fac",
    [
        (2, 3, True, True, 1.0, 3.0),
        (2, 5, False, False, 2.0, 2.0),
        (4, 6, True, False, 1.0, 5.0),
        (4, 10, False, True, 3.0, 7.0),
    ],
)
def test_properties_of_generated_dataset(
    n_nodes, n_clients_route, random_nodes, random_n_clients,
    min_budget_fac, max_budget_fac,
):
    """Test that the bilevel client generator produces data matching constraints.

    Verifies:
    - Client count bounds (random vs fixed)
    - Budget generation within factor range
    - Budget == factor * cost * weight when min == max factor
    """
    seed = random.randint(1, 1000)

    dataset = (
        DatasetBuilder()
        .pipe(HLPLoader(Dataset.CAB100))
        .pipe(HLPNodeSelector(n_nodes=n_nodes, random_nodes=random_nodes, seed=seed))
        .pipe(HLPCostScaling(scaling_factor=100))
        .pipe(
            BilevelClientGenerator(
                clients_per_route=n_clients_route,
                random_count=random_n_clients,
                min_budget_factor=min_budget_fac,
                max_budget_factor=max_budget_fac,
                seed=seed,
            )
        )
        .build()
    )

    costs = dataset[DataCol.COST_NODE_TO_NODE]
    weights = dataset[BilevelDataCol.TRANSPORT_WEIGHT_CLIENT]
    budgets = dataset[BilevelDataCol.BUDGET]
    routes = dataset[BilevelDataCol.CLIENT_ROUTE]

    # --- Test 1: Client count ---
    n_routes = n_nodes * (n_nodes - 1)  # i != j for all node pairs
    if random_n_clients:
        assert n_routes <= len(routes) <= n_routes * n_clients_route, (
            f"Client count {len(routes)} outside range [{n_routes}, {n_routes * n_clients_route}]"
        )
    else:
        assert len(routes) == n_routes * n_clients_route, (
            f"Expected {n_routes * n_clients_route} clients, got {len(routes)}"
        )

    # --- Test 2: Budget constraints ---
    for (c_id,), (i, j) in routes.items():
        c = costs[i, j]
        w = weights[c_id]
        budget = budgets[c_id]

        # Budget should be between min * c * w and max * c * w
        min_expected = round(min_budget_fac * c * w, 6)
        max_expected = round(max_budget_fac * c * w, 6)

        assert min_expected <= round(budget, 6) <= max_expected, (
            f"Budget {budget} for route ({i},{j}), client {c_id} "
            f"outside [{min_expected}, {max_expected}]"
        )


@pytest.mark.parametrize(
    "n_nodes, n_clients_route, random_n_clients",
    [
        (2, 3, False),
        (2, 5, True),
        (3, 4, False),
    ],
)
def test_client_entities_are_consistent(n_nodes, n_clients_route, random_n_clients):
    """Test that all client entities have matching key sets."""
    dataset = (
        DatasetBuilder()
        .pipe(HLPLoader(Dataset.CAB100))
        .pipe(HLPNodeSelector(n_nodes=n_nodes, random_nodes=False, seed=42))
        .pipe(HLPCostScaling(scaling_factor=100))
        .pipe(
            BilevelClientGenerator(
                clients_per_route=n_clients_route,
                random_count=random_n_clients,
                seed=42,
            )
        )
        .build()
    )

    route_keys = set(dataset[BilevelDataCol.CLIENT_ROUTE].data.keys())
    weight_keys = set(dataset[BilevelDataCol.TRANSPORT_WEIGHT_CLIENT].data.keys())
    budget_keys = set(dataset[BilevelDataCol.BUDGET].data.keys())
    client_keys = set(dataset[BilevelDataCol.CLIENT_KEY].data.keys())

    assert route_keys == weight_keys == budget_keys == client_keys, (
        "All client entities should have identical key sets"
    )


def test_generator_adds_expected_entities():
    """Test that BilevelClientGenerator adds the expected entities."""
    dataset = build_hlp_dataset(n_nodes=3, seed=42)

    gen = BilevelClientGenerator(clients_per_route=3, seed=42)
    gen.process(dataset)

    assert BilevelDataCol.CLIENT_ROUTE in dataset
    assert BilevelDataCol.TRANSPORT_WEIGHT_CLIENT in dataset
    assert BilevelDataCol.BUDGET in dataset
    assert BilevelDataCol.CLIENT_KEY in dataset


def test_generator_errors_on_missing_nodes():
    """Test that generator raises when NODE_ID entity is missing."""
    from bilevelpy.data.core import MultiEntityDataset

    empty = MultiEntityDataset()
    gen = BilevelClientGenerator(clients_per_route=3)
    with pytest.raises(AttributeError, match="node_id"):
        gen.process(empty)


def test_all_clients_have_valid_routes():
    """Test that every client is assigned to a valid (i != j) route."""
    dataset = (
        DatasetBuilder()
        .pipe(HLPLoader(Dataset.CAB100))
        .pipe(HLPNodeSelector(n_nodes=5, random_nodes=False, seed=42))
        .pipe(HLPCostScaling(scaling_factor=100))
        .pipe(BilevelClientGenerator(clients_per_route=3, seed=42))
        .build()
    )

    routes = dataset[BilevelDataCol.CLIENT_ROUTE]
    for (c_id,), (i, j) in routes.items():
        assert i != j, f"Client {c_id} assigned to self-route ({i},{i})"
        assert isinstance(i, (int, float)), f"i is not numeric: {type(i)}"
        assert isinstance(j, (int, float)), f"j is not numeric: {type(j)}"