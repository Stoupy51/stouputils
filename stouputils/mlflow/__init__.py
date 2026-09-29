""" MLflow utilities for stouputils.

- :py:class:`~process_metrics_monitor.ProcessMetricsMonitor` - Log CPU, memory, I/O and thread metrics of a process tree to MLflow.
"""

# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
from .process_metrics_monitor import (
	ProcessMetricsMonitor as ProcessMetricsMonitor,
)

