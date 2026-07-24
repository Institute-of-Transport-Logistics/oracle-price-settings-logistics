"""Benchmark result data class for a single model run."""

from dataclasses import dataclass, asdict
from typing import Any, Dict

from bilevelpy.solution import BaseModelSolution

from .config import BenchmarkConfig


@dataclass
class BenchmarkResult:
    """Stores the result of a single benchmark solve.

    Captures the configuration parameters (nodes, hubs, clients, seed)
    together with the solution metrics returned by a specific model/solver
    run (solving time, optimality gap, node count, etc.).
    """

    # Configuration
    n_nodes: int
    n_hubs: int
    alpha: float
    method: str

    # Timing
    total_time: float | None
    solving_time: float | None
    lagrange_time: float | None

    # Solution quality
    optimal: bool | None
    gap: float | None
    node_count: int | None

    # Problem-specific
    n_clients: int | None
    n_clients_route: int
    random_n_clients_route: bool
    min_budget_factor: float
    max_budget_factor: float

    # Run info
    run_number: int
    seed: int
    sanctioned: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a plain dictionary."""
        return asdict(self)

    @classmethod
    def sanctioned_method(
        cls,
        config: BenchmarkConfig,
        method: str,
        n_nodes: int,
        n_clients: int,
        run: int,
    ) -> "BenchmarkResult":
        """Create a placeholder result for a sanctioned (skipped) method."""
        return cls(
            n_nodes=n_nodes,
            n_hubs=config.n_hubs,
            alpha=config.alpha,
            method=method,
            total_time=None,
            solving_time=None,
            lagrange_time=None,
            optimal=None,
            gap=None,
            node_count=None,
            n_clients=None,
            n_clients_route=n_clients,
            random_n_clients_route=config.random_n_clients_route,
            min_budget_factor=config.min_budget_factor,
            max_budget_factor=config.max_budget_factor,
            run_number=run,
            seed=config.seed_dict[run],
            sanctioned=True,
        )

    @classmethod
    def from_solution(
        cls,
        solution: BaseModelSolution,
        config: BenchmarkConfig,
        n_nodes: int,
        n_clients: int,
        run: int,
        method: str,
    ) -> "BenchmarkResult":
        """Construct from a
        [`BaseModelSolution`][bilevelpy.solution.core.BaseModelSolution]
        and benchmark configuration.

        Args:
            solution: The solution returned by the solver.
            config: The benchmark configuration.
            n_nodes: Number of nodes in the instance.
            n_clients: Number of clients per route.
            run: Run number (1-indexed, for seed lookup).
            method: Method string key (e.g. ``"pc_hlp"``).
        """
        meta = solution.solution_metadata
        extra = meta.extra if hasattr(meta, "extra") else {}

        lagrange_time = extra.get("lagrange_time", 0.0) or 0.0
        total_time = float(meta.solving_time) + float(lagrange_time)

        return cls(
            n_nodes=n_nodes,
            n_hubs=config.n_hubs,
            alpha=config.alpha,
            method=method,
            total_time=total_time,
            solving_time=float(meta.solving_time),
            lagrange_time=float(lagrange_time),
            optimal=meta.is_optimal,
            gap=float(meta.mip_gap),
            node_count=int(meta.node_count),
            n_clients=extra.get("n_clients", 0),
            n_clients_route=n_clients,
            random_n_clients_route=config.random_n_clients_route,
            min_budget_factor=config.min_budget_factor,
            max_budget_factor=config.max_budget_factor,
            run_number=run,
            seed=config.seed_dict[run],
        )