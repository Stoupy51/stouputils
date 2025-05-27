""" Keras-specific model implementation with TensorFlow integration.
Provides concrete implementations for Keras model operations.

Features:

- Transfer learning layer freezing/unfreezing
- Keras-specific callbacks (early stopping, LR reduction)
- Model checkpointing/weight management
- GPU-optimized prediction pipelines
- Keras metric/loss configuration
- Model serialization/deserialization

Implements ModelInterface for Keras-based models.
"""
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportArgumentType=false
# pyright: reportCallIssue=false
# pyright: reportMissingTypeStubs=false
# pyright: reportOptionalMemberAccess=false
# pyright: reportOptionalCall=false

# Imports
import gc
import multiprocessing
import multiprocessing.queues
import os
from collections.abc import Iterable
from tempfile import TemporaryDirectory
from typing import Any

import mlflow
import mlflow.keras
import numpy as np
import tensorflow as tf
from keras.backend import clear_session
from keras.callbacks import Callback, CallbackList, EarlyStopping, History, ReduceLROnPlateau, TensorBoard
from keras.layers import Dense, GlobalAveragePooling2D
from keras.losses import CategoricalCrossentropy, CategoricalFocalCrossentropy, Loss
from keras.metrics import AUC, CategoricalAccuracy, F1Score, Metric
from keras.models import Model, Sequential
from keras.optimizers import Adam, AdamW, Lion, Optimizer
from keras.utils import set_random_seed
from numpy.typing import NDArray

from ...decorators import measure_time
from ...print import info, warning, debug, progress
from ...parallel import colored_for_loop
from ...ctx import Muffle
from .. import mlflow_utils
from ..config.get import DataScienceConfig
from ..dataset import Dataset, GroupingStrategy
from ..utils import Utils
from .keras_utils.callbacks import ColoredProgressBar, LearningRateFinder, ModelCheckpointV2, ProgressiveUnfreezing, WarmupScheduler
from .keras_utils.losses import NextGenerationLoss
from .keras_utils.visualizations import all_visualizations_for_image
from .model_interface import ModelInterface


