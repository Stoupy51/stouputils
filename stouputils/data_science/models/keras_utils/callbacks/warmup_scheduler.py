
# pyright: reportMissingTypeStubs=false

# Imports
from typing import Any

import tensorflow as tf
from keras.callbacks import Callback
from keras.models import Model


class WarmupScheduler(Callback):
	""" Keras Callback for learning rate warmup.

	Sources:
	- Accurate, Large Minibatch SGD: Training ImageNet in 1 Hour: https://arxiv.org/abs/1706.02677
	- Attention Is All You Need: https://arxiv.org/abs/1706.03762

	This callback implements a learning rate warmup strategy where the learning rate
	gradually increases from an initial value to a target value over a specified
	number of epochs. This helps stabilize training in the early stages.

	The learning rate increases linearly from the initial value to the target value
	over the warmup period, and then remains at the target value.
	"""

	def __init__(self, warmup_epochs: int, initial_lr: float, target_lr: float) -> None:
		""" Initialize the warmup scheduler.

		Args:
			warmup_epochs  (int):    Number of epochs for warmup.
			initial_lr     (float):  Starting learning rate for warmup.
			target_lr      (float):  Target learning rate after warmup.
		"""
		super().__init__()
		self.warmup_epochs: int = warmup_epochs
		""" Number of epochs for warmup. """
		self.initial_lr: float = initial_lr
		""" Starting learning rate for warmup. """
		self.target_lr: float = target_lr
		""" Target learning rate after warmup. """
		self.model: Model
		""" Model to apply the warmup scheduler to. """

		# Pre-compute learning rates for each epoch to avoid calculations during training
		self.epoch_learning_rates: list[float] = []
		for epoch in range(warmup_epochs + 1):
			if epoch < warmup_epochs:
				lr = initial_lr + (target_lr - initial_lr) * (epoch + 1) / warmup_epochs
			else:
				lr = target_lr
			self.epoch_learning_rates.append(lr)

	def on_epoch_begin(self, epoch: int, logs: dict[str, Any] | None = None) -> None:
		""" Adjust learning rate at the beginning of each epoch during warmup.

		Args:
			epoch (int): Current epoch index.
			logs (dict | None): Training logs.
		"""
		if self.warmup_epochs <= 0 or epoch > self.warmup_epochs:
			return

		# Use pre-computed learning rate to avoid calculations during training
		tf.keras.backend.set_value(self.model.optimizer.learning_rate, self.epoch_learning_rates[epoch]) # type: ignore

