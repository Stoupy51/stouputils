""" MLflow utilities for stouputils.

- :py:class:`~process_metrics_monitor.ProcessMetricsMonitor` - Monitor CPU, memory, I/O, and thread metrics for a specific process tree and log them to MLflow.
"""

# Lazy imports (PEP 810), ignored before Python 3.15
__lazy_modules__: frozenset[str] = frozenset({
	"stouputils.mlflow.process_metrics_monitor",
})

# Imports
from .process_metrics_monitor import (
	ProcessMetricsMonitor as ProcessMetricsMonitor,
)

