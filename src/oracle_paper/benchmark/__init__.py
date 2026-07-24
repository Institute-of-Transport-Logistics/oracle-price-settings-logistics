import subprocess
import sys
from pathlib import Path

from oracle_paper.benchmark.config import BenchmarkConfig
from oracle_paper.benchmark.model_provider import PaperModelProvider
from oracle_paper.benchmark.result import BenchmarkResult
from oracle_paper.benchmark.results import BenchmarkResults
from oracle_paper.benchmark.results_saver import BenchmarkResultsSaver
from oracle_paper.benchmark.runner import BenchmarkRunner

__all__ = [
    "BenchmarkConfig",
    "BenchmarkResult",
    "BenchmarkResults",
    "BenchmarkResultsSaver",
    "BenchmarkRunner",
    "PaperModelProvider",
]


def main() -> None:
    """Launch the Streamlit benchmark UI."""
    app = Path(__file__).resolve().parents[3] / "reproduce" / "benchmarking_tool.py"
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(app)])