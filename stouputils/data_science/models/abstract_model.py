""" Abstract base class for all model implementations.
Defines the interface that all concrete model classes must implement.

Provides abstract methods for core model operations including:

- Class routine management
- Model loading
- Training procedures
- Prediction functionality
- Evaluation metrics

Classes inheriting from AbstractModel must implement all methods.
"""

# Imports
from __future__ import annotations

import multiprocessing.queues
from collections.abc import Iterable
from tempfile import TemporaryDirectory
from typing import Any

from ...decorators import abstract, LogLevels

from ..dataset import Dataset


# Base class
class AbstractModel:
	""" Abstract class for all models to copy and implement the methods. """
	# Class methods
	@abstract(error_log=LogLevels.ERROR_TRACEBACK)
	def __init__(
		self, num_classes: int, kfold: int = 0, transfer_learning: str = "imagenet", **override_params: Any
	) -> None:
		pass


	## Public abstract methods
	@abstract(error_log=LogLevels.ERROR_TRACEBACK)
	def routine_full(self, dataset: Dataset, verbose: int = 0) -> AbstractModel:
		return self

	@abstract(error_log=LogLevels.ERROR_TRACEBACK)
	def class_load(self) -> None:
		pass


	@abstract(error_log=LogLevels.ERROR_TRACEBACK)
	def class_train(self, dataset: Dataset, verbose: int = 0) -> bool:
		return False


	@abstract(error_log=LogLevels.ERROR_TRACEBACK)
	def class_predict(self, X_test: Iterable[Any]) -> Iterable[Any]:
		return []


	@abstract(error_log=LogLevels.ERROR_TRACEBACK)
	def class_evaluate(
		self,
		dataset: Dataset,
		metrics_names: tuple[str, ...] = (),
		save_model: bool = False,
		verbose: int = 0
	) -> bool:
		return False


	## Protected abstract methods
	@abstract(error_log=LogLevels.ERROR_TRACEBACK)
	def _fit(
		self,
		model: Any,
		x: Any,
		y: Any | None = None,
		validation_data: tuple[Any, Any] | None = None,
		shuffle: bool = True,
		batch_size: int | None = None,
		epochs: int = 1,
		callbacks: list[Any] | None = None,
		class_weight: dict[int, float] | None = None,
		verbose: int = 0,
		*args: Any,
		**kwargs: Any
	) -> Any:
		pass

	@abstract(error_log=LogLevels.ERROR_TRACEBACK)
	def _get_callbacks(self) -> list[Any]:
		return []

	@abstract(error_log=LogLevels.ERROR_TRACEBACK)
	def _get_metrics(self) -> list[Any]:
		return []

	@abstract(error_log=LogLevels.ERROR_TRACEBACK)
	def _get_optimizer(self, learning_rate: float = 0.0) -> Any:
		pass

	@abstract(error_log=LogLevels.ERROR_TRACEBACK)
	def _get_loss(self) -> Any:
		pass

	@abstract(error_log=LogLevels.ERROR_TRACEBACK)
	def _get_base_model(self) -> Any:
		pass

	@abstract(error_log=LogLevels.ERROR_TRACEBACK)
	def _get_architectures(
		self, optimizer: Any = None, loss: Any = None, metrics: list[Any] | None = None
	) -> tuple[Any, Any]:
		return (None, None)

	@abstract(error_log=LogLevels.ERROR_TRACEBACK)
	def _find_best_learning_rate(self, dataset: Dataset, verbose: int = 0) -> float:
		return 0.0

	@abstract(error_log=LogLevels.ERROR_TRACEBACK)
	def _train_fold(self, dataset: Dataset, fold_number: int = 0, mlflow_prefix: str = "history", verbose: int = 0) -> Any:
		pass

	@abstract(error_log=LogLevels.ERROR_TRACEBACK)
	def _log_final_model(self) -> None:
		pass

	@abstract(error_log=LogLevels.ERROR_TRACEBACK)
	def _find_best_learning_rate_subprocess(
		self, dataset: Dataset, queue: multiprocessing.queues.Queue[Any] | None = None, verbose: int = 0
	) -> dict[str, Any] | None:
		pass

	@abstract(error_log=LogLevels.ERROR_TRACEBACK)
	def _find_best_unfreeze_percentage_subprocess(
		self, dataset: Dataset, queue: multiprocessing.queues.Queue[Any] | None = None, verbose: int = 0
	) -> dict[str, Any] | None:
		pass

	@abstract(error_log=LogLevels.ERROR_TRACEBACK)
	def _train_subprocess(
		self,
		dataset: Dataset,
		checkpoint_path: str,
		temp_dir: TemporaryDirectory[str] | None = None,
		queue: multiprocessing.queues.Queue[Any] | None = None,
		verbose: int = 0
	) -> dict[str, Any] | None:
		pass

