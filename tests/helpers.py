"""Shared test helpers for oracle_paper data tests.

Provides factory functions to build MultiEntityDataset instances
using the new bilevelpy + oracle_paper data pipeline.
"""

from bilevelpy.core.columns import DataCol
from bilevelpy.core.datasets import Dataset
from bilevelpy.data.builder import DatasetBuilder
from bilevelpy.data.core import MultiEntityDataset
from bilevelpy.data.loaders import HLPLoader
from bilevelpy.data.processor import HLPNodeSelector, HLPCostScaling


from oracle_paper.data.calculator.lagrange import LagrangeCalculator
from oracle_paper.data.calculator.recursive_lagrange import RecursiveLagrangeCalculator
from oracle_paper.data.generator.bilevel_client_generator import BilevelClientGenerator
from oracle_paper.data.processor.client_ranker import LinearClientRanker


def create_base_bhlp_dataset(
    n_nodes: int,
    n_clients_per_route: int,
    random_nodes: bool = False,
    random_n_clients: bool = False,
    min_budget_factor: float = 1.0,
    max_budget_factor: float = 5.0,
    seed: int = 42,
) -> MultiEntityDataset:
    """Build a dataset with HLP loader + bilevel client generator + ranker.

    This is the shared pipeline that both Lagrange and RecursiveLagrange
    calculators expect as input.
    """
    return (
        DatasetBuilder()
        .pipe(HLPLoader(Dataset.CAB100))
        .pipe(HLPNodeSelector(n_nodes=n_nodes,
                                                 random_nodes=random_nodes,
                                                 seed=seed))
        .pipe(HLPCostScaling(scaling_factor=100))
        .pipe(
            BilevelClientGenerator(
                clients_per_route=n_clients_per_route,
                random_count=random_n_clients,
                min_budget_factor=min_budget_factor,
                max_budget_factor=max_budget_factor,
                seed=seed,
            )
        )
        .pipe(LinearClientRanker())
        .build()
    )


def create_lagrange_dataset(
    n_nodes: int,
    n_clients_per_route: int,
    random_nodes: bool = False,
    random_n_clients: bool = False,
    min_budget_factor: float = 1.0,
    max_budget_factor: float = 5.0,
    seed: int = 42,
) -> MultiEntityDataset:
    """Build a dataset with Lagrange multipliers computed."""
    base = create_base_bhlp_dataset(
        n_nodes, n_clients_per_route,
        random_nodes, random_n_clients,
        min_budget_factor, max_budget_factor, seed,
    )
    calc = LagrangeCalculator()
    calc.process(base)
    return base


def create_recursive_lagrange_dataset(
    n_nodes: int,
    n_clients_per_route: int,
    random_nodes: bool = False,
    random_n_clients: bool = False,
    min_budget_factor: float = 1.0,
    max_budget_factor: float = 5.0,
    seed: int = 42,
) -> MultiEntityDataset:
    """Build a dataset with both Lagrange and recursive Lagrange computed."""
    base = create_base_bhlp_dataset(
        n_nodes, n_clients_per_route,
        random_nodes, random_n_clients,
        min_budget_factor, max_budget_factor, seed,
    )
    LagrangeCalculator().process(base)
    RecursiveLagrangeCalculator().process(base)
    return base


# Reference implementations (for correctness validation)
def simple_lagrange_calculator(list_a: list, list_b: list) -> list:
    """Reference Lagrange calculator using flat lists"""
    lagrange = [0.0] * len(list_a)
    for k in range(len(list_a)):
        sum1 = 0.0
        for z in range(k + 1):
            sum1 += list_a[z]
        sum1 *= list_b[k] / list_a[k] if list_a[k] != 0 else 0.0

        sum2 = 0.0
        if k - 1 >= 0:
            for z in range(k):
                sum2 += list_a[z]
            sum2 *= list_b[k - 1] / list_a[k - 1] if list_a[k - 1] != 0 else 0.0

        lagrange[k] = sum1 - sum2

    return lagrange


def simple_lagrange_calculator_dict(dict_a: dict, dict_b: dict) -> dict:
    """Reference Lagrange calculator with dict inputs {z: value}"""
    sorted_z = sorted(dict_a.keys())
    list_a = [dict_a[z] for z in sorted_z]
    list_b = [dict_b[z] for z in sorted_z]
    lagrange_list = simple_lagrange_calculator(list_a, list_b)
    return {z: lagrange_list[i] for i, z in enumerate(sorted_z)}


def get_nodes_from_dataset(dataset: MultiEntityDataset) -> list:
    """Extract node list from a dataset."""
    return list(dataset[DataCol.NODE_ID].values)