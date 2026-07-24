from typing import Dict, Any

from bilevelpy.benchmarks.protocols import ModelProvider
from bilevelpy.models.meta import ModelMetaData
from bilevelpy.solution import BaseModelSolution
from bilevelpy.solver import ModelSolver
from bilevelpy.core.datasets import Dataset
from bilevelpy.data.builder import DatasetBuilder
from bilevelpy.data.loaders import HLPLoader
from bilevelpy.data.processor import HLPNodeSelector, HLPCostScaling

from oracle_paper.benchmark import BenchmarkConfig
from oracle_paper.core.columns import BilevelDataCol
from oracle_paper.data.generator.bilevel_client_generator import BilevelClientGenerator
from oracle_paper.data.processor.client_ranker import LinearClientRanker
from oracle_paper.data.calculator.lagrange import LagrangeCalculator
from oracle_paper.data.calculator.recursive_lagrange import RecursiveLagrangeCalculator
from oracle_paper.models.ps_hlp import PS_HLP
from oracle_paper.models.pc_hlp import PC_HLP
from oracle_paper.models.ppc_hlp import PPC_HLP
from oracle_paper.models.ps_bhlp import PS_BHLP
from oracle_paper.core.names import OraclePaperModelNames


class PaperModelProvider(ModelProvider):
    """Builds datasets and instantiates models for benchmark runs.

    Handles the full pipeline for each of the four models studied in the
    paper. For a given scenario (nodes, clients, hubs), it:

    1. Builds the dataset via the standard pipeline (CAB loader → node
       selection → cost scaling → client generation → client ranking).
    2. Runs the appropriate calculators (Lagrange and/or recursive
       Lagrange) depending on the model.
    3. Instantiates the model with the configured parameters.
    4. Solves and returns the solution with metadata attached.
    """

    def __init__(self, config: BenchmarkConfig):
        self._config = config

    def build_and_solve(self,
                        model_name: ModelMetaData,
                        scenario: Dict[str, Any],
                        run_idx: int,
                        seed: int) -> BaseModelSolution:
        """Build dataset, instantiate model, solve, and return the solution.

        Args:
            model_name: Which model to run (from
                [`OraclePaperModelNames`][oracle_paper.core.names.OraclePaperModelNames]).
            scenario: Dict with ``n_nodes``, ``n_clients``, ``n_hubs``,
                and ``alpha``.
            run_idx: Zero-based run index (for dataset seed offset).
            seed: Random seed for reproducibility.

        Returns:
            The solution produced by
            [`ModelSolver`][bilevelpy.solver.ModelSolver].

        Raises:
            ValueError: If ``model_name`` is not one of the four known models.
        """

        n_nodes = scenario.get("n_nodes")
        n_clients = scenario.get("n_clients")
        n_hubs = scenario.get("n_hubs")
        alpha = scenario.get("alpha")

        builder = (
            DatasetBuilder()
            .pipe(HLPLoader(Dataset.CAB100))
            .pipe(
                HLPNodeSelector(
                    n_nodes=n_nodes,
                    random_nodes=self._config.random_nodes,
                    seed=seed,
                )
            )
        )

        if self._config.scaling:
            builder.pipe(
                HLPCostScaling(
                    scaling_factor=self._config.scaling_factor
                )
            )

        builder.pipe(
            BilevelClientGenerator(
                clients_per_route=n_clients,
                random_count=self._config.random_n_clients_route,
                min_budget_factor=self._config.min_budget_factor,
                max_budget_factor=self._config.max_budget_factor,
                possible_weights=list(range(1, 21)),
                seed=seed,
            )
        )

        builder.pipe(LinearClientRanker())

        processors_metadata = {}

        if model_name == OraclePaperModelNames.PC_HLP:
            lagrange_calc = LagrangeCalculator()
            recursive_lagrange_calc = RecursiveLagrangeCalculator()

            dataset = (builder
                       .pipe(lagrange_calc)
                       .pipe(recursive_lagrange_calc)
                       .build())

            total_lagrange_time =  (lagrange_calc.get_all_metrics()["lagrange_time"]
                + recursive_lagrange_calc.get_all_metrics()["recursive_lagrange_time"])

            processors_metadata.update({
                "lagrange_time": total_lagrange_time,})

            model = PC_HLP(n_hubs=n_hubs, alpha=alpha, data=dataset)

        elif model_name == OraclePaperModelNames.PPC_HLP:
            lagrange_calc = LagrangeCalculator()

            dataset = (builder
                       .pipe(lagrange_calc)
                       .build())


            processors_metadata.update({
                "lagrange_time": lagrange_calc.get_all_metrics()["lagrange_time"],
            })

            model = PPC_HLP(n_hubs=n_hubs, alpha=alpha, data=dataset)

        elif model_name in (OraclePaperModelNames.PS_HLP, OraclePaperModelNames.PS_BHLP):
            dataset = builder.build()
            model_cls = PS_HLP if model_name == OraclePaperModelNames.PS_HLP else PS_BHLP
            model = model_cls(n_hubs=n_hubs, alpha=alpha, data=dataset)

        else:
            raise ValueError(f"Unknown method requested: {model_name}")



        solution = ModelSolver(model=model,
                               use_max_threads=False,
                               time_limit=self._config.time_limit).solve()

        solution.solution_metadata.extra.update(processors_metadata)

        total_n_clients = len(dataset[BilevelDataCol.CLIENT_KEY])
        solution.solution_metadata.extra["n_clients"] = total_n_clients

        print(f"Solution Metadata of {model_name}:\n{solution.solution_metadata}")

        return solution