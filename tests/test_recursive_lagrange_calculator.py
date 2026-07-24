"""Tests for oracle_paper.data.calculator.recursive_lagrange.RecursiveLagrangeCalculator."""

import numpy as np
import pytest

from oracle_paper.core.columns import BilevelDataCol
from oracle_paper.data.calculator.lagrange import LagrangeCalculator
from oracle_paper.data.calculator.recursive_lagrange import RecursiveLagrangeCalculator

from tests.helpers import (
    create_base_bhlp_dataset,
    create_lagrange_dataset,
    create_recursive_lagrange_dataset,
    get_nodes_from_dataset,
)



# Static method tests
def test_sort_lagrange_multipliers_empty():
    """Test sort_lagrange_multipliers_dict with empty input."""
    result = (RecursiveLagrangeCalculator
              .sort_lagrange_multipliers_dict({},
                                              {},
                                              {}))
    assert result == ({}, {})


def test_sort_lagrange_multipliers_single_element():
    """Test with single-element dicts."""
    lagrange = {0: 5.0}
    keys = {0: 0}
    volumes = {0: 2.0}

    new_lagrange, new_keys = RecursiveLagrangeCalculator.sort_lagrange_multipliers_dict(
        lagrange, keys, volumes
    )
    assert new_lagrange == {0: 5.0}
    assert new_keys == {0: [0]}


def test_sort_lagrange_multipliers_already_sorted():
    """Test with ratios already in descending order, no merging expected."""
    # Ratios: 10/2=5, 5/2=2.5, 2/2=1 —>  descending, no merge
    lagrange = {0: 10.0, 1: 5.0, 2: 2.0}
    keys = {0: 0, 1: 1, 2: 2}
    volumes = {0: 2.0, 1: 2.0, 2: 2.0}

    new_lagrange, new_keys = RecursiveLagrangeCalculator.sort_lagrange_multipliers_dict(
        lagrange, keys, volumes
    )
    assert len(new_lagrange) == 3, f"Expected 3 elements, got {len(new_lagrange)}"
    assert new_lagrange[0] == 10.0
    assert new_lagrange[1] == 5.0
    assert new_lagrange[2] == 2.0


def test_sort_lagrange_multipliers_requires_merging():
    """Test where ratios violate order.
     In this case the clients should be merged."""

    # Ratios: 4/2=2, 6/2=3 -> ascending property violated -> should merge into one
    lagrange = {0: 4.0, 1: 6.0}
    keys = {0: 0, 1: 1}
    volumes = {0: 2.0, 1: 2.0}

    new_lagrange, new_keys = RecursiveLagrangeCalculator.sort_lagrange_multipliers_dict(
        lagrange, keys, volumes
    )
    assert len(new_lagrange) == 1, f"Expected 1 merged group, got {len(new_lagrange)}"
    assert new_lagrange[0] == 10.0, f"Expected merged lagrange 10.0, got {new_lagrange[0]}"
    assert new_keys[0] == [0, 1], f"Expected merged keys [0, 1], got {new_keys[0]}"


def test_sort_lagrange_multipliers_complex():
    """Test complex scenario with multiple merges."""
    # Ratios: 10/2=5, 8/2=4, 6/2=3, 4/2=2 —> already descending, no merge
    lagrange = {0: 10.0, 1: 8.0, 2: 6.0, 3: 4.0}
    keys = {0: 0, 1: 1, 2: 2, 3: 3}
    volumes = {0: 2.0, 1: 2.0, 2: 2.0, 3: 2.0}

    new_lagrange, new_keys = RecursiveLagrangeCalculator.sort_lagrange_multipliers_dict(
        lagrange, keys, volumes
    )
    assert len(new_lagrange) == 4, "No merges should occur"
    assert sum(new_lagrange.values()) == 28.0, "Sum should be preserved"



# Full pipeline tests
@pytest.mark.parametrize(
    "n_nodes, n_clients_route, random_nodes",
    [
        (2, 5, False),
        (2, 8, True),
        (3, 10, False),
    ],
)
def test_recursive_lagrange_sum_preservation(n_nodes, n_clients_route, random_nodes):
    """Test that total Lagrange sum is preserved after recursive merging."""
    dataset = create_lagrange_dataset(
        n_nodes=n_nodes,
        n_clients_per_route=n_clients_route,
        random_nodes=random_nodes,
        seed=42,
    )

    # Compute original sums before recursive processing alters the dataset
    original_sums = {}
    nodes = get_nodes_from_dataset(dataset)
    lagrange_store = dataset[BilevelDataCol.LAGRANGE]
    for i in nodes:
        for j in nodes:
            if i != j:
                original_sums[(i, j)] = sum(lagrange_store[i, j, z]
                                            for (_, _, z), _ in lagrange_store(i, j).items())

    # Now apply recursive
    RecursiveLagrangeCalculator().process(dataset)

    recursive_store = dataset[BilevelDataCol.RECURSIVE_LAGRANGE]
    for (i, j), expected_sum in original_sums.items():
        route_data = recursive_store(i, j)
        recursive_sum = sum(val for (_, _, z), val in route_data.items()
                           if not isinstance(val, list))
        assert np.allclose(recursive_sum, expected_sum, rtol=1e-9, atol=1e-9), (
            f"Sum mismatch for route ({i}, {j}): "
            f"{recursive_sum} vs {expected_sum}"
        )


