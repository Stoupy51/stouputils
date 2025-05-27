""" Base implementation for machine learning models with common functionality.
Provides shared infrastructure for model training, evaluation, and MLflow integration.

Implements core workflow methods:

- Full training/evaluation pipeline (routine_full)
- Transfer learning weight management
- MLflow experiment tracking integration
"""
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownArgumentType=false

# Imports
from __future__ import annotations

import gc
import multiprocessing
import multiprocessing.queues
from collections.abc import Generator, Iterable
from tempfile import TemporaryDirectory
from typing import Any

import mlflow
import numpy as np
from mlflow.entities import Run
from numpy.typing import NDArray
from sklearn.utils import class_weight

from ...decorators import handle_error, measure_time
from ...print import progress, debug, info
from ...ctx import Muffle, MeasureTime
from ...io import clean_path

from .. import mlflow_utils
from ..config.get import DataScienceConfig
from ..dataset import Dataset, DatasetLoader, XyTuple
from ..metric_dictionnary import MetricDictionnary
from ..metric_utils import MetricUtils
from ..utils import Utils
from .abstract_model import AbstractModel

# Constants
MODEL_DOCSTRING: str = """ {model} implementation using advanced model class with common functionality.
For information, refer to the ModelInterface class.
"""
CLASS_ROUTINE_DOCSTRING: str = """ Run the full routine for {model} model.

Args:
	dataset            (Dataset): Dataset to use for training and evaluation.
	kfold              (int): K-fold cross validation index.
	transfer_learning  (str): Pre-trained weights to use, can be "imagenet" or a dataset path like 'data/pizza_not_pizza'.
	verbose            (int): Verbosity level.
	**kwargs           (Any): Additional arguments.

Returns:
	{model}: Trained model instance.
"""

