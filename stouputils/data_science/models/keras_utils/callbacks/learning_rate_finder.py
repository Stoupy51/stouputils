
# pyright: reportMissingTypeStubs=false

# Imports
from typing import Any

import tensorflow as tf
from keras.callbacks import Callback
from keras.models import Model


class LearningRateFinder(Callback):
	""" Callback to find optimal learning rate by increasing LR during training.

	Sources:
	- Inspired by: https://github.com/WittmannF/LRFinder
	- Cyclical Learning Rates for Training Neural Networks: https://arxiv.org/abs/1506.01186 (first description of the method)

	This callback gradually increases the learning rate from a minimum to a maximum value
	during training, allowing you to identify the optimal learning rate range for your model.

	It works by:

	1. Starting with a very small learning rate
	2. Exponentially increasing it after each batch or epoch
	3. Recording the loss at each learning rate
	4. Restoring the model's initial weights after training

	The optimal learning rate is typically found where the loss is decreasing most rapidly
	before it starts to diverge.

	.. image:: https://blog.dataiku.com/hubfs/training%20loss.png
		:alt: Learning rate finder curve example
	"""

	def __init__(
		self,
		min_lr: float,
		max_lr: float,
		steps_per_epoch: int,
		epochs: int,
		update_per_epoch: bool = False,
		update_interval: int = 5
	) -> None:
		""" Initialize the learning rate finder.

		Args:
			min_lr           (float): Minimum learning rate
			max_lr           (float): Maximum learning rate
			steps_per_epoch  (int):   Steps per epoch
			epochs           (int):   Number of epochs
			update_per_epoch (bool):  If True, update LR once per epoch instead of every batch.
			update_interval  (int):   Number of steps between each lr increase, bigger value means more stable loss.
		"""
		super().__init__()
		self.min_lr: float = min_lr
		""" Minimum learning rate. """
		self.max_lr: float = max_lr
		""" Maximum learning rate. """
		self.total_updates: int = (epochs if update_per_epoch else steps_per_epoch * epochs) // update_interval
		""" Total number of update steps (considering update_interval). """
		self.update_per_epoch: bool = update_per_epoch
		""" Whether to update learning rate per epoch instead of per batch. """
		self.update_interval: int = max(1, int(update_interval))
		""" Number of steps between each lr increase, bigger value means more stable loss. """
		self.lr_mult: float = (max_lr / min_lr) ** (1 / self.total_updates)
		""" Learning rate multiplier. """
		self.learning_rates: list[float] = []
		""" List of learning rates. """
		self.losses: list[float] = []
		""" List of losses. """
		self.best_lr: float = min_lr
		""" Best learning rate. """
		self.best_loss: float = float("inf")
		""" Best loss. """
		self.model: Model
		""" Model to apply the learning rate finder to. """
		self.initial_weights: list[Any] | None = None
		""" Stores the initial weights of the model. """

	def on_train_begin(self, logs: dict[str, Any] | None = None) -> None:
		""" Set initial learning rate and save initial model weights at the start of training.

		Args:
			logs (dict | None): Training logs.
		"""
		self.initial_weights = self.model.get_weights()
		tf.keras.backend.set_value(self.model.optimizer.learning_rate, self.min_lr) # type: ignore

	def _update_lr_and_track_metrics(self, logs: dict[str, Any] | None = None) -> None:
		""" Update learning rate and track metrics.

		Args:
			logs (dict | None): Logs from training
		"""
		if logs is None:
			return

		# Get current learning rate and loss
		current_lr: float = float(tf.keras.backend.get_value(self.model.optimizer.learning_rate)) # type: ignore
		current_loss: float = logs["loss"]

		# Record values
		self.learning_rates.append(current_lr)
		self.losses.append(current_loss)

		# Track best values
		if current_loss < self.best_loss:
			self.best_loss = current_loss
			self.best_lr = current_lr

		# Update learning rate
		new_lr: float = current_lr * self.lr_mult
		tf.keras.backend.set_value(self.model.optimizer.learning_rate, new_lr) # type: ignore

	def on_batch_end(self, batch: int, logs: dict[str, Any] | None = None) -> None:
		""" Record loss and increase learning rate after each batch if not updating per epoch.

		Args:
			batch (int): Current batch index.
			logs (dict | None): Training logs.
		"""
		if self.update_per_epoch:
			return
		if batch % self.update_interval == 0:
			self._update_lr_and_track_metrics(logs)

	def on_epoch_end(self, epoch: int, logs: dict[str, Any] | None = None) -> None:
		""" Record loss and increase learning rate after each epoch if updating per epoch.

		Args:
			epoch (int): Current epoch index.
			logs (dict | None): Training logs.
		"""
		if not self.update_per_epoch:
			return
		if epoch % self.update_interval == 0:
			self._update_lr_and_track_metrics(logs)

	def on_train_end(self, logs: dict[str, Any] | None = None) -> None:
		""" Restore initial model weights at the end of training.

		Args:
			logs (dict | None): Training logs.
		"""
		if self.initial_weights is not None:
			self.model.set_weights(self.initial_weights) # pyright: ignore [reportUnknownMemberType]

