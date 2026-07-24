"""Tests for oracle_paper.data.calculator.lagrange.LagrangeCalculator."""

import numpy as np
import pytest

from bilevelpy.data.core import MultiEntityDataset

from oracle_paper.core.columns import BilevelDataCol
from oracle_paper.data.calculator.lagrange import LagrangeCalculator

from tests.helpers import (
    create_base_bhlp_dataset,
    create_lagrange_dataset,
    get_nodes_from_dataset,
    simple_lagrange_calculator_dict,
)


# Static method tests (no dataset needed)
@pytest.mark.parametrize(
    "dict_a, dict_b, expected_z",
    [
        ({}, {}, []),
        ({0: 1}, {0: 1}, [1]),
        ({0: 1}, {0: 2}, [2]),
        ({0: 2}, {0: 1}, [1]),
        ({0: 2}, {0: 0}, [0]),
        ({0: 1, 1: 1}, {0: 2, 1: 2}, [2, 2]),
        ({0: 1, 1: 2}, {0: 2, 1: 0}, [2, -2]),
    ],
)
def test_calculate_lagrange_static(dict_a, dict_b, expected_z):
    """Test the static LagrangeCalculator.calculate_lagrange method.

    Verifies that the Lagrange multiplier calculation matches the reference
    implementation across various input combinations.
    """
    result = LagrangeCalculator.calculate_lagrange(dict_a, dict_b)
    expected = simple_lagrange_calculator_dict(dict_a, dict_b)

    for z in dict_a:
        assert np.isclose(result[z], expected[z], rtol=1e-9, atol=1e-9), (
            f"z={z}: got {result[z]}, expected {expected[z]}"
        )

    assert set(result.keys()) == set(dict_a.keys())



# Full pipeline tests
@pytest.mark.parametrize(
    "n_nodes, n_clients_route, random_nodes",
    [
        (2, 5, False),
        (2, 8, True),
        (3, 10, False),
        (4, 12, True),
    ],
)
def test_lagrange_calculator_dataset_basic(n_nodes, n_clients_route, random_nodes):
    """Test Lagrange calculation with basic dataset configurations.

    Verifies that the LagrangeCalculator correctly computes Lagrange
    multipliers across different dataset configurations.
    """
    dataset = create_lagrange_dataset(
        n_nodes=n_nodes,
        n_clients_per_route=n_clients_route,
        random_nodes=random_nodes,
        seed=42,
    )

    nodes = get_nodes_from_dataset(dataset)
    lagrange_store = dataset[BilevelDataCol.LAGRANGE]
    weights_store = dataset[BilevelDataCol.TRANSPORT_WEIGHT_CLIENT]
    budgets_store = dataset[BilevelDataCol.BUDGET]

    for i in nodes:
        for j in nodes:
            if i == j:
                continue

            dict_a = {z: a for (_, __, z), a in weights_store(i, j).items()}
            dict_b = {z: b for (_, __, z), b in budgets_store(i, j).items()}

            expected = simple_lagrange_calculator_dict(dict_a, dict_b)

            for z in dict_a:
                calculated = lagrange_store[i, j, z]
                assert np.isclose(calculated, expected[z], rtol=1e-9, atol=1e-9), (
                    f"Lagrange mismatch for route ({i}, {j}), client {z}: "
                    f"{calculated} vs {expected[z]}"
                )