def test_recursive_lagrange_ordering_property():
    """Test that recursive Lagrange/weight ratio is non-increasing."""
    dataset = create_recursive_lagrange_dataset(
        n_nodes=2, n_clients_per_route=8, seed=42,
    )
    nodes = get_nodes_from_dataset(dataset)
    recursive_store = dataset[BilevelDataCol.RECURSIVE_LAGRANGE]
    weights_store = dataset[BilevelDataCol.SUMMED_LINEAR_WEIGHTS]

    for i in nodes:
        for j in nodes:
            if i == j:
                continue

            route_rec = {
                z: val for (_, _, z), val in recursive_store(i, j).items()
            }
            route_a = {
                z: val for (_, _, z), val in weights_store(i, j).items()
            }

            if len(route_rec) <= 1:
                continue

            sorted_z = sorted(route_rec.keys())
            ratios = [route_rec[z] / route_a[z] for z in sorted_z
                      if route_a[z] != 0]

            for r in range(len(ratios) - 1):
                assert ratios[r] >= ratios[r + 1], (
                    f"Ordering violated at route ({i}, {j}): "
                    f"ratio[{r}]={ratios[r]} < ratio[{r+1}]={ratios[r+1]}"
                )


def test_recursive_reduces_or_maintains_clients():
    """Test that recursive calculation never increases client count."""
    dataset = create_lagrange_dataset(
        n_nodes=2, n_clients_per_route=10,
        min_budget_factor=1, max_budget_factor=5, seed=42,
    )

    original_lagrange_count = sum(
        len(dataset[BilevelDataCol.LAGRANGE](i, j))
        for i in get_nodes_from_dataset(dataset)
        for j in get_nodes_from_dataset(dataset)
        if i != j
    )

    RecursiveLagrangeCalculator().process(dataset)

    recursive_count = sum(
        len(dataset[BilevelDataCol.RECURSIVE_LAGRANGE](i, j))
        for i in get_nodes_from_dataset(dataset)
        for j in get_nodes_from_dataset(dataset)
        if i != j
    )

    assert recursive_count <= original_lagrange_count, (
        f"Recursive should not increase clients: "
        f"{recursive_count} vs {original_lagrange_count}"
    )



# Entity access tests
def test_recursive_lagrange_route_access():
    """Test accessing recursive Lagrange for a route via EntityStore."""
    dataset = create_recursive_lagrange_dataset(
        n_nodes=2, n_clients_per_route=6, seed=42,
    )
    nodes = get_nodes_from_dataset(dataset)
    store = dataset[BilevelDataCol.RECURSIVE_LAGRANGE]

    for i in nodes:
        for j in nodes:
            if i == j:
                continue
            route_data = store(i, j)
            assert isinstance(route_data, dict)
            assert len(route_data) > 0

            for (_, _, z), val in route_data.items():
                single = store[i, j, z]
                assert np.isclose(single, val), (
                    f"Route vs single mismatch at ({i},{j},{z})"
                )


def test_recursive_lagrange_adds_expected_entities():
    """Test that RecursiveLagrangeCalculator adds the four expected entities."""
    dataset = create_lagrange_dataset(n_nodes=2, n_clients_per_route=5, seed=42)
    RecursiveLagrangeCalculator().process(dataset)

    assert BilevelDataCol.RECURSIVE_LAGRANGE in dataset
    assert BilevelDataCol.CLIENT_KEYS in dataset
    assert BilevelDataCol.SUMMED_LINEAR_WEIGHTS in dataset
    assert BilevelDataCol.SUMMED_BUDGETS in dataset



# Volume consistency
def test_volume_consistency():
    """Test that total shipping volumes are preserved through recursion."""
    dataset = create_base_bhlp_dataset(n_nodes=2, n_clients_per_route=8, seed=42)

    # Record original volumes per route
    weights_store = dataset[BilevelDataCol.TRANSPORT_WEIGHT_CLIENT]
    nodes = get_nodes_from_dataset(dataset)
    original_totals = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                route_data = weights_store(i, j)
                original_totals[(i, j)] = sum(val for _, val in route_data.items())

    # Run full pipeline
    LagrangeCalculator().process(dataset)
    RecursiveLagrangeCalculator().process(dataset)

    summed_store = dataset[BilevelDataCol.SUMMED_LINEAR_WEIGHTS]
    for (i, j), orig_total in original_totals.items():
        route_data = summed_store(i, j)
        recursive_total = sum(val for _, val in route_data.items())
        assert np.isclose(recursive_total, orig_total), (
            f"Volume mismatch for route ({i}, {j}): "
            f"{recursive_total} vs {orig_total}"
        )



# Metrics Test
def test_recursive_lagrange_records_metrics():
    """Test that RecursiveLagrangeCalculator records computation time."""
    dataset = create_lagrange_dataset(n_nodes=2, n_clients_per_route=5, seed=42)
    calc = RecursiveLagrangeCalculator()
    calc.process(dataset)

    metrics = calc.get_all_metrics()
    assert "recursive_lagrange_time" in metrics
    assert metrics["recursive_lagrange_time"] > 0