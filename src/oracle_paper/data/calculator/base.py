"""Base classes for calculation processors that track their own performance metrics."""

import time
from functools import wraps
from typing import Any, Callable

from bilevelpy.data.base_processor import EntityProcessor


class TrackableProcessor(EntityProcessor):
	"""Mixin for entity processors that track calculation metrics.

	Provides ``set_metric`` / ``get_metric`` / ``get_all_metrics`` so
	processors can record timing and other data that flows into benchmark
	results and solution metadata.
	"""

	def __init__(self):
		"""Initialize the processor with metadata storage."""
		super().__init__()
		self._processor_metadata: dict[str, Any] = {}

	def set_metric(self, key: str, value: Any) -> None:
		"""Store a metric value."""
		self._processor_metadata[key] = value

	def get_metric(self, key: str) -> Any:
		"""Retrieve a metric value."""
		return self._processor_metadata.get(key)

	def get_all_metrics(self) -> dict[str, Any]:
		"""Get all recorded metrics."""
		return self._processor_metadata.copy()


def track_metric(metric_name: str) -> Callable:
	"""
	Decorator to automatically track calculation time for a method.

	Args:
		metric_name: The name to store the metric under (e.g., "lagrange_time")

	Example:
		@track_metric("lagrange_calculation_time")
		def process(self, dataset):
			# ... calculation code ...

	The decorated method must be part of a TrackableProcessor instance.
	The elapsed time will be stored via set_metric(metric_name, elapsed_time).
	"""

	def decorator(func: Callable) -> Callable:
		@wraps(func)
		def wrapper(self, *args, **kwargs) -> Any:
			start_time = time.time()
			try:
				result = func(self, *args, **kwargs)
				return result
			finally:
				elapsed_time = time.time() - start_time
				# Only store if the instance supports metrics (TrackableProcessor)
				if hasattr(self, "set_metric"):
					self.set_metric(metric_name, elapsed_time)

		return wrapper

	return decorator

