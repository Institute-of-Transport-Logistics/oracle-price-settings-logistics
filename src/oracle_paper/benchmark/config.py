from dataclasses import dataclass, field
from typing import List, Dict, Literal


AllowedMethod = Literal["ps_hlp", "pc_hlp", "ppc_hlp", "ps_bhlp"]


@dataclass
class BenchmarkConfig:
    """Benchmark job configuration.

    Holds everything needed to describe a single benchmark queue entry:
    what ranges to sweep, which methods to run, and how results are saved.
    """
    n_hubs: int
    n_nodes_range: list[int]
    n_clients_range: list[int]
    methods: list[AllowedMethod]

    random_nodes: bool = True
    random_n_clients_route: bool = False

    alpha: float = 0.7

    min_budget_factor: float = 0.2
    max_budget_factor: float = 5.0

    time_limit: int = 3600
    mip_gap: float = 1e-4
    int_feas_tol: float = 1e-9

    benchmark_type: Literal["n_nodes", "n_clients"] = "n_nodes"

    file_name: str = "benchmark_results"
    output_dir: str = "benchmark_results"

    seed_dict: dict[int, int] = field(
        default_factory=lambda: {
            run: run for run in range(1, 11)
        }
    )
    n_runs: int = 10

    scaling: bool = True
    scaling_factor: int = 1000
