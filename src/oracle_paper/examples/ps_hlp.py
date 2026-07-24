"""Example: PS-HLP (Big M) model on a small CAB instance.

Builds a 5-node dataset with 5 clients per route, runs the Big-M
price-setting model with 2 hubs, and prints the solution.
"""

from bilevelpy.core.datasets import Dataset
from bilevelpy.data.builder import DatasetBuilder
from bilevelpy.data.loaders import HLPLoader
from bilevelpy.data.processor import HLPNodeSelector, HLPCostScaling
from bilevelpy.solver import ModelSolver

from oracle_paper.data.generator.bilevel_client_generator import BilevelClientGenerator
from oracle_paper.data.processor.client_ranker import LinearClientRanker
from oracle_paper.models.ps_hlp import PS_HLP


if __name__ == "__main__":

    dataset = (DatasetBuilder()
               .pipe(HLPLoader(Dataset.CAB100))
               .pipe(HLPNodeSelector(n_nodes=5, random_nodes=False))
               .pipe(HLPCostScaling(scaling_factor=1000))
               .pipe(BilevelClientGenerator(clients_per_route=5))
               .pipe(LinearClientRanker())
               .build())

    model = PS_HLP(
        n_hubs=2,
        alpha=0.5,
        data=dataset
    )

    solution = ModelSolver(model).solve()

    print(solution)
    merged_solution_data = solution.solution_data + model.data

    print(merged_solution_data)