class BaseKeras(ModelInterface):
	""" Base class for Keras models with common functionality. """

	def class_load(self) -> None:
		""" Clear the session and collect garbage, reset random seeds and call the parent class method. """
		super().class_load()
		clear_session()
		gc.collect()
		set_random_seed(DataScienceConfig.SEED)
		self.final_model: Model

	def _fit(
		self,
		model: Model,
		x: Any,
		y: Any | None = None,
		validation_data: tuple[Any, Any] | None = None,
		shuffle: bool = True,
		batch_size: int | None = None,
		epochs: int = 1,
		callbacks: list[Callback] | None = None,
		class_weight: dict[int, float] | None = None,
		verbose: int = 0,
		*args: Any,
		**kwargs: Any
	) -> History:
		""" Manually fit the model with a custom training loop instead of using model.fit().

		This method implements a custom training loop for more control over the training process.
		It's useful for implementing custom training behaviors that aren't easily done with model.fit()
		such as unfreezing layers during training, resetting the optimizer, etc.

		Args:
			model             (Model):                   The model to train
			x                 (Any):                     Training data inputs
			y                 (Any | None):              Training data targets
			validation_data   (tuple[Any, Any] | None):  Validation data as a tuple of (inputs, targets)
			shuffle           (bool):                    Whether to shuffle the training data every epoch
			batch_size        (int | None):              Number of samples per gradient update.
			epochs            (int):                     Number of epochs to train the model.
			callbacks         (list[Callback] | None):   List of callbacks to apply during training.
			class_weight      (dict[int, float] | None): Optional dictionary mapping class indices to weights.
			verbose           (int):                     Verbosity mode.

		Returns:
			History: Training history
		"""
		# Set TensorFlow to use the XLA compiler
		tf.config.optimizer.set_jit(True)

		# Build training dataset
		if y is None and isinstance(x, tf.data.Dataset):
			train_dataset: tf.data.Dataset = x
		else:
			train_dataset: tf.data.Dataset = tf.data.Dataset.from_tensor_slices((x, y) if y is not None else x)

		# Optimize dataset pipeline
		if shuffle:
			buffer_size: int = len(x) if hasattr(x, '__len__') else 10000
			buffer_size = min(buffer_size, 50000)
			train_dataset = train_dataset.shuffle(buffer_size=buffer_size, reshuffle_each_iteration=True)
		if batch_size is not None:
			train_dataset = train_dataset.batch(batch_size)
		train_dataset = train_dataset.prefetch(tf.data.AUTOTUNE)

		# Handle validation data
		val_dataset: tf.data.Dataset | None = None
		if validation_data is not None:
			x_val, y_val = validation_data
			val_dataset = tf.data.Dataset.from_tensor_slices((x_val, y_val))
			if batch_size is not None:
				val_dataset = val_dataset.batch(batch_size)
			val_dataset = val_dataset.cache().prefetch(tf.data.AUTOTUNE)

		# Handle callbacks
		callback_list: CallbackList = CallbackList(
			callbacks,
			add_history=True,
			add_progbar=verbose != 0,
			model=model,
			verbose=verbose,
			epochs=epochs,
			steps=tf.data.experimental.cardinality(train_dataset).numpy(),
		)

		# Precompute class weights tensor outside the training loop
		class_weight_tensor: NDArray[Any] | None = None
		if class_weight:
			class_weight_values: list[float] = [float(class_weight.get(i, 1.0)) for i in range(self.num_classes)]
			class_weight_tensor = tf.constant(class_weight_values, dtype=tf.float32)

		# Precompute the gather weights function outside the training loop
		@tf.function(jit_compile=True, experimental_relax_shapes=True)
		def gather_weights(label_indices: tf.Tensor) -> tf.Tensor | None:
			if class_weight_tensor is not None:
				return tf.gather(class_weight_tensor, label_indices)
			return None

		# Get optimizer (will use loss scaling automatically under mixed-precision)
		is_ls: bool = isinstance(model.optimizer, tf.keras.mixed_precision.LossScaleOptimizer)

		# Training step with proper loss scaling
		@tf.function(jit_compile=True, experimental_relax_shapes=True)
		def train_step(xb: tf.Tensor, yb: tf.Tensor, training: bool = True) -> dict[str, Any]:
			""" Execute a single training step with gradient calculation and optimization.

			Args:
				xb (tf.Tensor): Input batch data
				yb (tf.Tensor): Target batch data

			Returns:
				dict[str, Any]: The metrics for the training step
			"""
			labels = tf.cast(tf.argmax(yb, axis=1), tf.int32)
			sw = gather_weights(labels)
			with tf.GradientTape(watch_accessed_variables=training) as tape:
				preds = model(xb, training=training)
				loss = model.compiled_loss(yb, preds, sample_weight=sw)
				loss = tf.reduce_mean(loss)

				# Scale loss if using LossScaleOptimizer
				if is_ls:
					loss = model.optimizer.get_scaled_loss(loss)

			# Backpropagate the loss
			if training:
				model.optimizer.minimize(loss, model.trainable_weights, tape=tape)

			# Update the metrics
			model.compiled_metrics.update_state(yb, preds, sample_weight=sw)
			return model.get_metrics_result()

		# Start callbacks
		logs: dict[str, Any] = {"loss": 0.0}
		callback_list.on_train_begin()

		# Custom training loop
		for epoch in range(epochs):

			# Callbacks and reset metrics
			callback_list.on_epoch_begin(epoch)
			model.compiled_metrics.reset_state()
			model.compiled_loss.reset_state()

			# Train on all batches
			for step, (x_batch, y_batch) in enumerate(train_dataset):
				callback_list.on_batch_begin(step)
				logs.update(train_step(x_batch, y_batch, training=True))
				callback_list.on_batch_end(step, logs)

			# Compute metrics for validation
			if val_dataset is not None:
				model.compiled_metrics.reset_state()
				model.compiled_loss.reset_state()

				# Run through all validation data
				for x_val, y_val in val_dataset:
					train_step(x_val, y_val, training=False)

				# Prefix "val_" to the metrics
				for key, value in model.get_metrics_result().items():
					logs[f"val_{key}"] = value

			callback_list.on_epoch_end(epoch, logs)
		callback_list.on_train_end(logs)

		# Return history
		return model.history # pyright: ignore [reportReturnType]


	def _get_architectures(
		self, optimizer: Any = None, loss: Any = None, metrics: list[Any] | None = None
	) -> tuple[Model, Model]:
		""" Get the model architecture and compile it if enough information is provided.

		This method builds and returns the model architecture.
		If optimizer, loss, and (optionally) metrics are provided, the model will be compiled.

		Args:
			optimizer (Any): The optimizer to use for training
			loss (Any): The loss function to use for training
			metrics (list[Any] | None): The metrics to use for evaluation
		Returns:
			tuple[Model, Model]: The final model and the base model
		"""

		# Get the base model (use imagenet anyway)
		base_model: Model = self._get_base_model()

		# Add a top layer since the base model doesn't have one
		output_layer: Model = Sequential([
			GlobalAveragePooling2D(),
			Dense(self.num_classes, activation="softmax")
		])(base_model.output)
		final_model: Model = Model(inputs=base_model.input, outputs=output_layer)

		# If no optimizer is provided, return the uncompiled models
		if optimizer is None:
			return final_model, base_model

		# Load transfer learning weights if provided
		if os.path.exists(self.transfer_learning):
			try:
				final_model.load_weights(self.transfer_learning)
				info(f"Transfer learning weights loaded from '{self.transfer_learning}'")
			except Exception as e:
				warning(f"Error loading transfer learning weights from '{self.transfer_learning}': {e}")

		# Freeze the base model except for the last layers (if unfreeze percentage is less than 100%)
		if self.unfreeze_percentage < 100.0:
			base_model.trainable = False
			last_layers: list[Model] = base_model.layers[-self.fine_tune_last_layers:]
			for layer in last_layers:
				layer.trainable = True
			info(
				f"Fine-tune from layer {max(0, len(base_model.layers) - self.fine_tune_last_layers)} "
				f"to {len(base_model.layers)} ({self.fine_tune_last_layers} layers)"
			)

		# Add XLA specific optimizations for compilation
		compile_options = {}
		if hasattr(tf.config.optimizer, "get_jit") and tf.config.optimizer.get_jit():
			compile_options["steps_per_execution"] = 10  # Batch multiple steps for XLA

		# Compile the model and return it
		final_model.compile(
			optimizer=optimizer,
			loss=loss,
			metrics=metrics if metrics is not None else [],
			jit_compile=True,
			**compile_options
		)
		return final_model, base_model


	# Protected methods for training
	def _get_callbacks(self) -> list[Callback]:
		""" Get the callbacks for training. """
		callbacks: list[Callback] = []

		# Add warmup scheduler if enabled
		if self.warmup_epochs > 0:
			warmup_scheduler: WarmupScheduler = WarmupScheduler(
				warmup_epochs=self.warmup_epochs,
				initial_lr=self.initial_warmup_lr,
				target_lr=self.learning_rate
			)
			callbacks.append(warmup_scheduler)

		# Add ReduceLROnPlateau
		callbacks.append(ReduceLROnPlateau(
			monitor="val_loss",
			mode="min",
			factor=self.factor,
			patience=self.reduce_lr_patience,
			min_delta=self.min_delta,
			min_lr=self.min_lr
		))

		# Add TensorBoard for profiling
		log_dir: str = f"{DataScienceConfig.TENSORBOARD_FOLDER}/{self.run_name}"
		os.makedirs(log_dir, exist_ok=True)
		callbacks.append(TensorBoard(
			log_dir=log_dir,
			histogram_freq=1,  # Log histogram visualizations every epoch
			profile_batch=(10, 20)  # Profile batches 10-20
		))

		# Add EarlyStopping to prevent overfitting
		callbacks.append(EarlyStopping(
			monitor="val_loss",
			mode="min",
			patience=self.early_stop_patience,
			verbose=0
		))
		return callbacks

	def _get_metrics(self) -> list[Metric]:
		""" Get the metrics for training.

		Returns:
			list: List of metrics to track during training including accuracy, AUC, etc.
		"""
		# Fix the F1Score dtype if mixed precision is enabled
		f1score_dtype: tf.DType = tf.float16 if DataScienceConfig.MIXED_PRECISION_POLICY == "mixed_float16" else tf.float32
		f1score: F1Score = F1Score(name="f1_score", average="macro", dtype=f1score_dtype)
		f1score.beta = tf.constant(1.0, dtype=f1score_dtype) # pyright: ignore [reportAttributeAccessIssue]

		return [
			CategoricalAccuracy(name="categorical_accuracy"),
			AUC(name="auc"),
			f1score,
		]

	def _get_optimizer(self, learning_rate: float = 0.0, mode: int = 1) -> Optimizer:
		""" Get the optimizer for training.

		Args:
			learning_rate  (float):  Learning rate
			mode           (int):    Mode to use
		Returns:
			Optimizer: Optimizer
		"""
		lr: float = self.learning_rate if learning_rate == 0.0 else learning_rate
		if mode == 0:
			return Adam(lr, self.beta_1, self.beta_2)
		elif mode == 1:
			return AdamW(lr, self.beta_1, self.beta_2)
		else:
			return Lion(lr)

	def _get_loss(self, mode: int = 0) -> Loss:
		""" Get the loss function for training depending on the mode.

		- 0: CategoricalCrossentropy (default)
		- 1: CategoricalFocalCrossentropy
		- 2: Next Generation Loss (with alpha = 2.4092)

		Args:
			mode (int): Mode to use
		Returns:
			Loss: Loss function
		"""
		if mode == 0:
			return CategoricalCrossentropy(name="categorical_crossentropy")
		elif mode == 1:
			return CategoricalFocalCrossentropy(name="categorical_focal_crossentropy")
		elif mode == 2:
			return NextGenerationLoss(name="ngl_loss")
		else:
			raise ValueError(f"Invalid mode: {mode}")

	def _find_best_learning_rate_subprocess(
		self, dataset: Dataset, queue: multiprocessing.queues.Queue | None = None, verbose: int = 0 # type: ignore
	) -> dict[str, Any] | None:
		""" Helper to run learning rate finder, potentially in a subprocess.

		Args:
			dataset         (Dataset):                         Dataset to use for training.
			queue           (multiprocessing.Queue | None):    Queue to put results in (if running in subprocess).
			verbose         (int):                             Verbosity level.

		Returns:
			dict[str, Any] | None: Return values
		"""
		X_train, y_train, _ = (dataset.training_data + self.additional_training_data).ungrouped_array()

		# Set random seeds for reproducibility within the process/subprocess
		set_random_seed(DataScienceConfig.SEED)

		# Create LR finder callback
		lr_finder: LearningRateFinder = LearningRateFinder(
			min_lr=self.lr_finder_min_lr,
			max_lr=self.lr_finder_max_lr,
			steps_per_epoch=np.ceil(len(X_train) / self.batch_size),
			epochs=self.lr_finder_epochs,
			update_per_epoch=self.lr_finder_update_per_epoch,
			update_interval=self.lr_finder_update_interval
		)

		# Get compiled model with the optimizer and loss
		final_model, _ = self._get_architectures(self._get_optimizer(), self._get_loss())

		# Create callbacks
		callbacks: list[Callback] = [lr_finder]
		if verbose > 0:
			callbacks.append(ColoredProgressBar("LR Finder", show_lr=True))

		# Run a mini training to find the best learning rate
		self._fit(
			final_model,
			X_train, y_train,
			batch_size=self.batch_size,
			epochs=self.lr_finder_epochs,
			callbacks=callbacks,
			class_weight=self.class_weight,
			verbose=0
		)

		# Prepare results
		results: dict[str, Any] = {
			"learning_rates": lr_finder.learning_rates,
			"losses": lr_finder.losses
		}

		# Return values if no queue, otherwise put them in the queue
		if queue is None:
			return results
		else:
			return queue.put(results)

	def _find_best_unfreeze_percentage_subprocess(
		self, dataset: Dataset, queue: multiprocessing.queues.Queue | None = None, verbose: int = 0 # type: ignore
	) -> dict[str, Any] | None:
		""" Helper to run unfreeze percentage finder, potentially in a subprocess.

		Args:
			dataset         (Dataset):                         Dataset to use for training.
			queue           (multiprocessing.Queue | None):    Queue to put results in (if running in subprocess).
			verbose         (int):                             Verbosity level.

		Returns:
			dict[str, Any] | None: Return values
		"""
		X_train, y_train, _ = (dataset.training_data + self.additional_training_data).ungrouped_array()

		# Set random seeds for reproducibility within the process/subprocess
		set_random_seed(DataScienceConfig.SEED)

		# Get compiled model with the optimizer and loss
		lr: float = self.learning_rate
		optimizer = self._get_optimizer(lr)
		loss_fn = self._get_loss()
		final_model, base_model = self._get_architectures(optimizer, loss_fn)

		# Function to get compiled optimizer
		def get_compiled_optimizer() -> Optimizer:
			optimizer: Optimizer = self._get_optimizer(lr)
			return final_model._get_optimizer(optimizer) # pyright: ignore [reportPrivateUsage]

		# Create unfreeze finder callback
		unfreeze_finder: ProgressiveUnfreezing = ProgressiveUnfreezing(
			base_model=base_model,
			steps_per_epoch=np.ceil(len(X_train) / self.batch_size),
			epochs=self.unfreeze_finder_epochs,
			reset_weights=True,
			reset_optimizer_function=get_compiled_optimizer,
			update_per_epoch=self.unfreeze_finder_update_per_epoch,
			update_interval=self.unfreeze_finder_update_interval,
			progressive_freeze=True		# Start from 100% unfrozen to 0% unfrozen to prevent biases
		)

		# Create callbacks
		callbacks: list[Callback] = [unfreeze_finder]
		if verbose > 0:
			callbacks.append(ColoredProgressBar("Unfreeze Finder"))

		self._fit(
			final_model,
			X_train, y_train,
			batch_size=self.batch_size,
			epochs=self.unfreeze_finder_epochs,
			callbacks=callbacks,
			class_weight=self.class_weight,
			verbose=0
		)

		# Prepare results
		unfreeze_percentages, losses = unfreeze_finder.get_results()
		results: dict[str, Any] = {
			"unfreeze_percentages": unfreeze_percentages,
			"losses": losses
		}

		# Return values if no queue, otherwise put them in the queue
		if queue is None:
			return results
		else:
			return queue.put(results)

	def _train_subprocess(
		self,
		dataset: Dataset,
		checkpoint_path: str,
		temp_dir: TemporaryDirectory[str] | None = None,
		queue: multiprocessing.queues.Queue | None = None, # type: ignore
		verbose: int = 0
	) -> dict[str, Any] | None:
		""" Train the model in a subprocess.

		The reason for this is that when training too much models on the same process,
		your process may be killed by the OS since it used too much resources over time.
		So we train each model in a separate process to avoid this issue.

		Args:
			model            (Model):                           Model to train
			dataset          (Dataset):                         Dataset to train on
			checkpoint_path  (str):                             Path to save the best model checkpoint
			temp_dir         (TemporaryDirectory[str] | None):  Temporary directory to save the visualizations
			queue            (multiprocessing.Queue | None):    Queue to put the history in
			verbose          (int):                             Verbosity level
		Returns:
			dict[str, Any]: Return values
		"""
		to_return: dict[str, Any] = {}
		set_random_seed(DataScienceConfig.SEED)

		# Extract the training and validation data
		X_train, y_train, _ = (dataset.training_data + self.additional_training_data).ungrouped_array()
		X_val, y_val, _ = dataset.val_data.ungrouped_array()
		X_test, y_test, test_filepaths = dataset.test_data.ungrouped_array()
		true_classes: NDArray[Any] = Utils.convert_to_class_indices(y_val)

		# Create the checkpoint callback
		os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
		model_checkpoint: ModelCheckpointV2 = ModelCheckpointV2(
			epochs_before_start=self.model_checkpoint_delay,
			filepath=checkpoint_path,
			monitor="val_loss",
			mode="min",
			save_best_only=True,
			save_weights_only=True,
			verbose=0
		)

		# Get the compiled model
		model, _ = self._get_architectures(self._get_optimizer(), self._get_loss(), self._get_metrics())

		# Create the callbacks, add the progress bar if verbose is 1
		callbacks = [model_checkpoint, *self._get_callbacks()]
		if verbose > 0:
			callbacks.append(ColoredProgressBar("Training", show_lr=True))

		# Train the model
		history: History = self._fit(
			model,
			X_train, y_train,
			validation_data=(X_val, y_val),
			batch_size=self.batch_size,
			epochs=self.epochs,
			callbacks=callbacks,
			class_weight=self.class_weight,
			verbose=0
		)

		# Load the best model from the checkpoint file and remove it
		debug(f"Loading best model from '{checkpoint_path}'")
		model.load_weights(checkpoint_path)
		os.remove(checkpoint_path)
		debug(f"Best model loaded from '{checkpoint_path}', deleting it...")

		# Evaluate the model
		to_return["history"] = history.history
		to_return["eval_results"] = model.evaluate(X_test, y_test, return_dict=True, verbose=0)
		to_return["predictions"] = model.predict(X_test, verbose=0)
		to_return["true_classes"] = true_classes
		to_return["training_predictions"] = model.predict(X_train, verbose=0)
		to_return["training_true_classes"] = Utils.convert_to_class_indices(y_train)

		# --- Visualization Generation (Using viz_kwargs) ---
		if temp_dir is not None:

			# Ensure fold_number > 0 for LOO visualization
			test_images: list[NDArray[Any]] = list(X_test)

			# Prepare the arguments for the visualizations
			viz_args_list: list[tuple[NDArray[Any], Any, tuple[str, ...], str]] = [
				(test_images[i], true_classes[i], test_filepaths[i], "test_folds")
				for i in range(len(test_images))
			]

			# Generate visualizations in the provided temporary directory
			for img_viz, label_idx, files, data_type in viz_args_list:
				# Extract the base name of the file/group
				if dataset.grouping_strategy == GroupingStrategy.NONE:
					base_name: str = os.path.splitext(os.path.basename(files[0]))[0]
				else:
					base_name: str = os.path.basename(os.path.dirname(files[0]))

				# Generate all visualizations for the image
				all_visualizations_for_image(
					model=model, # Use the trained model from this subprocess
					folder_path=temp_dir.name,
					img=img_viz,
					base_name=base_name,
					class_idx=label_idx,
					class_name=dataset.labels[label_idx],
					files=files,
					data_type=data_type,
				)

		# Return values if no queue, otherwise put them in the queue
		if queue is None:
			to_return["model"] = model	# Add the trained model to the return values if not in a subprocess
			return to_return
		else:
			return queue.put(to_return)


	# Predict method
	def class_predict(self, X_test: Iterable[NDArray[Any]] | tf.data.Dataset) -> Iterable[NDArray[Any]]:
		""" Predict the class for the given input data.

		Args:
			X_test  (Iterable[NDArray[Any]]):  List of inputs to predict (e.g. a batch of images)
		Returns:
			Iterable[NDArray[Any]]: A batch of predictions (model.predict())
		"""
		# Create a tf.data.Dataset to avoid retracing
		if isinstance(X_test, tf.data.Dataset):
			dataset: tf.data.Dataset = X_test
			was_dataset: bool = True
		else:
			dataset: tf.data.Dataset = tf.data.Dataset.from_tensor_slices(X_test).batch(32).prefetch(tf.data.AUTOTUNE)
			was_dataset: bool = False

		# Create an optimized prediction function
		@tf.function(jit_compile=True)
		def optimized_predict(x_batch: tf.Tensor) -> tf.Tensor:
			return self.final_model(x_batch, training=False)

		# For each model, predict the class
		model_preds: list[NDArray[Any]] = []
		for batch in dataset:
			pred: tf.Tensor = optimized_predict(batch)
			model_preds.append(pred.numpy())

		# Clear RAM
		if not was_dataset:
			del dataset
		gc.collect()

		# Return the predictions
		return np.concatenate(model_preds) if model_preds else np.array([])


	# Protected methods for evaluation
	@measure_time(progress)
	def _log_final_model(self) -> None:
		""" Log the best model (and its weights). """
		with Muffle(mute_stderr=True):
			mlflow.keras.log_model(self.final_model, "best_model") # pyright: ignore [reportPrivateImportUsage]
		mlflow.set_tag(key="has_saved_model", value="True")

		# Get the weights path and create the directory if it doesn't exist
		weights_path: str = mlflow_utils.get_weights_path()
		os.makedirs(os.path.dirname(weights_path), exist_ok=True)

		# Save the best model's weights without the last layer
		self.final_model.save_weights(weights_path)


	def class_evaluate(
		self, dataset: Dataset, metrics_names: tuple[str, ...] = (), save_model: bool = False, verbose: int = 0
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
		# First perform standard evaluation from parent class
		result: bool = super().class_evaluate(dataset, metrics_names, save_model, verbose)
		if not DataScienceConfig.DO_SALIENCY_AND_GRADCAM:
			return result

		# Get test and train data
		X_test, y_test, test_filepaths = dataset.test_data.ungrouped_array()
		test_images: list[NDArray[Any]] = list(X_test)
		test_labels: list[int] = Utils.convert_to_class_indices(y_test).tolist()

		X_train, y_train, train_filepaths = dataset.training_data.remove_augmented_files().ungrouped_array()
		train_images: list[NDArray[Any]] = list(X_train)
		train_labels: list[int] = Utils.convert_to_class_indices(y_train).tolist()

		# Process test images
		test_args_list: list[tuple[NDArray[Any], int, tuple[str, ...], str]] = [
			(test_images[i], test_labels[i], test_filepaths[i], "test")
			for i in range(min(20, len(test_images)))
		]

		# Process train images
		train_args_list: list[tuple[NDArray[Any], int, tuple[str, ...], str]] = [
			(train_images[i], train_labels[i], train_filepaths[i], "train")
			for i in range(min(10, len(train_images)))
		]

		# Combine both lists
		all_args_list = test_args_list + train_args_list

		# Create the description
		desc: str = ""
		if verbose > 0:
			desc = f"Generating visualizations for {len(test_args_list)} test and {len(train_args_list)} train images"

		# For each image, generate all visualizations, then log them to MLFlow
		with TemporaryDirectory() as temp_dir:
			for img, label, files, data_type in colored_for_loop(all_args_list, desc=desc):

				# Extract the base name of the file
				if dataset.grouping_strategy == GroupingStrategy.NONE:
					base_name: str = os.path.splitext(os.path.basename(files[0]))[0]
				else:
					base_name: str = os.path.basename(os.path.dirname(files[0]))

				# Generate all visualizations for the image
				all_visualizations_for_image(
					model=self.final_model,
					folder_path=temp_dir,
					img=img,
					base_name=base_name,
					class_idx=label,
					class_name=dataset.labels[label],
					files=files,
					data_type=data_type,
				)

			# Log the visualizations
			mlflow.log_artifacts(temp_dir)

		return result

