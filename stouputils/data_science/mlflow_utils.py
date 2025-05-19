"""
This module contains utility functions for working with MLflow.

This module contains functions for:

- Getting the artifact path from the current mlflow run
- Getting the weights path
- Getting the runs by experiment name
- Logging the history of the model to the current mlflow run
- Starting a new mlflow run
"""

# Imports
import os
from typing import Any, Literal

import mlflow
from mlflow.entities import Experiment, Run

from ..decorators import handle_error, LogLevels
from ..io import clean_path


# Get artifact path
def get_artifact_path(from_string: str = "", os_name: str = os.name) -> str:
	""" Get the artifact path from the current mlflow run (without the file:// prefix).

	Handles the different path formats for Windows and Unix-based systems.

	Args:
		from_string	(str):		Path to the artifact (optional, defaults to the current mlflow run)
		os_name		(str):		OS name (optional, defaults to os.name)
	Returns:
		str: The artifact path
	"""
	# Get the artifact path from the current mlflow run or from a string
	if not from_string:
		artifact_path: str = mlflow.get_artifact_uri()
	else:
		artifact_path: str = from_string

	# Handle the different path formats for Windows and Unix-based systems
	if os_name == "nt":
		return artifact_path.replace("file:///", "")
	else:
		return artifact_path.replace("file://", "")

# Get weights path
def get_weights_path(from_string: str = "", weights_name: str = "best_model.keras", os_name: str = os.name) -> str:
	""" Get the weights path from the current mlflow run.

	Args:
		from_string     (str):      Path to the artifact (optional, defaults to the current mlflow run)
		weights_name    (str):      Name of the weights file (optional, defaults to "best_model.keras")
		os_name         (str):      OS name (optional, defaults to os.name)
	Returns:
		str: The weights path

	Examples:
		>>> get_weights_path(from_string="file:///path/to/artifact", weights_name="best_model.keras", os_name="posix")
		'/path/to/artifact/best_model.keras'

		>>> get_weights_path(from_string="file:///C:/path/to/artifact", weights_name="best_model.keras", os_name="nt")
		'C:/path/to/artifact/best_model.keras'
	"""
	return clean_path(f"{get_artifact_path(from_string=from_string, os_name=os_name)}/{weights_name}")

# Get runs by experiment name
def get_runs_by_experiment_name(experiment_name: str, filter_string: str = "", set_experiment: bool = False) -> list[Run]:
	""" Get the runs by experiment name.

	Args:
		experiment_name		(str):		Name of the experiment
		filter_string		(str):		Filter string to apply to the runs
		set_experiment		(bool):		Whether to set the experiment
	Returns:
		list[Run]:		List of runs
	"""
	if set_experiment:
		mlflow.set_experiment(experiment_name)
	experiment: Experiment | None = mlflow.get_experiment_by_name(experiment_name)
	if experiment:
		return mlflow.search_runs(
			experiment_ids=[experiment.experiment_id],
			output_format="list",
			filter_string=filter_string
		) # pyright: ignore [reportReturnType]
	return []

def get_runs_by_model_name(experiment_name: str, model_name: str, set_experiment: bool = False) -> list[Run]:
	""" Get the runs by model name.

	Args:
		experiment_name	(str):		Name of the experiment
		model_name		(str):		Name of the model
		set_experiment	(bool):		Whether to set the experiment
	Returns:
		list[Run]:		List of runs
	"""
	return get_runs_by_experiment_name(
		experiment_name,
		filter_string=f"tags.model_name = '{model_name}'",
		set_experiment=set_experiment
	)

# Log history
def log_history(history: dict[str, list[Any]], prefix: str = "history", **kwargs: Any) -> None:
	""" Log the history of the model to the current mlflow run.

	Args:
		history		(dict[str, list[Any]]):	History of the model
			(usually from a History object like from a Keras model: history.history)
		**kwargs	(Any):					Additional arguments to pass to mlflow.log_metric
	"""
	for (metric, values) in history.items():
		for epoch, value in enumerate(values):
			handle_error(mlflow.log_metric,
				message=f"Error logging metric {metric}",
				error_log=LogLevels.ERROR_TRACEBACK
			)(f"{prefix}_{metric}", value, step=epoch, **kwargs)


def start_run(mlflow_uri: str, experiment_name: str, model_name: str, override_run_name: str = "", **kwargs: Any) -> str:
	""" Start a new mlflow run.

	Args:
		mlflow_uri			(str):		MLflow URI
		experiment_name		(str):		Name of the experiment
		model_name			(str):		Name of the model
		override_run_name	(str):		Override the run name (if empty, it will be set automatically)
		**kwargs			(Any):		Additional arguments to pass to mlflow.start_run
	Returns:
		str: Name of the run (suffixed with the version number)
	"""
	# Set the mlflow URI
	mlflow.set_tracking_uri(mlflow_uri)

	# Get the runs and increment the version number
	runs: list[Run] = get_runs_by_model_name(experiment_name, model_name, set_experiment=True)
	run_number: int = len(runs) + 1
	run_name: str = f"{model_name}_v{run_number:02d}" if not override_run_name else override_run_name

	# Start the run
	mlflow.start_run(run_name=run_name, tags={"model_name": model_name}, log_system_metrics=True, **kwargs)
	return run_name

# Get best run by metric
def get_best_run_by_metric(
	experiment_name: str,
	metric_name: str,
	model_name: str = "",
	ascending: bool = False,
	has_saved_model: bool = True
) -> Run | None:
	""" Get the best run by a specific metric.

	Args:
		experiment_name  (str):    Name of the experiment
		metric_name      (str):    Name of the metric to sort by
		model_name       (str):    Name of the model (optional, if empty, all models are considered)
		ascending        (bool):   Whether to sort in ascending order (default: False, i.e. maximum metric value is best)
		has_saved_model  (bool):   Whether the model has been saved (default: True)
	Returns:
		Run | None: The best run or None if no runs are found
	"""
	# Get the runs
	filter_string: str = f"metrics.`{metric_name}` > 0"
	if model_name:
		filter_string += f" AND tags.model_name = '{model_name}'"
	if has_saved_model:
		filter_string += " AND tags.has_saved_model = 'True'"

	runs: list[Run] = get_runs_by_experiment_name(
		experiment_name,
		filter_string=filter_string,
		set_experiment=True
	)

	if not runs:
		return None

	# Sort the runs by the metric
	sorted_runs: list[Run] = sorted(
		runs,
		key=lambda run: float(run.data.metrics.get(metric_name, 0)), # type: ignore
		reverse=not ascending
	)

	return sorted_runs[0] if sorted_runs else None


def load_model(run_id: str, model_type: Literal["keras", "pytorch"] = "keras") -> Any:
	""" Load a model from MLflow.

	Args:
		run_id      (str):                          ID of the run to load the model from
		model_type  (Literal["keras", "pytorch"]):  Type of model to load (default: "keras")
	Returns:
		Any: The loaded model
	"""
	if model_type == "keras":
		return mlflow.keras.load_model(f"runs:/{run_id}/best_model") # type: ignore
	elif model_type == "pytorch":
		return mlflow.pytorch.load_model(f"runs:/{run_id}/best_model") # type: ignore
	raise ValueError(f"Model type {model_type} not supported")

