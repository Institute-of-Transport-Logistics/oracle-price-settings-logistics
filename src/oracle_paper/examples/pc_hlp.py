"""Example: PC-HLP (Fast Lagrange) model with recursive client aggregation.

Builds a 10-node dataset, computes Lagrange multipliers and recursive
aggregation, then solves with 2 hubs.
"""

from bilevelpy.core.datasets import Dataset
from bilevelpy.data.builder import DatasetBuilder
from bilevelpy.data.loaders import HLPLoader
from bilevelpy.data.processor import HLPNodeSelector, HLPCostScaling
from bilevelpy.solver import ModelSolver

from oracle_paper.data.calculator.lagrange import LagrangeCalculator
from oracle_paper.data.calculator.recursive_lagrange import RecursiveLagrangeCalculator
from oracle_paper.data.generator.bilevel_client_generator import BilevelClientGenerator
from oracle_paper.data.processor.client_ranker import LinearClientRanker
from oracle_paper.models.pc_hlp import PC_HLP


if __name__ == "__main__":
    dataset = (DatasetBuilder()
               .pipe(HLPLoader(Dataset.CAB100))
               .pipe(HLPNodeSelector(n_nodes=10, random_nodes=False))
               .pipe(HLPCostScaling(scaling_factor=100))
               .pipe(BilevelClientGenerator(clients_per_route=3))
               .pipe(LinearClientRanker())
               .pipe(LagrangeCalculator())
               .pipe(RecursiveLagrangeCalculator())
               .build())


    model = PC_HLP(n_hubs=2, alpha=0.5, data=dataset)

    solution = ModelSolver(model).solve()

    print(solution)