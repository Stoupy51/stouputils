"""
This module contains the Utils class, which provides static methods for common operations.

This class contains static methods for:

- Converting between one-hot encoding and class indices
"""

# Imports
from typing import Any
import numpy as np

from .config.get import DataScienceConfig as cfg
from ..decorators import handle_error
from numpy.typing import NDArray

# Class
class Utils:
	""" Utility class providing common operations. """

	@staticmethod
	@handle_error(error_log=cfg.ERROR_LOG)
	def convert_to_class_indices(y: NDArray[Any] | list[NDArray[Any]]) -> NDArray[Any]:
		""" Convert array from one-hot encoded format to class indices.
		If the input is already class indices, it returns the same array.

		Args:
			y (NDArray[Any] | list[NDArray[Any]]): Input array (either one-hot encoded or class indices)
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
	@handle_error(error_log=cfg.ERROR_LOG)
	def convert_to_one_hot(y: NDArray[Any] | list[NDArray[Any]], num_classes: int) -> NDArray[Any]:
		""" Convert array from class indices to one-hot encoded format.
		If the input is already one-hot encoded, it returns the same array.

		Args:
			y				(NDArray[Any] | list[NDArray[Any]]):	Input array (either class indices or one-hot encoded)
			num_classes		(int):								Total number of classes
		Returns:
			NDArray[Any]:		One-hot encoded array: [2, 0] -> [[0, 0, 1, 0], [1, 0, 0, 0]]

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
				one_hot[np.arange(n_samples), y.astype(int)] = 1.0
			return one_hot
		return y

