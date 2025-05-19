"""
This module contains the Dataset class, which provides an easy way to handle ML datasets.

The Dataset class has the following attributes:

- training_data        (XyTuple):              Training data containing features, labels and file paths
- test_data            (XyTuple):              Test data containing features, labels and file paths
- num_classes          (int):                  Number of classes in the dataset
- name                 (str):                  Name of the dataset
- grouping_strategy    (GroupingStrategy):     Strategy for grouping images when loading
- labels               (list[str]):            List of class labels (strings)
- loading_type         (Literal["image"]):     Type of the dataset (currently only "image" is supported)
- original_dataset     (Dataset | None):       Original dataset used for data augmentation
- class_distribution   (dict[str, dict]):      Class distribution counts for train/test sets

It provides methods for:

- Loading image datasets from directories using different grouping strategies
- Splitting data into train/test sets with stratification (and care for data augmentation)
- Managing class distributions and dataset metadata
"""
# pyright: reportUnknownMemberType=false

# Imports
from __future__ import annotations

import os
from collections.abc import Generator, Iterable
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray

from ...decorators import handle_error, LogLevels
from ...print import warning, progress
from ...collections import unique_list
from ..utils import Utils
from .grouping_strategy import GroupingStrategy
from .xy_tuple import XyTuple

# Constants
DEFAULT_IMAGE_KWARGS: dict[str, Any] = {
	"image_size": (224, 224),
	"label_mode": "categorical",
	"color_mode": "rgb",
	"batch_size": 1
}
""" Default image kwargs sent to keras.image_dataset_from_directory """

