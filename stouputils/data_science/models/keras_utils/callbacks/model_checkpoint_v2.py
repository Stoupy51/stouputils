
# pyright: reportMissingTypeStubs=false
# pyright: reportUnknownMemberType=false

# Imports
from typing import Any

from keras.callbacks import ModelCheckpoint


class ModelCheckpointV2(ModelCheckpoint):
	""" Model checkpoint callback but only starts after a given number of epochs.

	Args:
		epochs_before_start (int): Number of epochs before starting the checkpointing
	"""

	def __init__(self, epochs_before_start: int = 3, *args: Any, **kwargs: Any) -> None:
		super().__init__(*args, **kwargs)
		self.epochs_before_start = epochs_before_start
		self.current_epoch = 0

	def on_batch_end(self, batch: int, logs: dict[str, Any] | None = None) -> None:
		if self.current_epoch >= self.epochs_before_start:
			super().on_batch_end(batch, logs)

	def on_epoch_end(self, epoch: int, logs: dict[str, Any] | None = None) -> None:
		self.current_epoch = epoch
		if epoch >= self.epochs_before_start:
			super().on_epoch_end(epoch, logs)

