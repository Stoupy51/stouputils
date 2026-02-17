
# Imports
from __future__ import annotations

import os
import threading
from typing import Any

import psutil

from ..ctx.common import AbstractBothContextManager
from ..print.message import debug, info, warning


# Classes
class ProcessMetricsMonitor(AbstractBothContextManager["ProcessMetricsMonitor"]):
	""" Monitor that collects CPU, memory, I/O, and thread metrics for a specific
	process and (optionally) all its children, then logs them to MLflow.

	This is the per-process counterpart of MLflow's built-in
	``log_system_metrics=True`` which only captures **system-wide** metrics.
	Here every metric is scoped to the process tree rooted at *pid*.

	Metrics collected (all prefixed with ``process/``):

	- ``cpu_usage_percentage`` - cumulative CPU % (sum over the tree)
	- ``memory_rss_megabytes`` - resident set size in MB
	- ``memory_vms_megabytes`` - virtual memory size in MB
	- ``memory_uss_megabytes`` - unique set size in MB (Linux only, falls back to RSS)
	- ``memory_usage_percentage`` - RSS as % of total available RAM (see *max_memory_megabytes*)
	- ``num_threads`` - total thread count across the tree
	- ``num_fds`` - total open file descriptors (Linux only, 0 on other OS)
	- ``io_read_megabytes`` - cumulative bytes read in MB (since process start)
	- ``io_write_megabytes`` - cumulative bytes written in MB (since process start)

	Args:
		pid                     (int):      PID of the root process to monitor. Defaults to the current process (``os.getpid()``).
		children                (bool):     Whether to include child processes (recursively) in the metrics. Defaults to True.
		sampling_interval       (float):    Seconds between each sample collection. Defaults to 10.
		samples_before_logging  (int):      Number of samples to average before logging. Defaults to 1.
		prefix                  (str):      Metric name prefix. Defaults to ``"process/"``.
		verbose                 (bool):     Whether to log verbose debug messages. Defaults to False.
		max_memory_megabytes    (float):    Override the total memory in MB used to compute ``memory_usage_percentage``.
			Useful in containerized environments (e.g. Kubernetes pods) where ``psutil`` reports the
			host's total RAM instead of the container's limit. Defaults to ``None`` (use system total).
		max_cpu_count           (float):    Override the number of CPUs used to normalise ``cpu_usage_percentage``.
			For example, set to ``8.0`` when a pod is limited to 8 cores on a 128-core host.
			Defaults to ``None`` (use ``os.cpu_count()``).

	Examples:
		.. code-block:: python

			> import mlflow
			> from stouputils.mlflow.process_metrics_monitor import ProcessMetricsMonitor
			> mlflow.set_experiment("my_experiment")
			> with mlflow.start_run():
			.     monitor = ProcessMetricsMonitor(pid=12345, children=True, sampling_interval=5)
			.     monitor.start()
			.     # ... do heavy work ...
			.     monitor.finish()

		Or as a context manager:

		.. code-block:: python

			> import mlflow
			> from stouputils.mlflow.process_metrics_monitor import ProcessMetricsMonitor
			> mlflow.set_experiment("my_experiment")
			> with mlflow.start_run():
			.     with ProcessMetricsMonitor(pid=12345):
			.         # ... do heavy work ...
			.         pass
	"""

	def __init__(
		self,
		pid: int | None = None,
		children: bool = True,
		sampling_interval: float = 10.0,
		samples_before_logging: int = 1,
		prefix: str = "process/",
		verbose: bool = False,
		max_memory_megabytes: float | None = None,
		max_cpu_count: float | None = None,
	) -> None:
		self.pid: int = pid or os.getpid()
		""" PID of the root process to monitor. """
		self.children: bool = children
		""" Whether to include child processes recursively. """
		self.sampling_interval: float = sampling_interval
		""" Seconds between each sample collection. """
		self.samples_before_logging: int = max(1, samples_before_logging)
		""" Number of samples to average before logging. """
		self.prefix: str = prefix
		""" Metric name prefix. """
		self.verbose: bool = verbose
		""" Whether to log verbose debug messages. """
		self.max_memory_megabytes: float = max_memory_megabytes if max_memory_megabytes is not None else psutil.virtual_memory().total / (1024 ** 2)
		""" Total memory in MB used as the denominator for ``memory_usage_percentage``. """
		self.max_cpu_count: float = max_cpu_count if max_cpu_count is not None else float(os.cpu_count() or 1)
		""" Number of CPUs used to normalise ``cpu_usage_percentage`` (psutil returns per-core %). """

		self.run_id: str | None = None
		""" MLflow run ID captured at start time, ensures metrics are logged to the correct run from the daemon thread. """
		self.shutdown_event: threading.Event = threading.Event()
		""" Event used to signal the monitoring thread to stop. """
		self.thread: threading.Thread | None = None
		""" Reference to the monitoring daemon thread. """
		self.step: int = 0
		""" Current logging step counter. """
		self.samples: list[dict[str, float]] = []
		""" Buffer of collected metric samples waiting to be aggregated. """

	# Context manager interface
	def __enter__(self) -> ProcessMetricsMonitor:
		self.start()
		return self

	def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any | None) -> None:
		self.finish()

	async def __aenter__(self) -> ProcessMetricsMonitor:
		return self.__enter__()

	async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any | None) -> None:
		self.__exit__(exc_type, exc_val, exc_tb)



	# Public API
	def start(self) -> None:
		""" Start the background monitoring thread. """
		if self.thread is not None:
			warning("ProcessMetricsMonitor is already running.")
			return

		# Verify the target process exists before spawning the thread
		if not psutil.pid_exists(self.pid):
			warning(f"PID {self.pid} does not exist. ProcessMetricsMonitor will not start.")
			return

		# Prime cpu_percent for the root process (first call always returns 0)
		try:
			psutil.Process(self.pid).cpu_percent()
		except (psutil.NoSuchProcess, psutil.AccessDenied):
			pass

		# Capture the active run ID so the daemon thread logs to the correct run
		import mlflow
		active_run = mlflow.active_run() # type: ignore
		if active_run is None:
			warning("No active MLflow run found. ProcessMetricsMonitor will not start.")
			return
		self.run_id = str(active_run.info.run_id) # type: ignore

		self.shutdown_event.clear()
		self.thread = threading.Thread(
			target=self.monitor_loop,
			daemon=True,
			name="ProcessMetricsMonitor",
		)
		self.thread.start()
		if self.verbose:
			info(f"Started process metrics monitoring for PID {self.pid} (children={self.children}).")

	def finish(self) -> None:
		""" Stop monitoring and flush remaining metrics to MLflow. """
		if self.thread is None:
			return
		if self.verbose:
			info(f"Stopping process metrics monitoring for PID {self.pid}...")
		self.shutdown_event.set()
		self.thread.join(timeout=self.sampling_interval + 5)
		self.flush_remaining()
		self.thread = None
		if self.verbose:
			info("Successfully terminated process metrics monitoring.")



	# Internal
	def collect_once(self) -> dict[str, float]:
		""" Collect one snapshot of metrics for the process tree.

		Returns:
			dict[str, float]:	A dictionary of metric names to values.
		"""
		metrics: dict[str, float] = {
			"cpu_usage_percentage": 0.0,
			"memory_rss_megabytes": 0.0,
			"memory_vms_megabytes": 0.0,
			"memory_uss_megabytes": 0.0,
			"memory_usage_percentage": 0.0,
			"num_threads": 0.0,
			"num_fds": 0.0,
			"io_read_megabytes": 0.0,
			"io_write_megabytes": 0.0,
		}

		try:
			root: psutil.Process = psutil.Process(self.pid)
		except (psutil.NoSuchProcess, psutil.AccessDenied):
			return metrics

		procs: list[psutil.Process] = [root]
		if self.children:
			try:
				procs.extend(root.children(recursive=True))
			except (psutil.NoSuchProcess, psutil.AccessDenied):
				pass

		total_rss: float = 0.0
		for proc in procs:
			try:
				with proc.oneshot():
					# CPU
					metrics["cpu_usage_percentage"] += proc.cpu_percent()

					# Memory
					mem = proc.memory_info()
					rss_mb: float = mem.rss / (1024 ** 2)
					total_rss += rss_mb
					metrics["memory_rss_megabytes"] += rss_mb
					metrics["memory_vms_megabytes"] += mem.vms / (1024 ** 2)
					try:
						full_mem = proc.memory_full_info()
						metrics["memory_uss_megabytes"] += full_mem.uss / (1024 ** 2)
					except (psutil.AccessDenied, AttributeError):
						metrics["memory_uss_megabytes"] += rss_mb

					# Threads
					metrics["num_threads"] += proc.num_threads()

					# File descriptors (Linux only)
					try:
						metrics["num_fds"] += proc.num_fds()
					except (AttributeError, psutil.AccessDenied):
						pass

					# I/O counters
					try:
						io = proc.io_counters()
						metrics["io_read_megabytes"] += io.read_bytes / (1024 ** 2)
						metrics["io_write_megabytes"] += io.write_bytes / (1024 ** 2)
					except (psutil.AccessDenied, AttributeError):
						pass

			except (psutil.NoSuchProcess, psutil.AccessDenied):
				continue

		# Compute percentages using the configured maximums
		metrics["memory_usage_percentage"] = (total_rss / self.max_memory_megabytes * 100.0) if self.max_memory_megabytes > 0 else 0.0

		return metrics

	def aggregate(self, samples: list[dict[str, float]]) -> dict[str, float]:
		""" Average the collected samples.

		Args:
			samples (list[dict[str, float]]):	List of metric dictionaries.

		Returns:
			dict[str, float]:	A dictionary of averaged metric values.
		"""
		if not samples:
			return {}
		n: int = len(samples)
		keys: set[str] = set(samples[0].keys())
		return {k: sum(s[k] for s in samples) / n for k in keys}

	def publish(self, metrics: dict[str, float]) -> None:
		""" Log the aggregated metrics to the active MLflow run.

		Args:
			metrics (dict[str, float]):	Aggregated metric values.
		"""
		import mlflow

		prefixed: dict[str, float] = {self.prefix + k: v for k, v in metrics.items()}
		try:
			mlflow.log_metrics(prefixed, step=self.step, run_id=self.run_id) # type: ignore
		except Exception as e:
			warning(f"Failed to log process metrics at step {self.step}: {e}")
			return
		self.step += 1

	def monitor_loop(self) -> None:
		""" Main monitoring loop running in a daemon thread. """
		if self.verbose:
			debug(f"ProcessMetricsMonitor loop started (interval={self.sampling_interval}s, samples={self.samples_before_logging}).")

		while not self.shutdown_event.is_set():
			# Collect samples_before_logging samples
			local_samples: list[dict[str, float]] = []
			for _ in range(self.samples_before_logging):
				if self.shutdown_event.is_set():
					break
				sample: dict[str, float] = self.collect_once()
				local_samples.append(sample)
				self.shutdown_event.wait(self.sampling_interval)

			if not local_samples:
				break

			# Aggregate and publish
			aggregated: dict[str, float] = self.aggregate(local_samples)
			if aggregated:
				self.publish(aggregated)

	def flush_remaining(self) -> None:
		""" Flush any buffered samples that haven't been logged yet. """
		if self.samples:
			aggregated: dict[str, float] = self.aggregate(self.samples)
			if aggregated:
				self.publish(aggregated)
			self.samples.clear()

