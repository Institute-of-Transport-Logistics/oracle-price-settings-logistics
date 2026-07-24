"""Saves raw benchmark results to timestamped folders.

File paths are built from the benchmark config and the current date/time.
"""

import logging
import os
from datetime import datetime

from .config import BenchmarkConfig
from .results import BenchmarkResults


class BenchmarkResultsSaver:
    """Saves raw benchmark results to timestamped folders.

    File paths are constructed from benchmark configuration and the
    current date/time.
    """

    def __init__(self, bench_config: BenchmarkConfig) -> None:
        self.bench_config = bench_config
        self.file_name = bench_config.file_name
        self.file_path = self._build_file_path()

        os.makedirs(self.file_path, exist_ok=True)
        self._logger = self._init_logger()

        # Full base path (no extension)
        self.file_name = os.path.join(self.file_path, self.file_name)

    def _build_file_path(self) -> str:
        """Build a structured folder path from config and current time."""
        now = datetime.now()
        formatted_date = now.strftime("%Y_%m_%d_%H_%M")

        path = f"{self.bench_config.output_dir}/{formatted_date}"

        if self.bench_config.benchmark_type == "n_nodes":
            rng = self.bench_config.n_nodes_range
            path += f"/n_nodes/node_range_{rng[0]}_{rng[-1]}"
            path += f"/clients_{self.bench_config.n_clients_range[0]}"
        else:
            rng = self.bench_config.n_clients_range
            path += f"/n_clients/n_clients_range_{rng[0]}_{rng[-1]}"
            path += f"/n_nodes_{self.bench_config.n_nodes_range[0]}"

        path += f"/n_hubs_{self.bench_config.n_hubs}"
        return path

    def _init_logger(self) -> logging.Logger:
        log_file = os.path.join(self.file_path, "execution.log")

        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)

        has_file_handler = any(
            isinstance(h, logging.FileHandler)
            and os.path.abspath(h.baseFilename) == os.path.abspath(log_file)
            for h in logger.handlers
        )

        if not has_file_handler:
            fh = logging.FileHandler(log_file, mode="a")
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            fh.setFormatter(formatter)
            logger.addHandler(fh)

        if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
            sh = logging.StreamHandler()
            sh.setFormatter(formatter)
            logger.addHandler(sh)

        return logger

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    def save_benchmark_raw_results(self, benchmark_results: BenchmarkResults) -> None:
        """Save raw benchmark results to CSV.

        Args:
            benchmark_results: The results collection to persist.
        """
        raw_csv = self.file_name + "_raw.csv"
        benchmark_results.save_to_csv(raw_csv)