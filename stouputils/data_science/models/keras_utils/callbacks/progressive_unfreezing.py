
# pyright: reportMissingTypeStubs=false

# Imports
from collections.abc import Callable
from typing import Any

from keras.callbacks import Callback
from keras.models import Model
from keras.optimizers import Optimizer


class ProgressiveUnfreezing(Callback):
	""" Callback inspired by the Learning Rate Finder to progressively unfreeze model layers during training.

	Warning: This callback is not compatible with model.fit() as it modifies the trainable state of the model.
	Prefer doing your own training loop instead.

	This callback can operate in two modes:
	1. Start with all layers frozen and incrementally unfreeze them from 0% to 100% (progressive_freeze=False)
	2. Start with all layers unfrozen and incrementally freeze them from 100% to 0% (progressive_freeze=True)
	"""

	def __init__(
		self,
		base_model: Model,
		steps_per_epoch: int,
		epochs: int,
		reset_weights: bool = False,
		reset_optimizer_function: Callable[[], Optimizer] | None = None,
		update_per_epoch: bool = True,
		update_interval: int = 5,
		progressive_freeze: bool = False
	) -> None:
		""" Initialize the progressive unfreezing callback.

		Args:
			base_model         (Model):   Base model to unfreeze.
			steps_per_epoch    (int):     Number of steps per epoch.
			epochs             (int):     Total number of epochs.
			reset_weights      (bool):    If True, reset weights after each unfreeze.
			reset_optimizer_function (Callable | None):
				If set, use this function to reset the optimizer every update_interval.
				The function should return a compiled optimizer, e.g. `lambda: model._get_optimizer(AdamW(...))`.
			update_per_epoch   (bool):    If True, unfreeze per epoch, else per batch.
			update_interval    (int):     Number of steps between each unfreeze to allow model to stabilize.
			progressive_freeze (bool):    If True, start with all layers unfrozen and progressively freeze them.
		"""
		super().__init__()
		self.base_model: Model = base_model
		""" Base model to unfreeze. """
		self.model: Model
		""" Model to apply the progressive unfreezing to. """
		self.steps_per_epoch: int = int(steps_per_epoch)
		""" Number of steps per epoch. """
		self.epochs: int = int(epochs)
		""" Total number of epochs. """
		self.reset_weights: bool = bool(reset_weights)
		""" If True, reset weights after each unfreeze. """
		self.reset_optimizer_function: Callable[[], Optimizer] | None = reset_optimizer_function
		""" If reset_weights is True and this is not None, use this function to get a new optimizer. """
		self.update_per_epoch: bool = bool(update_per_epoch)
		""" If True, unfreeze per epoch, else per batch. """
		self.update_interval: int = max(1, int(update_interval))
		""" Number of steps between each unfreeze to allow model to stabilize. """
		self.progressive_freeze: bool = bool(progressive_freeze)
		""" If True, start with all layers unfrozen and progressively freeze them. """

		# If updating per epoch, remove to self.epochs the update interval to allow the last step to train with 100% unfreeze
		if self.update_per_epoch:
			self.epochs -= self.update_interval

		# Calculate total steps considering the update interval
		total_steps_raw: int = self.epochs if self.update_per_epoch else self.steps_per_epoch * self.epochs
		self.total_steps: int = total_steps_raw // self.update_interval
		""" Total number of update steps (considering update_interval). """

		self.fraction_unfrozen: list[float] = []
		""" Fraction of layers unfrozen. """
		self.losses: list[float] = []
		""" Losses. """
		self._all_layers: list[Any] = []
		""" All layers. """
		self._initial_trainable: list[bool] = []
		""" Initial trainable states. """
		self._initial_weights: list[Any] | None = None
		""" Initial weights of the model. """
		self._last_update_step: int = -1
		""" Last step when layers were unfrozen. """
		self.params: dict[str, Any]

	def on_train_begin(self, logs: dict[str, Any] | None = None) -> None:
		""" Set initial layer trainable states at the start of training and store initial states and weights.

		Args:
			logs (dict | None): Training logs.
		"""
		# Collect all layers from the model and preserve their original trainable states for potential restoration
		self._all_layers = self.base_model.layers
		self._initial_trainable = [bool(layer.trainable) for layer in self._all_layers]

		# Store initial weights to reset after each unfreeze
		if self.reset_weights:
			self._initial_weights = self.model.get_weights()

		# Set initial trainable state based on mode
		for layer in self._all_layers:
			layer.trainable = self.progressive_freeze  # If progressive_freeze, start with all layers unfrozen

	def _update_layers(self, step: int) -> None:
		""" Update layer trainable states based on the current step and mode.
		Reset weights after each update to prevent bias in the results.

		Args:
			step (int): Current training step.
		"""
		# Calculate the effective step considering the update interval
		effective_step: int = step // self.update_interval

		# Skip if we haven't reached the next update interval
		if effective_step <= self._last_update_step:
			return
		self._last_update_step = effective_step

		# Calculate the number of layers to unfreeze based on current effective step
		n_layers: int = len(self._all_layers)

		if self.progressive_freeze:
			# For progressive freezing, start at 1.0 (all unfrozen) and decrease to 0.0
			fraction: float = max(0.0, 1.0 - (effective_step + 1) / self.total_steps)
		else:
			# For progressive unfreezing, start at 0.0 (all frozen) and increase to 1.0
			fraction: float = min(1.0, (effective_step + 1) / self.total_steps)

		n_unfreeze: int = int(n_layers * fraction)  # Number of layers to keep unfrozen
		self.fraction_unfrozen.append(fraction)

		# Set trainable state for each layer based on position
		# For both modes, we unfreeze from the top (output layers) to the bottom (input layers)
		for i, layer in enumerate(self._all_layers):
			layer.trainable = i >= (n_layers - n_unfreeze)

		# Reset weights to initial state to prevent bias and reset optimizer
		if self._initial_weights is not None:
			self.model.set_weights(self._initial_weights) # pyright: ignore [reportUnknownMemberType]
		if self.reset_optimizer_function is not None:
			self.model.optimizer = self.reset_optimizer_function()
			self.model.optimizer.build(self.model.trainable_variables) # pyright: ignore [reportUnknownMemberType]

	def _track_loss(self, logs: dict[str, Any] | None = None) -> None:
		""" Track the current loss.

		Args:
			logs (dict | None): Training logs containing loss information.
		"""
		if logs and "loss" in logs:
			self.losses.append(logs["loss"])

	def on_batch_begin(self, batch: int, logs: dict[str, Any] | None = None) -> None:
		""" Update layer trainable states at the start of each batch if not updating per epoch.

		Args:
			batch (int): Current batch index.
			logs (dict | None): Training logs.
		"""
		# Skip if we're updating per epoch instead of per batch
		if self.update_per_epoch:
			return

		# Calculate the current step across all epochs and update layers
		step: int = self.params.get("steps", self.steps_per_epoch) * self.params.get("epoch", 0) + batch
		self._update_layers(step)

	def on_batch_end(self, batch: int, logs: dict[str, Any] | None = None) -> None:
		""" Track loss at the end of each batch if not updating per epoch.

		Args:
			batch (int): Current batch index.
			logs (dict | None): Training logs.
		"""
		# Skip if we're updating per epoch instead of per batch
		if self.update_per_epoch:
			return

		# Record the loss if update interval is reached
		if batch % self.update_interval == 0:
			self._track_loss(logs)

	def on_epoch_begin(self, epoch: int, logs: dict[str, Any] | None = None) -> None:
		""" Update layer trainable states at the start of each epoch if updating per epoch.

		Args:
			epoch (int): Current epoch index.
			logs (dict | None): Training logs.
		"""
		# Skip if we're updating per batch instead of per epoch
		if not self.update_per_epoch:
			return

		# Update layers based on current epoch
		self._update_layers(epoch)

	def on_epoch_end(self, epoch: int, logs: dict[str, Any] | None = None) -> None:
		""" Track loss at the end of each epoch if updating per epoch.

		Args:
			epoch (int): Current epoch index.
			logs (dict | None): Training logs.
		"""
		# Skip if we're updating per batch instead of per epoch
		if not self.update_per_epoch:
			return

		# Record the loss if update interval is reached
		if epoch % self.update_interval == 0:
			self._track_loss(logs)

	def on_train_end(self, logs: dict[str, Any] | None = None) -> None:
		""" Restore original trainable states at the end of training.

		Args:
			logs (dict | None): Training logs.
		"""
		# Restore each layer's original trainable state
		for layer, trainable in zip(self._all_layers, self._initial_trainable, strict=False):
			layer.trainable = trainable

	def get_results(self, multiply_by_100: bool = True) -> tuple[list[float], list[float]]:
		""" Get the results of the progressive unfreezing from 0% to 100% even if progressive_freeze is True.

		Args:
			multiply_by_100 (bool): If True, multiply the fractions by 100 to get percentages.

		Returns:
			tuple[list[float], list[float]]: fractions of layers unfrozen, and losses.
		"""
		fractions: list[float] = self.fraction_unfrozen

		# Reverse the order if progressive_freeze is True
		if self.progressive_freeze:
			fractions = fractions[::-1]

		# Multiply by 100 if requested
		if multiply_by_100:
			fractions = [x * 100 for x in fractions]

		# Return the results
		return fractions, self.losses