# Dataset class
class Dataset:
	""" Dataset class used for easy data handling. """

	# Class constructors
	def __init__(
		self,
		training_data: XyTuple | list[Any],
		val_data: XyTuple | list[Any] | None = None,
		test_data: XyTuple | list[Any] | None = None,
		name: str = "",
		grouping_strategy: GroupingStrategy = GroupingStrategy.NONE,
		labels: tuple[str, ...] = (),
		loading_type: Literal["image"] = "image"
	) -> None:
		""" Initialize the dataset class

		>>> Dataset(training_data=tuple(), test_data=tuple(), name="doctest")
		Traceback (most recent call last):
			...
		AssertionError: data must be a tuple with X and y as iterables
		"""
		if val_data is None:
			val_data = XyTuple.empty()
		if test_data is None:
			test_data = XyTuple.empty()

		# Assertions
		all_data: tuple[Any, ...] = (training_data, val_data, test_data)
		for data in all_data:
			if not isinstance(data, XyTuple):
				assert isinstance(data, Iterable) \
					and 2 <= len(data) <= 3 \
					and isinstance(data[0], Iterable) \
					and isinstance(data[1], Iterable), "data must be a tuple with X and y as iterables"

		# Get training, validation and test data
		xy_tuples: list[XyTuple] = [XyTuple(*data) if not isinstance(data, XyTuple) else data for data in all_data]

		# Pre-process for attributes initialization
		num_classes: int = self._get_num_classes(xy_tuples[0].y, xy_tuples[1].y, xy_tuples[2].y)
		labels = tuple(str(x).replace("_", " ").title() for x in (labels if labels else range(num_classes)))

		# Initialize attributes
		self._training_data: XyTuple = xy_tuples[0]
		""" Training data as XyTuple containing X and y as numpy arrays.
		This is a protected attribute accessed via the public property self.training_data. """
		self._val_data: XyTuple = xy_tuples[1]
		""" Validation data as XyTuple containing X and y as numpy arrays.
		This is a protected attribute accessed via the public property self.val_data. """
		self._test_data: XyTuple = xy_tuples[2]
		""" Test data as XyTuple containing X and y as numpy arrays.
		This is a protected attribute accessed via the public property self.test_data. """
		self.num_classes: int = num_classes
		""" Number of classes in the dataset (y) """
		self.name: str = os.path.basename(name)
		""" Name of the dataset (path given in the constructor are converted,
		ex: ".../data/pizza_not_pizza" becomes "pizza_not_pizza") """
		self.loading_type: Literal["image"] = loading_type
		""" Type of the dataset """
		self.grouping_strategy: GroupingStrategy = grouping_strategy
		""" Grouping strategy for the dataset """
		self.labels: tuple[str, ...] = labels
		""" List of class labels (strings) """
		self.class_distribution: dict[str, dict[int, int]] = {"train": {}, "val": {}, "test": {}}
		""" Class distribution in the dataset for both training and test sets """
		self.original_dataset: Dataset | None = None
		""" Original dataset used for data augmentation (can be None) """

		# Update class distribution
		self._update_class_distribution()

	def _get_num_classes(self, *values: Any) -> int:
		""" Get the number of classes in the dataset.

		Args:
			values (NDArray[Any]): Arrays containing class labels
		Returns:
			int: Number of unique classes
		"""
		# Handle case where arrays have different dimensions (1D vs 2D)
		processed_values: list[NDArray[Any]] = []
		for value in values:
			value: NDArray[Any] = np.array(value)
			if len(value.shape) == 2:  # One-hot encoded
				processed_values.append(Utils.convert_to_class_indices(value))
			else:
				processed_values.append(value)

		return len(np.unique(np.concatenate(processed_values)))

	def _update_class_distribution(self, update_num_classes: bool = False) -> None:
		""" Update the class distribution dictionary for both training and test data. """
		# For each data type,
		for data_type, data in (("train", self._training_data), ("val", self._val_data), ("test", self._test_data)):
			y_data: NDArray[Any] = np.array(data.y)
			if len(y_data.shape) == 2:  # One-hot encoded
				y_data = Utils.convert_to_class_indices(y_data)

			# Update the class distribution
			self.class_distribution[data_type] = {}
			for class_id in range(self.num_classes):
				self.class_distribution[data_type][class_id] = np.sum(y_data == class_id)

		# Update the number of classes if needed
		if update_num_classes:
			self.num_classes = self._get_num_classes(self._training_data.y, self._val_data.y, self._test_data.y)

	def exclude_augmented_images_from_val_test(self, original_dataset: Dataset) -> None:
		""" Exclude augmented versions of validation and test images from the training set.

		This ensures that augmented versions of images in the validation and test sets are not present in the training set,
		which would cause data leakage.

		Args:
			original_dataset (Dataset): The original dataset containing the test images to exclude
		"""
		# Get base filenames from original test set
		progress("Excluding augmented versions of validation and test images from training set...")
		val_test_base_names: list[list[str]] = [
			[os.path.splitext(os.path.basename(f))[0] for f in filepaths]
			for filepaths in (*original_dataset.val_data.filepaths, *original_dataset.test_data.filepaths)
		]
		val_test_base_names = unique_list(val_test_base_names, method="str")

		# Get base filenames from training set
		train_base_names: list[list[str]] = [
			[os.path.splitext(os.path.basename(f))[0] for f in filepaths]
			for filepaths in self.training_data.filepaths
		]

		# Remove augmented versions of test images from training set
		# Get indices of training samples that are not augmented versions of test samples
		# For each training sample, check if any of its filenames start with any test filename
		train_indices: list[int] = [
			i for i, train_names in enumerate(train_base_names)
			if not any(
				any(train_name.startswith(name) for train_name in train_names)
				for names in val_test_base_names
				for name in names
			)
		]

		# Update training data to exclude augmented versions
		self._training_data = XyTuple(
			[self.training_data.X[i] for i in train_indices],
			[self.training_data.y[i] for i in train_indices],
			tuple(self.training_data.filepaths[i] for i in train_indices)
		)

		# Use original test data
		self._test_data = original_dataset.test_data     # Impossible to have augmented test_data here
		self._val_data = original_dataset.val_data       # Impossible to have augmented val_data here
		self._update_class_distribution(update_num_classes=False)

	@property
	def training_data(self) -> XyTuple:
		return self._training_data

	@training_data.setter
	def training_data(self, value: XyTuple | Any) -> None:
		warning("Setting training data...", value)
		self._training_data = XyTuple(*value) if not isinstance(value, XyTuple) else value
		self._update_class_distribution(update_num_classes=True)

	@property
	def val_data(self) -> XyTuple:
		return self._val_data

	@val_data.setter
	def val_data(self, value: XyTuple | Any) -> None:
		self._val_data = XyTuple(*value) if not isinstance(value, XyTuple) else value
		self._update_class_distribution(update_num_classes=True)

	@property
	def test_data(self) -> XyTuple:
		return self._test_data

	@test_data.setter
	def test_data(self, value: XyTuple | Any) -> None:
		self._test_data = XyTuple(*value) if not isinstance(value, XyTuple) else value
		self._update_class_distribution(update_num_classes=True)

	# Class methods
	def __str__(self) -> str:
		train_dist: dict[int, int] = self.class_distribution["train"]
		val_dist: dict[int, int] = self.class_distribution["val"]
		test_dist: dict[int, int] = self.class_distribution["test"]
		return (
			f"Dataset {self.name}: "
			f"{len(self.training_data.X):,} training samples, "
			f"{len(self.val_data.X):,} validation samples, "
			f"{len(self.test_data.X):,} test samples, "
			f"{self.num_classes:,} classes "
			f"(train: {train_dist}, val: {val_dist}, test: {test_dist})"
		)

	def __repr__(self) -> str:
		return (
			f"Dataset(training_data={self.training_data!r}, "
			f"val_data={self.val_data!r}, "
			f"test_data={self.test_data!r}, "
			f"num_classes={self.num_classes}, "
			f"name={self.name!r}, "
			f"grouping_strategy={self.grouping_strategy.name})"
		)

	def __iter__(self) -> Generator[XyTuple, Any, Any]:
		""" Allow unpacking of the dataset into train and test sets.

		Returns:
			Generator[XyTuple], Any, Any]: Generator over the dataset splits

		>>> X, y = [[1]], [2]
		>>> dataset = Dataset(training_data=(X, y), test_data=(X, y), name="doctest")
		>>> train, val, test = dataset
		>>> train == (X, y) and val == () and test == (X, y)
		True
		>>> train == XyTuple(X, y) and val == XyTuple.empty() and test == XyTuple(X, y)
		True
		"""
		yield from (self.training_data, self.val_data, self.test_data)

	def get_experiment_name(self, override_name: str = "") -> str:
		""" Get the experiment name for mlflow, e.g. "DatasetName_GroupingStrategyName"

		Args:
			override_name (str): Override the Dataset name
		Returns:
			str: Experiment name
		"""
		if override_name:
			return f"{override_name}_{self.grouping_strategy.name.title()}"
		else:
			return f"{self.name}_{self.grouping_strategy.name.title()}"


	# Static methods
	@staticmethod
	@handle_error(error_log=LogLevels.ERROR_TRACEBACK)
	def empty() -> Dataset:
		return Dataset(XyTuple.empty(), name="empty", grouping_strategy=GroupingStrategy.NONE)