# Base class
class ModelInterface(AbstractModel):
	""" Base class for all models containing common/public methods. """

	# Class constructor
	def __init__(
		self, num_classes: int, kfold: int = 0, transfer_learning: str = "imagenet", **override_params: Any
	) -> None:
		np.random.seed(DataScienceConfig.SEED)
		multiprocessing.set_start_method("spawn", force=True)

		## Base attributes
		self.final_model: Any
		""" Attribute storing the final trained model (Keras model or PyTorch model). """
		self.model_name: str = self.__class__.__name__
		""" Attribute storing the name of the model class, automatically set from the class name.
		Used for logging and display purposes. """
		self.kfold: int = kfold
		""" Attribute storing the number of folds to use for K-fold cross validation.
		If 0 or 1, no K-fold cross validation is used. If > 1, uses K-fold cross validation with that many folds. """
		self.transfer_learning: str = transfer_learning
		""" Attribute storing the transfer learning source, defaults to "imagenet",
		can be set to None or a dataset name present in the data folder. """
		self.is_trained: bool = False
		""" Flag indicating if the model has been trained.
		Must be True before making predictions or evaluating the model. """
		self.num_classes: int = num_classes
		""" Attribute storing the number of classes in the dataset. """
		self.override_params: dict[str, Any] = override_params
		""" Attribute storing the override parameters dictionary for the model. """
		self.run_name: str = ""
		""" Attribute storing the name of the current run, automatically set during training. """
		self.history: list[dict[str, list[float]]] = []
		""" Attribute storing the training history for each fold. """
		self.evaluation_results: list[dict[str, float]] = []
		""" Attribute storing the evaluation results for each fold. """
		self.additional_training_data: XyTuple = XyTuple.empty()
		""" Attribute storing additional training data as a XyTuple
		that is incorporated into the training set right before model fitting.

		This data bypasses cross-validation splitting and is only used during the training phase which
		differs from directly augmenting the dataset via dataset.training_data += additional_training_data,
		which would include the additional data in the cross-validation splitting process.
		"""


		## Model parameters
		# Training parameters
		self.batch_size: int = 8
		""" Attribute storing the batch size for training. """
		self.epochs: int = 50
		""" Attribute storing the number of epochs for training. """
		self.class_weight: dict[int, float] | None = None
		""" Attribute storing the class weights for training, e.g. {0: 0.34, 1: 0.66}. """

		# Fine-tuning parameters
		self.unfreeze_percentage: float = 100
		""" Attribute storing the percentage of layers to fine-tune from the last layer of the base model (0-100). """
		self.fine_tune_last_layers: int = -1
		""" Attribute storing the number of layers to fine-tune, calculated from percentage when total_layers is known. """

		# Optimizer parameters
		self.beta_1: float = 0.95
		""" Attribute storing the beta 1 for Adam optimizer. """
		self.beta_2: float = 0.999
		""" Attribute storing the beta 2 for Adam optimizer. """

		# Callback parameters
		self.early_stop_patience: int = 15
		""" Attribute storing the patience for early stopping. """
		self.model_checkpoint_delay: int = 0
		""" Attribute storing the number of epochs before starting the checkpointing. """

		# ReduceLROnPlateau parameters
		self.learning_rate: float = 1e-4
		""" Attribute storing the learning rate for training. """
		self.reduce_lr_patience: int = 5
		""" Attribute storing the patience for ReduceLROnPlateau. """
		self.min_delta: float = 0.05
		""" Attribute storing the minimum delta for ReduceLROnPlateau (default of the library is 0.0001). """
		self.min_lr: float = 1e-7
		""" Attribute storing the minimum learning rate for ReduceLROnPlateau. """
		self.factor: float = 0.5
		""" Attribute storing the factor for ReduceLROnPlateau. """

		# Warmup parameters
		self.warmup_epochs: int = 5
		""" Attribute storing the number of epochs for learning rate warmup (0 to disable). """
		self.initial_warmup_lr: float = 1e-7
		""" Attribute storing the initial learning rate for warmup. """

		# Learning Rate Finder parameters
		self.lr_finder_min_lr: float = 1e-9
		""" Attribute storing the *minimum* learning rate for the LR Finder. """
		self.lr_finder_max_lr: float = 1.0
		""" Attribute storing the *maximum* learning rate for the LR Finder. """
		self.lr_finder_epochs: int = 3
		""" Attribute storing the number of epochs for the LR Finder. """
		self.lr_finder_update_per_epoch: bool = False
		""" Attribute storing if the LR Finder should increase LR every epoch (True) or batch (False). """
		self.lr_finder_update_interval: int = 5
		""" Attribute storing the number of steps between each lr increase, bigger value means more stable loss. """

		# Unfreeze Percentage Finder parameters
		self.unfreeze_finder_epochs: int = 500
		""" Attribute storing the number of epochs for the Unfreeze Percentage Finder """
		self.unfreeze_finder_update_per_epoch: bool = True
		""" Attribute storing if the Unfreeze Finder should unfreeze every epoch (True) or batch (False). """
		self.unfreeze_finder_update_interval: int = 25
		""" Attribute storing the number of steps between each unfreeze, bigger value means more stable loss. """

		## Model architecture
		self.total_layers: int = 0
		""" Attribute storing the total number of layers in the model. """

	# String representation
	def __str__(self) -> str:
		return f"{self.model_name} (is_trained: {self.is_trained})"

	# Public methods
	@classmethod
	def class_routine(
		cls, dataset: Dataset, kfold: int = 0, transfer_learning: str = "imagenet", verbose: int = 0, **override_params: Any
	) -> ModelInterface:
		return cls(dataset.num_classes, kfold, transfer_learning, **override_params).routine_full(dataset, verbose)

	@measure_time(debug, "Class load (ModelInterface)")
	def class_load(self) -> None:
		""" Clear histories, and set model parameters. """
		# Initialize some attributes
		self.history.clear()
		self.evaluation_results.clear()

		# Get the total number of layers in a subprocess to avoid memory leaks with tensorflow
		with multiprocessing.Pool(1) as pool:
			self.total_layers = pool.apply(self._get_total_layers)

		# Create final model by connecting input to output layer
		self._set_parameters(self.override_params)

	@measure_time(progress)
	@handle_error(error_log=DataScienceConfig.ERROR_LOG)
	def train(self, dataset: Dataset, verbose: int = 0) -> bool:
		""" Method to train the model.

		Args:
			dataset  (Dataset):  Dataset containing the training and testing data.
			verbose  (int):      Level of verbosity, decrease by 1 for each depth
		Returns:
			bool: True if the model was trained successfully.
		Raises:
			ValueError: If the model could not be trained.
		"""
		if not self.class_train(dataset, verbose=verbose):
			raise ValueError("The model could not be trained.")
		self.is_trained = True
		return True


	@handle_error(error_log=DataScienceConfig.ERROR_LOG)
	def predict(self, X_test: Iterable[NDArray[Any]] | Dataset) -> Iterable[NDArray[Any]]:
		""" Method to predict the classes of a batch of data.

		If a Dataset is provided, the test data ungrouped array will be used:
		X_test.test_data.ungrouped_array()[0]

		Otherwise, the input is expected to be an Iterable of NDArray[Any].

		Args:
			X_test  (Iterable[NDArray[Any]] | Dataset):     Features to use for prediction.
		Returns:
			Iterable[NDArray[Any]]: Predictions of the batch.
		Raises:
			ValueError: If the model is not trained.
		"""
		if not self.is_trained:
			raise ValueError("The model must be trained before predicting.")

		# Get X_test from Dataset
		if isinstance(X_test, Dataset):
			return self.class_predict(X_test.test_data.ungrouped_array()[0])
		else:
			return self.class_predict(X_test)


	@measure_time(progress)
	@handle_error(error_log=DataScienceConfig.ERROR_LOG)
	def evaluate(self, dataset: Dataset, verbose: int = 0) -> None:
		""" Method to evaluate the model, it will log metrics and plots to mlflow along with the model.

		Args:
			dataset  (Dataset):  Dataset containing the training and testing data.
			verbose  (int):      Level of verbosity, decrease by 1 for each depth
		"""
		if not self.is_trained:
			raise ValueError("The model must be trained before evaluating.")

		# Metrics (Sensibility, Specificity, AUC, etc.)
		predictions: Iterable[NDArray[Any]] = self.predict(dataset)
		metrics: dict[str, float] = MetricUtils.metrics(dataset, predictions, self.run_name)
		mlflow.log_metrics(metrics)

		# Model specific evaluation
		self.class_evaluate(dataset, save_model=DataScienceConfig.SAVE_MODEL, verbose=verbose)


	@handle_error(error_log=DataScienceConfig.ERROR_LOG)
	@measure_time(progress)
	def routine_full(self, dataset: Dataset, verbose: int = 0) -> ModelInterface:
		""" Method to perform a full routine (load, train and predict, evaluate, and export the model).

		Args:
			dataset  (Dataset):  Dataset containing the training and testing data.
			verbose  (int):      Level of verbosity, decrease by 1 for each depth
		Returns:
			ModelInterface: The model trained and evaluated.
		"""
		# Get the transfer learning weights
		self.transfer_learning = self._get_transfer_learning_weights(dataset, verbose=verbose)

		# Perform the routine
		return self._routine(dataset, verbose=verbose)


	@handle_error(error_log=DataScienceConfig.ERROR_LOG)
	def _routine(self, dataset: Dataset, exp_name: str = "", verbose: int = 0):
		""" Sub-method used in routine_full to perform a full routine

		Args:
			dataset  (Dataset):  Dataset containing the training and testing data.
			exp_name (str):      Name of the experiment (if empty, it will be set automatically)
			verbose  (int):      Level of verbosity, decrease by 1 for each depth
		Returns:
			ModelInterface: The model trained and evaluated.
		"""
		# Init the model
		self.class_load()

		# Start mlflow run silently
		with MeasureTime(message="Experiment setup time"):
			with Muffle(mute_stderr=True):
				exp_name = dataset.get_experiment_name() if exp_name == "" else exp_name
				self.run_name = mlflow_utils.start_run(DataScienceConfig.MLFLOW_URI, exp_name, self.model_name)

		# Log the dataset used for data augmentation and parameters
		if dataset.original_dataset:
			mlflow.log_params({"data_augmentation_based_of": dataset.original_dataset.name})
		self._log_parameters()

		# Train the model
		self.train(dataset, verbose)

		# Evaluate the model
		self.evaluate(dataset, verbose)

		# End mlflow run and return the model
		with Muffle(mute_stderr=True):
			mlflow.end_run()
		return self



	# Protected methods
	def _get_transfer_learning_weights(self, dataset: Dataset, verbose: int = 0) -> str:
		""" Get the transfer learning weights for the model.

		This method handles retrieving pre-trained weights for transfer learning.
		It can:

		1. Return 'imagenet' weights for standard transfer learning
		2. Return None for no transfer learning
		3. Load weights from a previous training run on a different dataset
		4. Train a new model on a different dataset if no previous weights exist

		Returns:
			str: Path to weights file, 'imagenet', or None
		"""
		# If transfer is None or imagenet, return it
		if self.transfer_learning in ("imagenet", None):
			return self.transfer_learning

		# Else, find the weights file path
		else:
			dataset_name: str = clean_path(self.transfer_learning).split("/")[-1]
			exp_name: str = dataset.get_experiment_name(override_name=dataset_name)

			# Find a run with the same model name, and get the weights file
			with Muffle(mute_stderr=True):
				runs: list[Run] = mlflow_utils.get_runs_by_model_name(exp_name, self.model_name)

			# If no runs are found, train a new model on the dataset
			if len(runs) == 0:

				# Load dataset
				pre_dataset: Dataset = DatasetLoader.from_path(
					self.transfer_learning,
					loading_type=dataset.loading_type,
					grouping_strategy=dataset.grouping_strategy
				)
				info(f"In order to do Transfer Learning, training the model on the dataset '{pre_dataset}' first.")

				# Save current settings
				previous_transfer_learning: str = self.transfer_learning
				previous_save_model: bool = DataScienceConfig.SAVE_MODEL
				previous_kfold: int = self.kfold

				# Configure for transfer learning training
				self.transfer_learning = "imagenet"  # Start with imagenet weights
				DataScienceConfig.SAVE_MODEL = True  # Enable model saving
				self.kfold = 0         # Disable k-fold

				# Train model on transfer learning dataset
				self._routine(pre_dataset, exp_name=exp_name, verbose=verbose)

				# Restore previous settings
				self.transfer_learning = previous_transfer_learning
				DataScienceConfig.SAVE_MODEL = previous_save_model
				self.kfold = previous_kfold

				# Get the weights file path - need to refresh the experiment object
				runs: list[Run] = mlflow_utils.get_runs_by_model_name(exp_name, self.model_name)

			# If no runs are found, raise an error
			if not runs:
				raise ValueError(f"No runs found for model {self.model_name} in experiment {exp_name}")
			run: Run = runs[-1]

			# Get the last run's weights path
			# FIXME: Only works if MLFLow URI is file-tree based (not remote or sqlite), which is default
			return mlflow_utils.get_weights_path(from_string=str(run.info.artifact_uri))

	def _get_total_layers(self) -> int:
		""" Get the total number of layers in the model architecture, e.g. 427 for DenseNet121.

		Compatible with Keras/TensorFlow and PyTorch models.

		Returns:
			int: Total number of layers in the model architecture.
		"""
		architecture: Any = self._get_architectures()[1]
		total_layers: int = 0
		# Keras/TensorFlow
		if hasattr(architecture, "layers"):
			total_layers = len(architecture.layers)

		# PyTorch
		elif hasattr(architecture, "children"):
			total_layers = len(architecture.children())

		# Free memory and return the total number of layers
		del architecture
		gc.collect()
		return total_layers

	def _set_parameters(self, override: dict[str, Any] | None = None) -> None:
		""" Set some useful and common models parameters.

		Args:
			override (dict[str, Any]): Dictionary of parameters to override.
		"""
		if override is None:
			override = {}

		# Training parameters
		self.batch_size = override.get("batch_size", self.batch_size)
		self.epochs = override.get("epochs", self.epochs)

		# Callback parameters
		self.early_stop_patience = override.get("early_stop_patience", self.early_stop_patience)
		self.model_checkpoint_delay = override.get("model_checkpoint_delay", self.model_checkpoint_delay)

		# ReduceLROnPlateau parameters
		self.learning_rate = override.get("learning_rate", self.learning_rate)
		self.reduce_lr_patience = override.get("reduce_lr_patience", self.reduce_lr_patience)
		self.min_delta = override.get("min_delta", self.min_delta)
		self.min_lr = override.get("min_lr", self.min_lr)
		self.factor = override.get("factor", self.factor)

		# Warmup parameters
		self.warmup_epochs = override.get("warmup_epochs", self.warmup_epochs)
		self.initial_warmup_lr = override.get("initial_warmup_lr", self.initial_warmup_lr)

		# Fine-tune parameters
		self.unfreeze_percentage = override.get("unfreeze_percentage", self.unfreeze_percentage)
		self.fine_tune_last_layers = max(1, round(self.total_layers * self.unfreeze_percentage / 100))

		# Optimizer parameters
		self.beta_1 = override.get("beta_1", self.beta_1)
		self.beta_2 = override.get("beta_2", self.beta_2)

		# Learning Rate Finder parameters
		self.lr_finder_min_lr = override.get("lr_finder_min_lr", self.lr_finder_min_lr)
		self.lr_finder_max_lr = override.get("lr_finder_max_lr", self.lr_finder_max_lr)
		self.lr_finder_epochs = override.get("lr_finder_epochs", self.lr_finder_epochs)
		self.lr_finder_update_per_epoch = override.get("lr_finder_update_per_epoch", self.lr_finder_update_per_epoch)
		self.lr_finder_update_interval = override.get("lr_finder_update_interval", self.lr_finder_update_interval)

		# Unfreeze Percentage Finder parameters
		self.unfreeze_finder_epochs = override.get("unfreeze_finder_epochs", self.unfreeze_finder_epochs)
		self.unfreeze_finder_update_per_epoch = override.get("unfreeze_finder_update_per_epoch", self.unfreeze_finder_update_per_epoch)
		self.unfreeze_finder_update_interval = override.get("unfreeze_finder_update_interval", self.unfreeze_finder_update_interval)

		# Other parameters
		self.additional_training_data += override.get("additional_training_data", XyTuple.empty())


	def _set_class_weight(self, y_train: NDArray[Any]) -> None:
		""" Calculate class weight for balanced training.

		Args:
			y_train (NDArray[Any]): Training labels
		Returns:
			dict[int, float]: Dictionary mapping class indices to weights, e.g. {0: 0.34, 1: 0.66}
		"""
		# Get the true classes (one-hot -> class indices)
		true_classes: NDArray[Any] = Utils.convert_to_class_indices(y_train)

		# Set the class weights (balanced)
		self.class_weight = dict(enumerate(class_weight.compute_class_weight(
			class_weight="balanced",
			classes=np.unique(true_classes),
			y=true_classes
		)))

	def _log_parameters(self) -> None:
		""" Log the model parameters. """
		mlflow.log_params({
			"cfg_test_size": DataScienceConfig.TEST_SIZE,
			"cfg_validation_size": DataScienceConfig.VALIDATION_SIZE,
			"cfg_seed": DataScienceConfig.SEED,
			"cfg_save_model": DataScienceConfig.SAVE_MODEL,
			"cfg_device": DataScienceConfig.TENSORFLOW_DEVICE,

			# Base attributes
			"param_kfold": self.kfold,
			"param_transfer_learning": self.transfer_learning,

			# Training parameters
			"param_batch_size": self.batch_size,
			"param_epochs": self.epochs,

			# Fine-tuning parameters
			"param_unfreeze_percentage": self.unfreeze_percentage,
			"param_fine_tune_last_layers": self.fine_tune_last_layers,
			"param_total_layers": self.total_layers,

			# Optimizer parameters
			"param_beta_1": self.beta_1,
			"param_beta_2": self.beta_2,
			"param_learning_rate": self.learning_rate,

			# Callback parameters
			"param_early_stop_patience": self.early_stop_patience,
			"param_model_checkpoint_delay": self.model_checkpoint_delay,

			# ReduceLROnPlateau parameters
			"param_reduce_lr_patience": self.reduce_lr_patience,
			"param_min_delta": self.min_delta,
			"param_min_lr": self.min_lr,
			"param_factor": self.factor,

			# Warmup parameters
			"param_warmup_epochs": self.warmup_epochs,
			"param_initial_warmup_lr": self.initial_warmup_lr,
		})

	def _get_fold_split(self, training_data: XyTuple, kfold: int = 5) -> Generator[tuple[XyTuple, XyTuple], None, None]:
		""" Get fold split indices for cross validation.

		This method splits the training data into k folds for cross validation while preserving
		the relationship between original images and their augmented versions.

		The split is done using stratified k-fold to maintain class distribution across folds.
		For each fold, both the training and validation sets contain complete groups of original
		and augmented images.

		Args:
			training_data  (XyTuple): Dataset containing training and test data to split into folds
			kfold          (int):     Number of folds to create
		Returns:
			list[tuple[XyTuple, XyTuple]]: List of (train_data, val_data) tuples for each fold
		"""
		assert kfold not in (0, 1), "kfold must not be 0 or 1"
		yield from training_data.kfold_split(n_splits=kfold, random_state=DataScienceConfig.SEED)

	@handle_error(error_log=DataScienceConfig.ERROR_LOG)
	def _train_final_model(self, dataset: Dataset, verbose: int = 0) -> None:
		""" Train the final model on all data and return it.

		Args:
			dataset  (Dataset):  Dataset containing the training and testing data
			verbose  (int):      Level of verbosity
		"""
		# Get validation data from training data
		debug(f"Training final model on train/val split: {dataset}")

		# Verbose info message
		if verbose > 0:
			info(
				f"({self.model_name}) Training final model on full dataset with "
				f"{len(dataset.training_data.X)} samples ({len(dataset.val_data.X)} validation)"
			)

		# Put the validation data in the test data (since we don't use the test data in the train function)
		old_test_data: XyTuple = dataset.test_data
		dataset.test_data = dataset.val_data

		# Train the final model and remember it
		self.final_model = self._train_fold(dataset, fold_number=0, mlflow_prefix="history_final", verbose=verbose)

		# Restore the old test data
		dataset.test_data = old_test_data
		gc.collect()

	@measure_time(progress)
	@handle_error(error_log=DataScienceConfig.ERROR_LOG)
	def _train_each_fold(self, dataset: Dataset, verbose: int = 0) -> None:
		""" Train the model on each fold and fill self.models with the trained models.

		Args:
			dataset  (Dataset):  Dataset containing the training and testing data
			verbose  (int):      Level of verbosity
		"""
		# Get fold split
		fold_split: Generator[tuple[XyTuple, XyTuple], None, None] = self._get_fold_split(dataset.training_data, self.kfold)

		# Train on each fold
		for i, (train_data, test_data) in enumerate(fold_split):
			fold_number: int = i + 1

			# During Cross Validation, the validation data is the same as the test data.
			# Except when the validation population is 1 sample (e.g. LeaveOneOut)
			# Therefore, we need to use the original validation data for the final model
			if self.kfold < 0 or len(test_data.X) == 1:
				val_data: XyTuple = dataset.val_data
			else:
				val_data: XyTuple = test_data

			# Create a new dataset (train/val based of training data)
			new_dataset: Dataset = Dataset(
				training_data=train_data,
				val_data=val_data,
				test_data=test_data,
				name=dataset.name,
				grouping_strategy=dataset.grouping_strategy,
				labels=dataset.labels
			)

			# Log the fold
			if verbose > 0:
				# If there are multiple validation samples or no filepaths, show the number of validation samples
				if len(test_data.X) != 1 or not test_data.filepaths:
					debug(
						f"({self.model_name}) Fold {fold_number} training with "
						f"{len(train_data.X)} samples ({len(test_data.X)} validation)"
					)
				# Else, show the filepath of the single validation sample (useful for debugging)
				else:
					debug(
						f"({self.model_name}) Fold {fold_number} training with "
						f"{len(train_data.X)} samples (validation: {test_data.filepaths[0]})"
					)

			# Train the model on the fold
			handle_error(self._train_fold,
				message=f"({self.model_name}) Fold {fold_number} training failed", error_log=DataScienceConfig.ERROR_LOG
			)(
				dataset=new_dataset,
				fold_number=fold_number,
				mlflow_prefix=f"history_fold_{fold_number}",
				verbose=verbose
			)

			# Collect garbage to free up some memory
			gc.collect()

	@measure_time(progress)
	@handle_error(error_log=DataScienceConfig.ERROR_LOG)
	def class_train(self, dataset: Dataset, verbose: int = 0) -> bool:
		""" Train the model using k-fold cross validation and then full model training.

		Args:
			dataset (Dataset):  Dataset containing the training and testing data (test data will not be used in class_train)
			verbose (int):      Level of verbosity
		Returns:
			bool: True if training was successful
		"""
		# Compute the class weights
		self._set_class_weight(np.array(dataset.training_data.y))

		# Find the best learning rate
		if DataScienceConfig.DO_LEARNING_RATE_FINDER > 0:
			info(f"({self.model_name}) Finding the best learning rate...")
			found_lr: float | None = self._find_best_learning_rate(dataset, verbose)
			if DataScienceConfig.DO_LEARNING_RATE_FINDER == 2 and found_lr is not None:
				self.learning_rate = found_lr
				mlflow.log_params({"param_learning_rate": found_lr})
				info(f"({self.model_name}) Now using learning rate: {found_lr:.2e}")

		# Find the best unfreeze percentage
		if DataScienceConfig.DO_UNFREEZE_FINDER > 0:
			info(f"({self.model_name}) Finding the best unfreeze percentage...")
			found_unfreeze: float | None = self._find_best_unfreeze_percentage(dataset, verbose)
			if DataScienceConfig.DO_UNFREEZE_FINDER == 2 and found_unfreeze is not None:
				self.unfreeze_percentage = found_unfreeze
				info(f"({self.model_name}) Now using unfreeze percentage: {found_unfreeze:.2f}%")

		# If k-fold is enabled, train the model on each fold
		if self.kfold not in (0, 1):
			self._train_each_fold(dataset, verbose)

		# Train the final model on all data
		self._train_final_model(dataset, verbose)
		return True

	@handle_error(error_log=DataScienceConfig.ERROR_LOG)
	def _log_metrics(self, from_index: int = 1) -> None:
		""" Calculate (average and standard deviation) and log metrics for each evaluation result.

		Args:
			from_index (int): Index of the first evaluation result to use
		"""
		# For each metric, calculate the average and standard deviation
		for metric_name in self.evaluation_results[0].keys():

			# Get the metric values for each fold
			metric_values: list[float] = [x[metric_name] for x in self.evaluation_results[from_index:]]
			if not metric_values:
				continue

			# Log the average and standard deviation
			avg_key: str = MetricDictionnary.AVERAGE_METRIC.replace("METRIC_NAME", metric_name)
			std_key: str = MetricDictionnary.STANDARD_DEVIATION_METRIC.replace("METRIC_NAME", metric_name)
			mlflow.log_metric(avg_key, float(np.mean(metric_values)))
			mlflow.log_metric(std_key, float(np.std(metric_values)))

	@handle_error(error_log=DataScienceConfig.ERROR_LOG)
	def class_evaluate(
		self,
		dataset: Dataset,
		metrics_names: tuple[str, ...] = (),
		save_model: bool = False,
		verbose: int = 0
	) -> bool:
		""" Evaluate the model using the given predictions and labels.

		Args:
			dataset         (Dataset):   Dataset containing the training and testing data
			metrics_names   (list[str]): List of metrics to plot (default to all metrics)
			save_model      (bool):      Whether to save the best model
			verbose         (int):       Level of verbosity
		Returns:
			bool: True if evaluation was successful
		"""
		# If no metrics names are provided, use all metrics
		if not metrics_names:
			metrics_names = tuple(self.evaluation_results[0].keys())

		# Log metrics and plot curves
		MetricUtils.plot_every_metric_curves(self.history, metrics_names, self.run_name)
		self._log_metrics()

		# Save the best model if save_model is True
		if save_model:
			if verbose > 0:
				with MeasureTime(debug, "Saving best model"):
					self._log_final_model()
			else:
				self._log_final_model()

		# Success
		return True


	# Protected methods for training
	@handle_error(error_log=DataScienceConfig.ERROR_LOG)
	def _find_best_learning_rate(self, dataset: Dataset, verbose: int = 0) -> float:
		""" Find the best learning rate for the model, optionally using a subprocess.

		Args:
			dataset  (Dataset):  Dataset to use for training.
			verbose  (int):      Verbosity level (controls progress bar).
		Returns:
			float: The best learning rate found.
		"""
		if DataScienceConfig.DO_FIT_IN_SUBPROCESS:
			queue: multiprocessing.queues.Queue[dict[str, Any]] = multiprocessing.Queue()
			process: multiprocessing.Process = multiprocessing.Process(
				target=self._find_best_learning_rate_subprocess,
				kwargs={"dataset": dataset, "queue": queue, "verbose": verbose}
			)
			process.start()
			process.join()
			results: dict[str, Any] = queue.get(timeout=60)
		else:
			results: dict[str, Any] = self._find_best_learning_rate_subprocess(dataset, verbose=verbose)

		# Plot the learning rate vs loss and find the best learning rate
		return MetricUtils.find_best_x_and_plot(
			results["learning_rates"],
			results["losses"],
			smoothen=True,
			use_steep=True,
			run_name=self.run_name,
			x_label="Learning Rate",
			y_label="Loss",
			plot_title="Learning Rate Finder",
			log_x=True,
			y_limits=(0, 4.0)
		)

	@handle_error(error_log=DataScienceConfig.ERROR_LOG)
	def _find_best_unfreeze_percentage(self, dataset: Dataset, verbose: int = 0) -> float:
		""" Find the best unfreeze percentage for the model, optionally using a subprocess.

		Args:
			dataset  (Dataset):  Dataset to use for training.
			verbose  (int):      Verbosity level (controls progress bar).
		Returns:
			float: The best unfreeze percentage found.
		"""
		if DataScienceConfig.DO_FIT_IN_SUBPROCESS:
			queue: multiprocessing.queues.Queue[dict[str, Any]] = multiprocessing.Queue()
			process: multiprocessing.Process = multiprocessing.Process(
				target=self._find_best_unfreeze_percentage_subprocess,
				kwargs={"dataset": dataset, "queue": queue, "verbose": verbose}
			)
			process.start()
			process.join()
			results: dict[str, Any] = queue.get(timeout=60)
		else:
			results: dict[str, Any] = self._find_best_unfreeze_percentage_subprocess(dataset, verbose=verbose)

		# Plot the unfreeze percentage vs loss and find the best unfreeze percentage
		return MetricUtils.find_best_x_and_plot(
			results["unfreeze_percentages"],
			results["losses"],
			smoothen=True,
			use_steep=False,
			run_name=self.run_name,
			x_label="Unfreeze Percentage",
			y_label="Loss",
			plot_title="Unfreeze Percentage Finder",
			log_x=False,
			y_limits=(0, 4.0)
		)


	@measure_time(progress)
	def _train_fold(self, dataset: Dataset, fold_number: int = 0, mlflow_prefix: str = "history", verbose: int = 0) -> Any:
		""" Train model on a single fold.

		Args:
			dataset      (Dataset):  Dataset to train on
			fold_number  (int):      Fold number (0 for final model)
			prefix       (str):      Prefix for the history
			verbose      (int):      Verbosity level
		"""
		# Create the checkpoint path
		checkpoint_path: str = f"{DataScienceConfig.TEMP_FOLDER}/{self.run_name}_best_model_fold_{fold_number}.keras"

		# Prepare visualization arguments if needed
		temp_dir: TemporaryDirectory[str] | None = None
		if DataScienceConfig.DO_SALIENCY_AND_GRADCAM and dataset.test_data.n_samples == 1:
			temp_dir = TemporaryDirectory()

		# Create and run the process
		if DataScienceConfig.DO_FIT_IN_SUBPROCESS and fold_number > 0:
			queue: multiprocessing.queues.Queue[dict[str, Any]] = multiprocessing.Queue()
			process: multiprocessing.Process = multiprocessing.Process(
				target=self._train_subprocess,
				args=(dataset, checkpoint_path, temp_dir),
				kwargs={"queue": queue, "verbose": verbose}
			)
			process.start()
			process.join()
			return_values: dict[str, Any] = queue.get(timeout=60)
		else:
			return_values: dict[str, Any] = self._train_subprocess(
				dataset, checkpoint_path, temp_dir, verbose=verbose
			)
		history: dict[str, Any] = return_values["history"]
		eval_results: dict[str, Any] = return_values["eval_results"]
		predictions: NDArray[Any] = return_values["predictions"]
		true_classes: NDArray[Any] = return_values["true_classes"]
		training_predictions: NDArray[Any] = return_values.get("training_predictions", None)
		training_true_classes: NDArray[Any] = return_values.get("training_true_classes", None)

		# For each epoch, log the history
		mlflow_utils.log_history(history, prefix=mlflow_prefix)

		# Append the history and evaluation results
		self.history.append(history)
		self.evaluation_results.append(eval_results)

		# Generate and save ROC curve for this fold
		MetricUtils.roc_and_auc(
			true_classes=true_classes,
			pred_probs=predictions,
			fold_number=fold_number,
			run_name=self.run_name
		)

		# If final model, also log the ROC curve for the train set
		if fold_number == 0:
			MetricUtils.roc_and_auc(
				true_classes=training_true_classes,
				pred_probs=training_predictions,
				fold_number=-2,
				run_name=self.run_name
			)

		# Log visualization artifacts if they were generated
		if temp_dir is not None:
			mlflow.log_artifacts(temp_dir.name)
			temp_dir.cleanup()

		# Show some metrics
		if verbose > 0:
			last_history: dict[str, Any] = {k: v[-1] for k, v in history.items()}
			info(f"Training done, metrics: {last_history}")

		# Return the trained model
		return return_values.get("model", None)

