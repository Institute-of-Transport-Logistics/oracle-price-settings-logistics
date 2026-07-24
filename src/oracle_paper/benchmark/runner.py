"""Benchmark runner — orchestrates model building, solving, and result collection."""

from typing import Callable, Dict, List

from .model_provider import PaperModelProvider
from oracle_paper.core.names import OraclePaperModelNames
from bilevelpy.models.meta import ModelMetaData

from .config import BenchmarkConfig
from .result import BenchmarkResult
from .results import BenchmarkResults
from .results_saver import BenchmarkResultsSaver


# Map old string method keys → ModelMetaData instances
METHOD_MAP: Dict[str, ModelMetaData] = {
    "ps_hlp": OraclePaperModelNames.PS_HLP,
    "pc_hlp": OraclePaperModelNames.PC_HLP,
    "ppc_hlp": OraclePaperModelNames.PPC_HLP,
    "ps_bhlp": OraclePaperModelNames.PS_BHLP,
}


class BenchmarkRunner:
    """Runs benchmark experiments from a
    [`BenchmarkConfig`][oracle_paper.benchmark.config.BenchmarkConfig].

    For each scenario (varying ``n_nodes`` or ``n_clients``), it calls
    `PaperModelProvider.build_and_solve` for every method × run
    combination, collects
    [`BenchmarkResult`][oracle_paper.benchmark.result.BenchmarkResult]
    entries, and streams raw results to disk after each solve.

    Supports optional progress and result callbacks for live UIs.
    """

    def __init__(self, config: BenchmarkConfig) -> None:
        self.config = config
        self.provider = PaperModelProvider(config=config)

        self.benchmark_saver = BenchmarkResultsSaver(config)
        self._results = BenchmarkResults()

        # Callbacks
        self.callbacks: List[Callable[[BenchmarkResults], None]] = []
        self.progress_callback: Callable[[int, int, str], None] | None = None
        self.total_steps = 0
        self.current_step = 0

        # Sanctioning state (per method string key)
        self.sanctions_dict: Dict[str, int] = dict.fromkeys(config.methods, 0)
        self.is_sanctioned: Dict[str, bool] = dict.fromkeys(config.methods, False)

    def add_callback(self, callback_fn: Callable[[BenchmarkResults], None]) -> None:
        """Register a callback invoked after each result is added."""
        self.callbacks.append(callback_fn)

    def set_progress_callback(
        self, callback: Callable[[int, int, str], None]
    ) -> None:
        """Register a progress callback: ``fn(current, total, status_text)``."""
        self.progress_callback = callback

    def run(self) -> None:
        """Execute the full benchmark grid."""
        logger = self.benchmark_saver.logger
        logger.info(f"Running benchmark: {self.config.benchmark_type}")

        scenarios = self._build_scenarios()
        self.total_steps = (
            len(scenarios) * self.config.n_runs * len(self.config.methods)
        )
        self.current_step = 0

        for scenario in scenarios:
            n_nodes = scenario["n_nodes"]
            n_clients = scenario["n_clients"]
            logger.info(f"n_nodes={n_nodes}, n_clients={n_clients}")

            for run in range(1, self.config.n_runs + 1):
                seed = self.config.seed_dict[run]
                run_idx = run - 1  # 0-indexed for the provider
                logger.info(f"\tRun={run}")

                for method_str in self.config.methods:
                    self.current_step += 1

                    if self.progress_callback:
                        info = (
                            f"Nodes: {n_nodes} | Clients: {n_clients} | "
                            f"Run: {run}/{self.config.n_runs} | Method: {method_str}"
                        )
                        self.progress_callback(
                            self.current_step, self.total_steps, info
                        )

                    # --- Sanctioning logic ---
                    if run == 1:
                        if self.sanctions_dict[method_str] >= self.config.n_runs:
                            self.is_sanctioned[method_str] = True
                            logger.warning(
                                f"\t\tMethod {method_str} has been sanctioned."
                            )
                        else:
                            self.sanctions_dict[method_str] = 0

                    if self.is_sanctioned[method_str]:
                        result = BenchmarkResult.sanctioned_method(
                            config=self.config,
                            method=method_str,
                            n_nodes=n_nodes,
                            n_clients=n_clients,
                            run=run,
                        )
                        self._results.add(result)
                        self.benchmark_saver.save_benchmark_raw_results(self._results)
                        self._notify_callbacks()
                        logger.warning(
                            f"\t\tSanctioned method {method_str} skipped."
                        )
                        continue

                    # --- Build & solve ---
                    model_meta = METHOD_MAP.get(method_str)
                    if model_meta is None:
                        logger.warning(
                            f"\t\tUnknown method '{method_str}', skipping."
                        )
                        result = BenchmarkResult.sanctioned_method(
                            config=self.config,
                            method=method_str,
                            n_nodes=n_nodes,
                            n_clients=n_clients,
                            run=run,
                        )
                        self._results.add(result)
                        self.benchmark_saver.save_benchmark_raw_results(self._results)
                        self._notify_callbacks()
                        continue

                    try:
                        solution = self.provider.build_and_solve(
                            model_name=model_meta,
                            scenario=scenario,
                            run_idx=run_idx,
                            seed=seed,
                        )
                    except Exception:
                        logger.exception(
                            "Unexpected benchmark failure for %s",
                            method_str,
                        )
                        raise

                    # --- Collect result ---
                    result = BenchmarkResult.from_solution(
                        solution=solution,
                        config=self.config,
                        n_nodes=n_nodes,
                        n_clients=n_clients,
                        run=run,
                        method=method_str,
                    )

                    if not result.optimal:
                        self.sanctions_dict[method_str] += 1
                        logger.warning(
                            f"\t\tSolution not optimal for {method_str}, "
                            f"sanction counter: {self.sanctions_dict[method_str]}"
                        )
                    else:
                        logger.info(
                            f"\t\tOptimal solution for {method_str}, "
                            f"solving time: {result.solving_time:.2f}s"
                        )

                    self._results.add(result)
                    self.benchmark_saver.save_benchmark_raw_results(self._results)
                    self._notify_callbacks()

                    # Dispose Gurobi model to free memory
                    try:
                        solution.dispose()
                    except Exception:
                        pass

    def _build_scenarios(self) -> List[Dict]:
        """Build a flat list of scenario dicts from the config ranges."""
        scenarios: List[Dict] = []
        if self.config.benchmark_type == "n_nodes":
            for n_nodes in self.config.n_nodes_range:
                scenarios.append({
                    "n_nodes": n_nodes,
                    "n_clients": self.config.n_clients_range[0],
                    "n_hubs": self.config.n_hubs,
                    "alpha": self.config.alpha,
                })
        else:
            for n_clients in self.config.n_clients_range:
                scenarios.append({
                    "n_nodes": self.config.n_nodes_range[0],
                    "n_clients": n_clients,
                    "n_hubs": self.config.n_hubs,
                    "alpha": self.config.alpha,
                })
        return scenarios

    def _notify_callbacks(self) -> None:
        """Notify all registered callbacks with the current result set."""
        for cb in self.callbacks:
            cb(self._results)