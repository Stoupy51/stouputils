"""
This module contains the GroupingStrategy class, which provides a strategy for grouping images when loading a dataset.

There are 3 strategies, NONE, SIMPLE and CONCATENATE.
Refer to the docstrings of the GroupingStrategy class for more information.
"""
# pyright: reportUnknownMemberType=false

# Imports
from __future__ import annotations

import os
from enum import Enum
from typing import Any

import numpy as np
from numpy.typing import NDArray

from ...decorators import handle_error
from ...parallel import multiprocessing
from ...print import warning
from ...io import clean_path
from ..config.get import DataScienceConfig
from .image_loader import load_images_from_directory
from .xy_tuple import XyTuple


# Grouping strategy class for the dataset
class GroupingStrategy(Enum):
	""" Grouping strategy for the dataset """

	NONE = 0
	""" Default behavior: A subfolder "subject1" is a group of images, all images are grouped together (list of features)
	and the label is the class of the folder above (class1)

	Example file tree:

	- dataset/class1/subject1/image1.png
	- dataset/class1/subject1/image2.png
	- dataset/class1/subject1/image3.png

	Example data (if binary classification):

	- features = [features_image1, features_image2, features_image3] where
		features_image1, features_image2, features_image3 are NDArray[Any] of shape `(224, 224, 3)`
	- labels = [1.0, 0.0]

	If subjects do not have the same number of images,
	the missing images are padded with zeros so every features have the same shape.

	This strategy preserves the relationship between images of the same subject when splitting the dataset,
	ensuring that all images from the same subject stay together in either train or test sets.
	"""

	CONCATENATE = 1
	""" A subfolder "subject1" is a group of images, all images are concatenated into a single feature (NDArray[Any])
	and the label is the class of the folder above (class1)

	Example file tree:

	- dataset/class1/subject1/image1.png
	- dataset/class1/subject1/image2.png
	- dataset/class1/subject1/image3.png

	Example data (if binary classification):

	- features will have a shape of `(224, 224, 3*num_images)` (if RGB images).
		Notice that the concatenation is done along the last axis.
	- labels = [1.0, 0.0]

	If subjects do not have the same number of images,
	the missing images are padded with zeros so every features have the same shape.
	"""

	@staticmethod
	def _load_folder(
		folder_path: str,
		class_idx: int,
		num_classes: int,
		kwargs: dict[str, Any]
	) -> tuple[list[NDArray[Any]], NDArray[Any], tuple[str, ...]]:
		""" Load images from a single folder.

		Args:
			folder_path        (str):               Path to the folder
			class_idx          (int):               Index of the class
			num_classes        (int):               Total number of classes
			kwargs             (dict[str, Any]):    Additional arguments for image_dataset_from_directory
		Returns:
			list[tuple[NDArray[Any], NDArray[Any], str]]: List of tuples containing (images, one-hot label, filepaths)

		Examples:
			.. code-block:: python

				> data = GroupingStrategy._load_folder(
					folder_path="data/pizza/pizza1",
					class_idx=0,
					num_classes=2,
					kwargs={"color_mode": "grayscale"}
				)
				> features, label, filepaths = zip(*data, strict=True)
		"""
		# Load images from the folder
		images_and_paths: list[tuple[NDArray[Any], str]] = load_images_from_directory(folder_path, **kwargs)
		images, paths = zip(*images_and_paths, strict=True) if images_and_paths else ([], [])
		images: list[NDArray[Any]]
		paths: list[str]

		# Create a one-hot encoded label vector
		label: NDArray[Any] = np.zeros(num_classes)
		label[class_idx] = 1.0

		return list(images), label, tuple(paths)

	@staticmethod
	@handle_error(error_log=DataScienceConfig.ERROR_LOG)
	def image_dataset_from_directory(
		grouping_strategy: GroupingStrategy,
		path: str,
		seed: int,
		**kwargs: Any
	) -> tuple[XyTuple, tuple[str, ...], GroupingStrategy]:
		""" Load images from a directory while keeping groups of images together.

		Args:
			grouping_strategy  (GroupingStrategy):  Grouping strategy to use
			path               (str):               Path to the dataset directory
			seed               (int):               Random seed for shuffling
			**kwargs           (Any):               Additional arguments passed to image_dataset_from_directory

		Returns:
			XyTuple:          XyTuple with the data
			tuple[str, ...]:  List of class labels (strings)
			GroupingStrategy: Grouping strategy used (because it can be updated)

		Examples:
			.. code-block:: python

				> data = GroupingStrategy.image_dataset_from_directory(
					grouping_strategy=GroupingStrategy.NONE,
					path="data/pizza",
					seed=42,
					color_mode="grayscale"
				)
				> all_data: XyTuple = data[0]
				> all_labels: tuple[str, ...] = data[1]
		"""
		# Get all subdirectories (classes)
		path = clean_path(path)
		class_dirs: tuple[str, ...] = tuple(d for d in os.listdir(path) if os.path.isdir(f"{path}/{d}"))

		# Check if there are subfolders in each class
		any_subfolders: bool = any(
			os.path.isdir(f"{path}/{class_dir}/{sub_dir}")
			for class_dir in class_dirs for sub_dir in os.listdir(f"{path}/{class_dir}")
		)

		# Verify if wrong grouping strategy, then adjust it
		if grouping_strategy != GroupingStrategy.NONE and not any_subfolders:
			warning(
				f"Strategy is {grouping_strategy.name} but there are no subfolders in each class, adjusting to NONE "
				"as there is no way to group the images together, that just doesn't make sense"
			)
			grouping_strategy = GroupingStrategy.NONE

		# Prepare multithreading arguments
		queue: list[tuple[str, int, int, dict[str, Any]]] = []
		for class_idx, class_dir in enumerate(class_dirs):
			class_path: str = f"{path}/{class_dir}"

			# Get subfolders (class1/subject1/image1.png) to the queue
			sub_folders: list[str] = [d for d in os.listdir(class_path) if os.path.isdir(f"{class_path}/{d}")]
			for sub_folder in sub_folders:
				folder_path: str = f"{class_path}/{sub_folder}"
				queue.append((folder_path, class_idx, len(class_dirs), kwargs))

			# Get files in the class folder
			files: list[str] = [f for f in os.listdir(class_path) if os.path.isfile(f"{class_path}/{f}")]
			for file in files:
				queue.append((f"{class_path}/{file}", class_idx, len(class_dirs), kwargs))

		# Process folders in parallel
		splitted: list[str] = path.split('/')
		description: str = f".../{splitted[-1]}" if len(splitted) > 2 else path
		extracted_folders: list[tuple[list[NDArray[Any]], NDArray[Any], tuple[str, ...]]] = multiprocessing(
			GroupingStrategy._load_folder,
			queue,
			use_starmap=True,
			desc=f"Loading dataset '{description}'"
		)

		# Extract results properly
		all_X: list[list[NDArray[Any]]] = []
		all_y: list[NDArray[Any]] = []
		all_filenames: list[tuple[str, ...]] = []

		# For each folder extracted (each subject maybe)
		for images, label, filepaths in extracted_folders:
			if not images:
				continue	# Skip if no images are found

			to_append_X: list[NDArray[Any]] = []
			to_append_filepaths: list[str] = []

			# For each image of the subject,
			for image, filepath in zip(images, filepaths, strict=True):

				# Add the data
				to_append_X.append(image)
				to_append_filepaths.append(filepath)

			# Append the subject if there are images
			if to_append_X:

				# If concatenate strategy, combine images along the channel axis
				if grouping_strategy == GroupingStrategy.CONCATENATE:
					# Step 1: Make an array of shape (num_images, height, width, channels)
					images_array = np.array(to_append_X)

					# Step 2: Transpose to move channels next to num_images
					# From (num_images, height, width, channels) to (height, width, num_images, channels)
					images_array = np.transpose(images_array, (1, 2, 0, 3))

					# Step 3: Reshape to combine num_images and channels dimensions
					# From (height, width, num_images, channels) to (height, width, num_images * channels)
					images_array = images_array.reshape(images_array.shape[0], images_array.shape[1], -1)

					# Step 4: Add single concatenated feature array
					all_X.append([images_array])

				# Else, just add the images
				else:
					all_X.append(to_append_X)

				all_y.append(label)
				all_filenames.append(tuple(to_append_filepaths))

		# Fix different sizes of images
		if grouping_strategy == GroupingStrategy.CONCATENATE:
			all_X = GroupingStrategy.fix_different_sizes(all_X, grouping_strategy)

		# Shuffle the data
		combined = list(zip(all_X, all_y, all_filenames, strict=True))
		np.random.seed(seed)
		np.random.shuffle(combined) # pyright: ignore [reportArgumentType]
		all_X, all_y, all_filenames = zip(*combined, strict=True)

		# Create a XyTuple and return it
		return XyTuple(all_X, all_y, tuple(all_filenames)), class_dirs, grouping_strategy


	@staticmethod
	def fix_different_sizes(data: list[list[NDArray[Any]]], grouping_strategy: GroupingStrategy) -> list[list[NDArray[Any]]]:
		""" Fix different sizes of images in a list of lists of numpy arrays.

		Simple strategy will add empty images to shape[0]
		Concatenate strategy will add empty channels to shape[-1]

		Args:
			data                (list[list[NDArray[Any]]]):  List of lists of numpy arrays
			grouping_strategy   (GroupingStrategy):        Grouping strategy used

		Returns:
			list[list[NDArray[Any]]]:  List of lists of numpy arrays with consistent shapes

		Examples:
			>>> # Concatenate grouping strategy
			>>> data = [[np.zeros((7, 224, 224, 3))], [np.zeros((1, 224, 224, 1))]]
			>>> data = GroupingStrategy.fix_different_sizes(data, GroupingStrategy.CONCATENATE)
			>>> data[0][0].shape
			(7, 224, 224, 3)
			>>> data[1][0].shape
			(1, 224, 224, 3)
			>>> data[1][0].shape[0] == data[0][0].shape[0]
			False
			>>> data[1][0].shape[-1] == data[0][0].shape[-1]
			True
		"""
		# Add empty channels to images that have less channels than others
		if grouping_strategy == GroupingStrategy.CONCATENATE:
			# Find the maximum number of channels across all images in all groups
			max_num_channels: int = max(x.shape[-1] for group in data for x in group)

			for i, group in enumerate(data):
				for j, image in enumerate(group):
					if image.shape[-1] < max_num_channels:
						# Calculate how many times to repeat the channels
						repeat_count: int = int(np.ceil(max_num_channels / image.shape[-1]))

						# Repeat the channels and then slice to get exactly the right number
						repeated_channels = np.repeat(image, repeat_count, axis=-1)
						data[i][j] = repeated_channels[..., :max_num_channels]

		# Return the fixed list of lists of numpy arrays
		return data

