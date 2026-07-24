"""Example: PS-BHLP model via Julia + BilevelJuMP (requires Julia ≥ 1.10).

Builds a 3-node dataset and solves the full bilevel formulation through
Julia. Make sure Julia is installed and on PATH before running.
"""

from bilevelpy.core.columns import DataCol
from bilevelpy.core.datasets import Dataset
from bilevelpy.data.builder import DatasetBuilder
from bilevelpy.data.loaders import HLPLoader
from bilevelpy.data.processor import HLPNodeSelector, HLPCostScaling
from bilevelpy.solver import ModelSolver

from oracle_paper.core.columns import BilevelDataCol
from oracle_paper.data.generator.bilevel_client_generator import BilevelClientGenerator
from oracle_paper.data.processor.client_ranker import LinearClientRanker
from oracle_paper.models.ps_bhlp import PS_BHLP

if __name__ == "__main__":
    dataset = (
        DatasetBuilder()
        .pipe(HLPLoader(Dataset.CAB100))
        .pipe(HLPNodeSelector(n_nodes=3, random_nodes=False))
        .pipe(HLPCostScaling(scaling_factor=100))
        .pipe(BilevelClientGenerator(clients_per_route=2))
        .pipe(LinearClientRanker())
        .build()
    )

    print("Dataset built.")
    print(f"  Nodes: {list(dataset[DataCol.NODE_ID].values)}")
    print(f"  Cost pairs: {len(dataset[DataCol.COST_NODE_TO_NODE])}")
    print(f"  Client triples: {len(dataset[BilevelDataCol.CLIENT_ID_ROUTE])}")
    print()

    print("Building PS_BHLP via Julia …")
    model = PS_BHLP(n_hubs=2, alpha=0.5, data=dataset)

    print(f"  Gurobi model has {model.model.NumVars} vars, {model.model.NumConstrs} constrs")
    print()

    print("Solving …")
    solution = ModelSolver(model, time_limit=60).solve()

    print(solution)
    print()
    print("Metadata dict:", solution.solution_metadata.to_dict())