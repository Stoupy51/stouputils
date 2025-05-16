
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportMissingTypeStubs=false
# pyright: reportAssignmentType=false

# Imports
import tensorflow as tf
from keras.losses import Loss


class NextGenerationLoss(Loss):
	""" Next Generation Loss with alpha = 2.4092.

	Sources:
	- Code: https://github.com/ZKI-PH-ImageAnalysis/Next-Generation-Loss/blob/main/NGL_torch.py
	- Next Generation Loss Function for Image Classification: https://arxiv.org/pdf/2404.12948
	"""

	def __init__(self, alpha: float = 2.4092, name: str = "ngl_loss"):
		""" Initialize the Next Generation Loss.

		Args:
			alpha    (float):  The alpha parameter.
			name     (str):    The name of the loss function.
		"""
		super().__init__(name=name)
		self.name: str = name
		""" The name of the loss function. """
		self.alpha: float = alpha
		""" The alpha parameter. """

	def call(self, y_true: tf.Tensor, y_pred: tf.Tensor) -> tf.Tensor:
		""" Compute the NGL loss.

		Args:
			y_true (tf.Tensor): The true labels.
			y_pred (tf.Tensor): The predicted labels.
		Returns:
			tf.Tensor: The computed NGL loss.
		"""
		# Cast to float32
		y_pred = tf.cast(y_pred, tf.float32)
		y_true = tf.cast(y_true, tf.float32)

		# Apply softmax to predictions
		y_pred = tf.nn.softmax(y_pred, axis=-1)

		# Compute the NGL loss using the alpha parameter (default 2.4092)
		loss: tf.Tensor = tf.reduce_mean(
			tf.math.exp(self.alpha - y_pred - y_pred * y_true) -
			tf.math.cos(tf.math.cos(tf.math.sin(y_pred)))
		)
		return loss

