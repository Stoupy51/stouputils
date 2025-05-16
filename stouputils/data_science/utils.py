"""
This module contains the Utils class, which provides static methods for common operations.

This class contains static methods for:

- Safe division (with 0 as denominator or None)
- Safe multiplication (with None)
- Converting between one-hot encoding and class indices
- Calculating ROC curves and AUC scores
"""
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false

# Imports
from typing import Any

import numpy as np
from numpy.typing import NDArray
from ..decorators import handle_error
from ..ctx import Muffle

from .config.get import DataScienceConfig


# Class
class Utils:
	""" Utility class providing common operations. """

	@staticmethod
	def safe_divide_float(a: float, b: float) -> float:
		""" Safe division of two numbers, return 0 if denominator is 0.

		Args:
			a  (float):  First number
			b  (float):  Second number
		Returns:
			float: Result of the division

		Examples:
			>>> Utils.safe_divide_float(10, 2)
			5.0
			>>> Utils.safe_divide_float(0, 5)
			0.0
			>>> Utils.safe_divide_float(10, 0)
			0
			>>> Utils.safe_divide_float(-10, 2)
			-5.0
		"""
		return a / b if b > 0 else 0

	@staticmethod
	def safe_divide_none(a: float | None, b: float | None) -> float | None:
		""" Safe division of two numbers, return None if either number is None or denominator is 0.

		Args:
			a  (float | None):  First number
			b  (float | None):  Second number
		Returns:
			float | None: Result of the division or None if denominator is None

		Examples:
			>>> None == Utils.safe_divide_none(None, 2)
			True
			>>> None == Utils.safe_divide_none(10, None)
			True
			>>> None == Utils.safe_divide_none(10, 0)
			True
			>>> Utils.safe_divide_none(10, 2)
			5.0
		"""
		return a / b if a is not None and b is not None and b > 0 else None

	@staticmethod
	def safe_multiply_none(a: float | None, b: float | None) -> float | None:
		""" Safe multiplication of two numbers, return None if either number is None.

		Args:
			a  (float | None):  First number
			b  (float | None):  Second number
		Returns:
			float | None: Result of the multiplication or None if either number is None

		Examples:
			>>> None == Utils.safe_multiply_none(None, 2)
			True
			>>> None == Utils.safe_multiply_none(10, None)
			True
			>>> Utils.safe_multiply_none(10, 2)
			20
			>>> Utils.safe_multiply_none(-10, 2)
			-20
		"""
		return a * b if a is not None and b is not None else None

	@staticmethod
	@handle_error(error_log=DataScienceConfig.ERROR_LOG)
	def convert_to_class_indices(y: NDArray[np.intc | np.single] | list[NDArray[np.intc | np.single]]) -> NDArray[Any]:
		""" Convert array from one-hot encoded format to class indices.
		If the input is already class indices, it returns the same array.

		Args:
			y (NDArray[intc | single] | list[NDArray[intc | single]]): Input array (either one-hot encoded or class indices)
		Returns:
			NDArray[Any]: Array of class indices: [[0, 0, 1, 0], [1, 0, 0, 0]] -> [2, 0]

		Examples:
			>>> Utils.convert_to_class_indices(np.array([[0, 0, 1, 0], [1, 0, 0, 0]])).tolist()
			[2, 0]
			>>> Utils.convert_to_class_indices(np.array([2, 0, 1])).tolist()
			[2, 0, 1]
			>>> Utils.convert_to_class_indices(np.array([[1], [0]])).tolist()
			[[1], [0]]
			>>> Utils.convert_to_class_indices(np.array([])).tolist()
			[]
		"""
		y = np.array(y)
		if y.ndim > 1 and y.shape[1] > 1:
			return np.argmax(y, axis=1)
		return y

	@staticmethod
	@handle_error(error_log=DataScienceConfig.ERROR_LOG)
	def convert_to_one_hot(
		y: NDArray[np.intc | np.single] | list[NDArray[np.intc | np.single]], num_classes: int
	) -> NDArray[Any]:
		""" Convert array from class indices to one-hot encoded format.
		If the input is already one-hot encoded, it returns the same array.

		Args:
			y            (NDArray[intc|single] | list[NDArray[intc|single]]):  Input array (either class indices or one-hot encoded)
			num_classes  (int):                                                Total number of classes
		Returns:
			NDArray[Any]:	One-hot encoded array: [2, 0] -> [[0, 0, 1, 0], [1, 0, 0, 0]]

		Examples:
			>>> Utils.convert_to_one_hot(np.array([2, 0]), 4).tolist()
			[[0.0, 0.0, 1.0, 0.0], [1.0, 0.0, 0.0, 0.0]]
			>>> Utils.convert_to_one_hot(np.array([[0, 0, 1, 0], [1, 0, 0, 0]]), 4).tolist()
			[[0, 0, 1, 0], [1, 0, 0, 0]]
			>>> Utils.convert_to_one_hot(np.array([0, 1, 2]), 3).shape
			(3, 3)
			>>> Utils.convert_to_one_hot(np.array([]), 3)
			array([], shape=(0, 3), dtype=float32)

			>>> array = np.array([[0.1, 0.9], [0.2, 0.8]])
			>>> array = Utils.convert_to_class_indices(array)
			>>> array = Utils.convert_to_one_hot(array, 2)
			>>> array.tolist()
			[[0.0, 1.0], [0.0, 1.0]]
		"""
		y = np.array(y)
		if y.ndim == 1 or y.shape[1] != num_classes:

			# Get the number of samples and create a one-hot encoded array
			n_samples: int = len(y)
			one_hot: NDArray[np.float32] = np.zeros((n_samples, num_classes), dtype=np.float32)
			if n_samples > 0:
				# Create a one-hot encoding by setting specific positions to 1.0:
				# - np.arange(n_samples) creates an array [0, 1, 2, ..., n_samples-1] for row indices
				# - y.astype(int) contains the class indices that determine which column gets the 1.0
				# - Together they form coordinate pairs (row_idx, class_idx) where we set values to 1.0
				row_indices: NDArray[np.intc] = np.arange(n_samples)
				one_hot[row_indices, y.astype(int)] = 1.0
			return one_hot
		return y

	@staticmethod
	@handle_error(error_log=DataScienceConfig.ERROR_LOG)
	def get_roc_curve_and_auc(
		y_true: NDArray[np.intc | np.single],
		y_pred: NDArray[np.single]
	) -> tuple[float, NDArray[np.single], NDArray[np.single], NDArray[np.single]]:
		""" Calculate ROC curve and AUC score.

		Args:
			y_true  (NDArray[intc | single]):   True class labels (either one-hot encoded or class indices)
			y_pred  (NDArray[single]):           Predicted probabilities (must be probability scores, not class indices)
		Returns:
			tuple[float, NDArray[np.single], NDArray[np.single], NDArray[np.single]]:
				Tuple containing AUC score, False Positive Rate, True Positive Rate, and Thresholds

		Examples:
			>>> # Binary classification example
			>>> y_true = np.array([0.0, 1.0, 0.0, 1.0, 0.0])
			>>> y_pred = np.array([[0.2, 0.8], [0.1, 0.9], [0.8, 0.2], [0.2, 0.8], [0.7, 0.3]])
			>>> auc_value, fpr, tpr, thresholds = Utils.get_roc_curve_and_auc(y_true, y_pred)
			>>> round(auc_value, 2)
			0.92
			>>> [round(x, 2) for x in fpr.tolist()]
			[0.0, 0.0, 0.33, 0.67, 1.0]
			>>> [round(x, 2) for x in tpr.tolist()]
			[0.0, 0.5, 1.0, 1.0, 1.0]
			>>> [round(x, 2) for x in thresholds.tolist()]
			[inf, 0.9, 0.8, 0.3, 0.2]
		"""
		# For predictions, assert they are probabilities (one-hot encoded)
		assert y_pred.ndim > 1 and y_pred.shape[1] > 1, "Predictions must be probability scores in one-hot format"
		pred_probs: NDArray[np.single] = y_pred[:, 1]  # Take probability of positive class only

		# Convert true labels to class indices if they're one-hot encoded
		true_classes: NDArray[np.intc] = Utils.convert_to_class_indices(y_true)

		# Calculate ROC curve and AUC score using probabilities
		with Muffle(mute_stderr=True):	# Suppress "UndefinedMetricWarning: No positive samples in y_true [...]"

			# Import functions
			try:
				from sklearn.metrics import auc, roc_curve
			except ImportError as e:
				raise ImportError("scikit-learn is required for ROC curve calculation. Install with 'pip install scikit-learn'") from e

			results: tuple[Any, Any, Any] = roc_curve(true_classes, pred_probs, drop_intermediate=False)
			fpr: NDArray[np.single] = results[0]
			tpr: NDArray[np.single] = results[1]
			thresholds: NDArray[np.single] = results[2]
			auc_value: float = float(auc(fpr, tpr))
		return auc_value, fpr, tpr, thresholds

