"""
This module contains the DatasetLoader class which handles dataset loading operations.

The DatasetLoader class provides the following key features:

- Loading image datasets from directories using keras.image_dataset_from_directory
- Handling different grouping strategies (when having multiple images per subject)
- Preventing data leakage between train/test sets when using data augmentation
- Ensuring test data consistency when loading an augmented dataset
"""

# Imports
from typing import Any, Literal

import numpy as np

from ...decorators import handle_error, LogLevels
from ..config.get import DataScienceConfig
from .dataset import Dataset
from .grouping_strategy import GroupingStrategy
from .xy_tuple import XyTuple

# Constants
DEFAULT_IMAGE_KWARGS: dict[str, Any] = {
    "image_size": (224, 224),
    "color_mode": "RGB",
}

class DatasetLoader:
	""" Handles dataset loading operations """

	@staticmethod
	@handle_error(error_log=LogLevels.ERROR_TRACEBACK)
	def from_path(
		path: str,
		loading_type: Literal["image"] = "image",
		seed: int = DataScienceConfig.SEED,
		test_size: float = 0.2,
		val_size: float = 0.2,
		grouping_strategy: GroupingStrategy = GroupingStrategy.NONE,
		based_of: str = "",
		**kwargs: Any
	) -> Dataset:
		""" Create a balanced dataset from a path.

		Args:
			path              (str):               Path to the dataset
			loading_type      (Literal["image"]):  Type of the dataset
			seed              (int):               Seed for the random generator
			test_size         (float):             Size of the test dataset (0 means no test set)
			val_size          (float):             Size of the validation dataset (0 means no validation set)
			grouping_strategy (GroupingStrategy):  Grouping strategy for the dataset (ex: GroupingStrategy.CONCATENATE)
			based_of          (str):               Assuming `path` is an augmentation of `based_of`,
				this parameter is used to load the original dataset and
				prevent having test_data that have augmented images in the training set
			**kwargs          (Any):               Keyword arguments for the loading function
				(ex for image: `keras.src.utils.image_dataset_from_directory(..., **kwargs)`)
		Returns:
			Dataset: Dataset object

		Examples:
			.. code-block:: python

				> dataset = DatasetLoader.from_path(
					path="data/pizza_augmented",
					loading_type="image",
					seed=42,
					test_size=0.2,
					val_size=0.2,
					grouping_strategy=GroupingStrategy.NONE,
					based_of="data/pizza",

					# Image loading kwargs
					color_mode="grayscale",
					image_size=(224, 224),
				)
		"""
		# Assertions
		assert grouping_strategy in GroupingStrategy, f"Invalid grouping strategy: '{grouping_strategy.name}'"
		assert loading_type in ("image",), f"Invalid loading type: '{loading_type}'"

		# Set seed
		np.random.seed(seed)

		# Load the base dataset
		original_dataset: Dataset = Dataset.empty()
		if based_of:
			original_dataset = DatasetLoader.from_path(
				path=based_of,
				loading_type=loading_type,
				seed=seed,
				test_size=test_size,
				val_size=val_size,
				grouping_strategy=grouping_strategy,
				**kwargs
			)

		# Load the data
		all_data: XyTuple = XyTuple.empty()
		if loading_type == "image":
			for key in DEFAULT_IMAGE_KWARGS.keys():
				if not kwargs.get(key):
					kwargs[key] = DEFAULT_IMAGE_KWARGS[key]

			# Load the data using image_dataset_from_directory
			# Grouping strategy can be changed by image_dataset_from_directory so we need to save it
			all_data, all_labels, grouping_strategy = GroupingStrategy.image_dataset_from_directory(
				grouping_strategy, path, seed, **kwargs
			)

			# Split the data using stratification
			real_test_size: float = test_size if not based_of else 0
			training_data, test_data = all_data.split(real_test_size, seed=DataScienceConfig.SEED)
			training_data, val_data = training_data.split(val_size, seed=DataScienceConfig.SEED)

		# Create and return the dataset
		dataset = Dataset(
			training_data=training_data,
			val_data=val_data,
			test_data=test_data,
			name=path,
			grouping_strategy=grouping_strategy,
			labels=all_labels,
			loading_type=loading_type
		)

		# If this dataset is based on another dataset, ensure test data consistency
		if based_of:
			dataset.exclude_augmented_images_from_val_test(original_dataset)

		# Remember the original dataset
		dataset.original_dataset = original_dataset

		return dataset

