""" 📈 MLflow utilities for stouputils.

- :py:class:`~process_metrics_monitor.ProcessMetricsMonitor` - Log CPU, memory, I/O and thread metrics of a process tree to MLflow.

.. code-block:: python

	import time
	import mlflow
	import stouputils as stp
	from stouputils.mlflow import ProcessMetricsMonitor

	# Store the runs in a local database file
	mlflow.set_tracking_uri("sqlite:///mlflow.db")

	# Record the CPU and memory used by this process every 0.5 seconds while the block runs
	with mlflow.start_run() as run, ProcessMetricsMonitor(sampling_interval=0.5, verbose=True):
		blocks = []
		for _ in range(5):
			blocks.append(bytearray(100_000_000))  # Use 100 MB more memory
			time.sleep(0.6)

	# Read the memory curve back from MLflow
	history = mlflow.MlflowClient().get_metric_history(run.info.run_id, "system/process/memory_rss_megabytes")
	stp.info("Memory in MB, as logged:", [round(metric.value) for metric in history])

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/mlflow_module.svg
  :alt: Terminal output of the example, the memory curve as MLflow stored it
"""

# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
from .process_metrics_monitor import (
	ProcessMetricsMonitor as ProcessMetricsMonitor,
)

