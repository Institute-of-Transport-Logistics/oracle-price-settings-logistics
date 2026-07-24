"""Container for a collection of
[`BenchmarkResult`][oracle_paper.benchmark.result.BenchmarkResult] instances.
"""

from typing import List

import pandas as pd

from .result import BenchmarkResult


class BenchmarkResults:
    """Manages a collection of
    [`BenchmarkResult`][oracle_paper.benchmark.result.BenchmarkResult]
    instances.

    Provides utilities to add results, export to CSV, filter, and iterate.
    """

    def __init__(self, save: bool = False):
        self._results: List[BenchmarkResult] = []

    def add(self, result: BenchmarkResult) -> None:
        """Add a result to the collection."""
        self._results.append(result)

    def to_dicts(self) -> List[dict]:
        """Convert all results to a list of dictionaries."""
        return [r.to_dict() for r in self._results]

    def to_dataframe(self) -> pd.DataFrame:
        """Convert results to a pandas DataFrame."""
        return pd.DataFrame(self.to_dicts())

    def save_to_csv(self, path: str) -> None:
        """Save results to a CSV file."""
        self.to_dataframe().to_csv(path, index=False)

    def filter_by_method(self, method: str) -> List[BenchmarkResult]:
        """Filter stored results by method name."""
        return [r for r in self._results if r.method == method]

    def __iter__(self):
        return iter(self._results)

    def __len__(self) -> int:
        return len(self._results)