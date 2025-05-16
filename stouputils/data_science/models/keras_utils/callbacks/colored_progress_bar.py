
# pyright: reportMissingTypeStubs=false

# Imports
from typing import Any

import tensorflow as tf
from keras.callbacks import Callback
from keras.models import Model
from tqdm.auto import tqdm

from .....print import MAGENTA
from .....parallel import BAR_FORMAT

class ColoredProgressBar(Callback):
	""" Progress bar using tqdm for Keras training.

	A callback that displays a progress bar using tqdm during model training.
	Shows the training progress across steps with a customized format
	instead of the default Keras one showing multiple lines.
	"""
	def __init__(
		self,
		desc: str = "Training",
		track_epochs: bool = False,
		show_lr: bool = False,
		update_frequency: int = 1,
		color: str = MAGENTA
	) -> None:
		""" Initialize the progress bar callback.

		Args:
			desc             (str):   Custom description for the progress bar.
			track_epochs     (bool):  Whether to track epochs instead of batches.
			show_lr          (bool):  Whether to show the learning rate.
			update_frequency (int):   How often to update the progress bar (every N batches).
			color            (str):   Color of the progress bar.
		"""
		super().__init__()
		self.desc: str = desc
		""" Description of the progress bar. """
		self.track_epochs: bool = track_epochs
		""" Whether to track epochs instead of batches. """
		self.show_lr: bool = show_lr
		""" Whether to show the learning rate. """
		self.latest_val_loss: float = 0.0
		""" Latest validation loss, updated at the end of each epoch. """
		self.latest_lr: float = 0.0
		""" Latest learning rate, updated during batch and epoch processing. """
		self.batch_count: int = 0
		""" Counter to update the progress bar less frequently. """
		self.update_frequency: int = max(1, update_frequency) # Ensure frequency is at least 1
		""" How often to update the progress bar (every N batches). """
		self.color: str = color
		""" Color of the progress bar. """
		self.pbar: tqdm[Any] | None = None
		""" The tqdm progress bar instance. """
		self.epochs: int = 0
		""" Total number of epochs. """
		self.steps: int = 0
		""" Number of steps per epoch. """
		self.total: int = 0
		""" Total number of steps/epochs to track. """
		self.params: dict[str, Any]
		""" Training parameters. """
		self.model: Model

	def on_train_begin(self, logs: dict[str, Any] | None = None) -> None:
		""" Initialize the progress bar at the start of training.

		Args:
			logs (dict | None): Training logs.
		"""
		# Get training parameters
		self.epochs = self.params.get("epochs", 0)
		self.steps = self.params.get("steps", 0)

		# Determine total units and initial description
		if self.track_epochs:
			desc: str = f"{self.color}{self.desc} (Epochs)"
			self.total = self.epochs
		else:
			desc: str = f"{self.color}{self.desc} (Epoch 1/{self.epochs})"
			self.total = self.epochs * self.steps

		# Initialize tqdm bar
		self.pbar = tqdm(
			total=self.total,
			desc=desc,
			position=0,
			leave=True,
			bar_format=BAR_FORMAT,
			ascii=False
		)
		# Reset state variables
		self.latest_val_loss = 0.0
		self.latest_lr = 0.0
		self.batch_count = 0

	def on_batch_end(self, batch: int, logs: dict[str, Any] | None = None) -> None:
		""" Update the progress bar after each batch, based on update frequency.

		Args:
			batch (int): Current batch number (0-indexed).
			logs (dict | None): Dictionary of logs containing metrics for the batch.
		"""
		# Skip updates if tracking epochs, pbar isn't initialized, or steps are unknown
		if self.track_epochs or self.pbar is None or self.steps == 0:
			return

		self.batch_count += 1
		is_last_batch: bool = (batch + 1) == self.steps

		# Update only every `update_frequency` batches or on the last batch
		if self.batch_count % self.update_frequency == 0 or is_last_batch:
			increment: int = self.batch_count
			self.batch_count = 0 # Reset counter

			# Calculate current epoch (1-based) based on the progress bar's state *before* this update
			# Ensure epoch doesn't exceed total epochs in description
			current_epoch: int = min(self.epochs, self.pbar.n // self.steps + 1)
			current_step: int = batch + 1  # Convert to 1-indexed for display
			self.pbar.set_description(
				f"{self.color}{self.desc} (Epoch {current_epoch}/{self.epochs}, Step {current_step}/{self.steps})"
			)

			# Update learning rate if model and optimizer are available
			if self.model and hasattr(self.model, "optimizer"):
				self.latest_lr = float(tf.keras.backend.get_value(self.model.optimizer.learning_rate)) # type: ignore

			# Update postfix with batch loss and the latest known validation loss
			if logs and "loss" in logs:
				loss: float = logs["loss"]
				val_loss_str: str = ""
				if self.latest_val_loss != 0.0:
					if self.latest_val_loss < 1e-3:
						val_loss_str = f", val_loss: {self.latest_val_loss:.2e}"
					else:
						val_loss_str = f", val_loss: {self.latest_val_loss:.5f}"

				# Format learning rate string
				lr_str: str = ""
				if self.show_lr and self.latest_lr != 0.0:
					if self.latest_lr < 1e-3:
						lr_str = f", lr: {self.latest_lr:.2e}"
					else:
						lr_str = f", lr: {self.latest_lr:.5f}"

				if loss < 1e-3:
					self.pbar.set_postfix_str(f"loss: {loss:.2e}{val_loss_str}{lr_str}", refresh=False)
				else:
					self.pbar.set_postfix_str(f"loss: {loss:.5f}{val_loss_str}{lr_str}", refresh=False)

			# Update progress bar position, ensuring not to exceed total
			actual_increment: int = min(increment, self.total - self.pbar.n)
			if actual_increment > 0:
				self.pbar.update(actual_increment)

	def on_epoch_end(self, epoch: int, logs: dict[str, Any] | None = None) -> None:
		""" Update metrics and progress bar position at the end of each epoch.

		Args:
			epoch (int): Current epoch number (0-indexed).
			logs (dict | None): Dictionary of logs containing metrics for the epoch.
		"""
		if self.pbar is None:
			return

		# Update the latest validation loss from epoch logs
		if logs:
			current_val_loss: float = logs.get("val_loss", 0.0)
			if current_val_loss != 0.0:
				self.latest_val_loss = current_val_loss

			# Update learning rate if model and optimizer are available
			if self.model and hasattr(self.model, "optimizer"):
				self.latest_lr = float(tf.keras.backend.get_value(self.model.optimizer.learning_rate)) # type: ignore

			# Update postfix string with final epoch metrics
			loss: float = logs.get("loss", 0.0)
			val_loss_str: str = f", val_loss: {self.latest_val_loss:.5f}" if self.latest_val_loss != 0.0 else ""

			# Format learning rate string
			lr_str: str = ""
			if self.show_lr and self.latest_lr != 0.0:
				if self.latest_lr < 1e-3:
					lr_str = f", lr: {self.latest_lr:.2e}"
				else:
					lr_str = f", lr: {self.latest_lr:.5f}"

			if loss != 0.0: # Only update if loss is available
				self.pbar.set_postfix_str(f"loss: {loss:.5f}{val_loss_str}{lr_str}", refresh=True)

		# Update progress bar position
		if self.track_epochs:
			# Increment by 1 epoch if not already at total
			if self.pbar.n < self.total:
				self.pbar.update(1)
		else:
			# Ensure the progress bar is exactly at the end of the current epoch
			expected_position: int = min(self.total, (epoch + 1) * self.steps)
			increment: int = expected_position - self.pbar.n
			if increment > 0:
				self.pbar.update(increment)

	def on_train_end(self, logs: dict[str, Any] | None = None) -> None:
		""" Close the progress bar when training is complete.

		Args:
			logs (dict | None): Training logs.
		"""
		if self.pbar is not None:
			# Ensure the bar reaches 100%
			increment: int = self.total - self.pbar.n
			if increment > 0:
				self.pbar.update(increment)
			self.pbar.close()
			self.pbar = None # Reset pbar instance