@pytest.mark.parametrize(
    "random_n_clients, min_budget_fac, max_budget_fac",
    [
        (False, 1, 3),
        (True, 2, 6),
        (False, 3, 8),
    ],
)
def test_lagrange_cumulative_property(random_n_clients, min_budget_fac, max_budget_fac):
    """Test that cumulative Lagrange values satisfy the mathematical formula.

    cumulative_lagrange = (budget / weight) * cumulative_weights
    """
    dataset = create_lagrange_dataset(
        n_nodes=2,
        n_clients_per_route=8,
        random_n_clients=random_n_clients,
        min_budget_factor=min_budget_fac,
        max_budget_factor=max_budget_fac,
        seed=42,
    )

    nodes = get_nodes_from_dataset(dataset)
    lagrange_store = dataset[BilevelDataCol.LAGRANGE]
    weights_store = dataset[BilevelDataCol.TRANSPORT_WEIGHT_CLIENT]
    budgets_store = dataset[BilevelDataCol.BUDGET]

    for i in nodes:
        for j in nodes:
            if i == j:
                continue

            dict_a = {z: a for (_, __, z), a in weights_store(i, j).items()}
            dict_b = {z: b for (_, __, z), b in budgets_store(i, j).items()}

            sorted_z = sorted(dict_a.keys())
            list_a = np.array([dict_a[z] for z in sorted_z])
            list_b = np.array([dict_b[z] for z in sorted_z])
            list_lagrange = np.array([lagrange_store[i, j, z] for z in sorted_z])

            cumulative_lagrange = np.cumsum(list_lagrange)
            cumulative_a = np.cumsum(list_a)

            # Skip zero-division cases
            if np.all(list_a > 0):
                expected_cum = (list_b / list_a) * cumulative_a
                assert np.allclose(cumulative_lagrange, expected_cum, rtol=1e-9, atol=1e-9), (
                    f"Cumulative Lagrange property violated for route ({i}, {j})"
                )



# EntityStore access pattern tests
def test_lagrange_route_access():
    """Test accessing Lagrange multipliers for an entire route via EntityStore(i,j)."""
    dataset = create_lagrange_dataset(n_nodes=2, n_clients_per_route=8, seed=42)
    nodes = get_nodes_from_dataset(dataset)
    lagrange_store = dataset[BilevelDataCol.LAGRANGE]

    for i in nodes:
        for j in nodes:
            if i == j:
                continue
            route_data = lagrange_store(i, j)
            assert isinstance(route_data, dict), f"Expected dict, got {type(route_data)}"
            assert len(route_data) > 0, f"Empty route data for ({i}, {j})"

            for (_, _, z), val in route_data.items():
                assert isinstance(val, (int, float, np.number)), (
                    f"Non-numeric value for ({i}, {j}, {z})"
                )


def test_lagrange_client_access():
    """Test accessing a single Lagrange multiplier via EntityStore[i,j,z]."""
    dataset = create_lagrange_dataset(n_nodes=2, n_clients_per_route=8, seed=42)
    nodes = get_nodes_from_dataset(dataset)
    lagrange_store = dataset[BilevelDataCol.LAGRANGE]

    for i in nodes:
        for j in nodes:
            if i == j:
                continue
            route_data = lagrange_store(i, j)
            for (_, _, z), expected_val in route_data.items():
                actual = lagrange_store[i, j, z]
                assert np.isclose(actual, expected_val), (
                    f"Mismatch at ({i}, {j}, {z}): {actual} vs {expected_val}"
                )



# Error handling
def test_missing_entities_raises():
    """Test that process() raises AttributeError when required entities are missing."""
    calc = LagrangeCalculator()
    empty_dataset = MultiEntityDataset()

    with pytest.raises(AttributeError, match="not found in dataset"):
        calc.process(empty_dataset)


def test_missing_budget_only():
    """Test error when weights exist but budgets don't."""
    dataset = create_base_bhlp_dataset(n_nodes=2, n_clients_per_route=3, seed=42)
    # Remove budget entity
    dataset._stores.pop(BilevelDataCol.BUDGET, None)

    calc = LagrangeCalculator()
    with pytest.raises(AttributeError, match="budget"):
        calc.process(dataset)



# TrackableProcessor metrics
def test_lagrange_calculator_records_metrics():
    """Test that LagrangeCalculator records computation time via track_metric."""
    dataset = create_base_bhlp_dataset(n_nodes=2, n_clients_per_route=5, seed=42)
    calc = LagrangeCalculator()
    calc.process(dataset)

    metrics = calc.get_all_metrics()
    assert "lagrange_time" in metrics, "Should record lagrange_time metric"
    assert metrics["lagrange_time"] > 0, "Computation time should be positive"
