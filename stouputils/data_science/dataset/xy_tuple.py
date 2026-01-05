"""
This module contains the XyTuple class, which is a specialized tuple subclass
for maintaining ML dataset integrity with file tracking.

XyTuple handles grouped data to preserve relationships between files from the same subject.
All data is treated as grouped, even single files, for consistency.

File Structure Example:

- dataset/class1/hello.png
- dataset/class2/subject1/image1.png
- dataset/class2/subject1/image2.png

Data Representation:

1. Grouped Format (as loaded):
   - X: list[list[Any]] = [[image], [image, image], ...]
   - y: list[Any] = [class1, class2, ...]
   - filepaths = [("hello.png",), ("subject1/image1.png", "subject1/image2.png"), ...]

2. Ungrouped Format (after XyTuple.ungroup()):
   - X: list[Any] = [image, image, image, ...]
   - y: list[Any] = [class1, class2, class2, ...]
   - filepaths: tuple[str, ...] = ("hello.png", "subject1/image1.png", "subject1/image2.png")

Key Features:

- Preserves subject-level grouping during dataset operations
- Handles augmented files with automatic original/augmented mapping
- Supports group-aware dataset splitting
- Implements stratified k-fold splitting that maintains group integrity
"""
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
# pyright: reportIncompatibleMethodOverride=false
# pyright: reportUnknownArgumentType=false

# Imports
from __future__ import annotations

import os
from collections import defaultdict
from collections.abc import Generator, Iterable
from typing import Any

import numpy as np
from numpy.typing import NDArray
from sklearn.model_selection import BaseCrossValidator, LeaveOneOut, LeavePOut, StratifiedKFold, train_test_split

from ...print import info, warning
from ..config.get import DataScienceConfig
from ..utils import Utils


# Class definition
class XyTuple(tuple[list[list[Any]], list[Any], tuple[tuple[str, ...], ...]]):
	""" A tuple containing X (features) and y (labels) data with file tracking.

	XyTuple handles grouped data to preserve relationships between files from the same subject.
	All data is treated as grouped, even single files, for consistency.

	Examples:
		>>> data = XyTuple(X=[1, 2, 3], y=[4, 5, 6], filepaths=(("file1.jpg",), ("file2.jpg",), ("file3.jpg",)))
		>>> data.X
		[[1], [2], [3]]
		>>> data.y
		[4, 5, 6]
		>>> XyTuple(X=[1, 2], y=["a", "b"]).filepaths
		()
		>>> isinstance(XyTuple(X=[1, 2], y=[3, 4]), tuple)
		True
	"""
	def __new__(cls, X: NDArray[Any] | list[Any], y: NDArray[Any] | list[Any], filepaths: tuple[tuple[str, ...], ...] = ()) -> XyTuple:
		""" Initialize the XyTuple with given data.

		Args:
			X          (NDArray[Any] | list):        Features data, at least 2 dimensions: [[np.array, np.array, ...], ...]
			y          (NDArray[Any] | list):        Labels data, at least 1 dimension: [np.array, np.array, ...]
			filepaths (tuple[tuple[str, ...], ...]): Optional tuple of file paths tuples corresponding to the features
		"""
		# Assertions
		assert len(X) == len(y), f"X and y must have the same length, got {len(X)} and {len(y)}"
		if filepaths:
			assert isinstance(filepaths, tuple), f"filepaths must be a tuple, got {type(filepaths)}"
			assert all(isinstance(paths, tuple) for paths in filepaths), "Each element in filepaths must be a tuple"
			assert len(filepaths) == len(X), f"filepaths and X must have the same length, got {len(filepaths)} and {len(X)}"

		# Convert each element of X to a list of one element if it is not Iterable
		Xl: list[Iterable[Any]]
		if len(X) > 0 and not isinstance(X[0], Iterable):
			Xl = [[x] if not isinstance(x, Iterable) else x for x in X]
		elif isinstance(X, np.ndarray):
			Xl = list(X)
		else:
			Xl = X

		# Convert y if needed
		yl: list[Any] = y if isinstance(y, list) else list(y)

		# Return the new XyTuple
		return tuple.__new__(cls, (Xl, yl, filepaths))

	def __init__(self, *args: Any, **kwargs: Any) -> None:
		""" Initialize the XyTuple with given data.

		Args:
			X          (NDArray[Any] | list):        Features data, at least 2 dimensions: [[np.array, np.array, ...], ...]
			y          (NDArray[Any] | list):        Labels data, at least 1 dimension: [np.array, np.array, ...]
			filepaths (tuple[tuple[str, ...], ...]): Optional tuple of file paths tuples corresponding to the features
		"""
		super().__init__()

		# Attributes
		self._X: list[list[Any]] = self[0]
		""" Features data, list of groups of different sized numpy arrays.
		Each list corresponds to a subject that can have, for instance, multiple images

		This is a protected attribute accessed via the public property self.X.
		"""
		self._y: list[Any] = self[1]
		""" Labels data, either a numpy array or a list of different sized numpy arrays.

		This is a protected attribute accessed via the public property self.y.
		"""
		self.filepaths: tuple[tuple[str, ...], ...] = self[2]
		""" List of filepaths corresponding to the features (one file = list with one element) """
		self.augmented_files: dict[str, str] = self.update_augmented_files()
		""" Dictionary mapping all files to their original filepath, e.g. {"file1_aug_1.jpg": "file1.jpg"} """

	@property
	def n_samples(self) -> int:
		""" Number of samples in the dataset (property). """
		return len(self._y)

	@property
	def X(self) -> list[list[Any]]:  # noqa: N802
		return self._X

	@property
	def y(self) -> list[Any]:
		return self._y

	def __str__(self) -> str:
		return f"XyTuple(X: {str(self.X)[:20]}..., y: {str(self.y)[:20]}..., n_files: {len(self.filepaths)})"

	def __repr__(self) -> str:
		return f"XyTuple(X: {type(self.X)}, y: {type(self.y)}, n_files: {len(self.filepaths)})"

	def __eq__(self, other: object) -> bool:
		if isinstance(other, XyTuple):
			return bool(self.X == other.X and self.y == other.y and self.filepaths == other.filepaths)
		elif isinstance(other, tuple):
			if len(other) == 0 and len(self.X) == 0:
				return True
			if len(other) == 3:
				return bool(self.X == other[0] and self.y == other[1] and self.filepaths == other[2])
			if len(other) == 2:
				return bool(self.X == other[0] and self.y == other[1])
		return False

	def __add__(self, other: XyTuple | Any) -> XyTuple:
		""" Add two XyTuple instances together (merge them)

		Args:
			other (XyTuple): The XyTuple instance to add
		"""
		if not isinstance(other, XyTuple):
			raise ValueError("other must be an XyTuple instance")
		if other.is_empty():
			return self

		# Merge the XyTuple instances
		new_X: list[list[Any]] = [*self.X, *other.X]
		new_y: list[Any] = [*self.y, *other.y]
		new_filepaths: tuple[tuple[str, ...], ...] = (*self.filepaths, *other.filepaths)

		# Return the new XyTuple
		return XyTuple(X=new_X, y=new_y, filepaths=new_filepaths)


	def __getnewargs_ex__(self) -> tuple[tuple[Any, Any, Any], dict[str, Any]]:
		""" Return arguments for __new__ during unpickling. """
		# Return the components needed by __new__
		# self[0] is X, self[1] is y, self[2] is filepaths
		return ((self[0], self[1], self.filepaths), {})


	## Methods
	def is_empty(self) -> bool:
		""" Check if the XyTuple is empty. """
		return len(self.X) == 0

	def update_augmented_files(self) -> dict[str, str]:
		""" Create mapping of all files to their original version.
		If no filepaths are provided, return an empty dictionary

		Returns:
			dict[str, str]: Dictionary where keys are all files (original and augmented),
							and values are the corresponding original file

		Examples:
			>>> xy = XyTuple(X=[1, 2, 3], y=[4, 5, 6], filepaths=(("file1.jpg",), ("file2.jpg",), ("file1_aug_1.jpg",)))
			>>> xy.augmented_files
			{'file1.jpg': 'file1.jpg', 'file2.jpg': 'file2.jpg', 'file1_aug_1.jpg': 'file1.jpg'}
			>>> xy_empty = XyTuple(X=[1, 2], y=[3, 4])
			>>> xy_empty.augmented_files
			{}
		"""
		if len(self.filepaths) == 0:
			return {}

		augmented_files: dict[str, str] = {}
		originals: set[str] = set()

		# First pass: identify all original files (not augmented)
		for file_list in self.filepaths:
			for file in file_list:
				if DataScienceConfig.AUGMENTED_FILE_SUFFIX not in file:
					originals.add(file)
					augmented_files[file] = file

		# Second pass: map augmented files to their original file
		for file_list in self.filepaths:

			# Get the first file in the list (since if either it's grouped or not, it's the same file original file)
			file: str = file_list[0]
			if DataScienceConfig.AUGMENTED_FILE_SUFFIX in file:

				# Extract original path from augmented filepath
				splitted: list[str] = file.split(DataScienceConfig.AUGMENTED_FILE_SUFFIX, 1)
				if "/" in splitted[1]:
					# Case where: ".../fixee/114_aug_1/114 Bassin.jpg"
					# Becomes: ".../fixee/114/114 Bassin.jpg"
					slash_split: list[str] = splitted[1].split("/", 1)	# ["1", "114 Bassin.jpg"]
					original_path: str = splitted[0] + "/" + slash_split[1]
				else:
					# Case where: ".../fixee/114 Bassin_aug_1.jpg"
					# Becomes: ".../fixee/114 Bassin.jpg"
					extension: str = os.path.splitext(splitted[1])[1]	# .jpg
					original_path: str = splitted[0] + extension

				# If the original file is known, add the file to the augmented_files dictionary
				if original_path in originals:
					augmented_files[file] = original_path

				# Else, the original file is not known, so we treat the augmented file as its own original
				else:
					warning(
						f"Original file '{original_path}' not found for augmented file '{file}', "
						"treating it as its own original"
					)
					augmented_files[file] = file  # Fallback to self

		return augmented_files


	# New protected methods
	def group_by_original(self) -> tuple[dict[str, list[int]], dict[str, Any]]:
		""" Group samples by their original files and collect labels.

		Returns:
			tuple[dict[str, list[int]], dict[str, Any]]:
				- dict[str, list[int]]: Mapping from original files to their sample indices
				- dict[str, Any]: Mapping from original files to their labels

		Examples:
			>>> xy = XyTuple(X=[1, 2, 3], y=["a", "b", "c"],
			...              filepaths=(("file1.jpg",), ("file2.jpg",), ("file1_aug_2.jpg",)))
			>>> indices, labels = xy.group_by_original()
			>>> sorted(indices.items())
			[('file1.jpg', [0, 2]), ('file2.jpg', [1])]
			>>> [(x, str(y)) for x, y in sorted(labels.items())]
			[('file1.jpg', 'a'), ('file2.jpg', 'b')]
		"""
		# Initializations
		original_to_indices: dict[str, list[int]] = defaultdict(list)
		original_labels: dict[str, Any] = {}
		class_indices: NDArray[Any] = Utils.convert_to_class_indices(self.y)

		# Group samples by original files and collect labels
		for i, files in enumerate(self.filepaths):

			# Get the first file in the list (since if either it's grouped or not, it's the same file original file)
			file: str = files[0]

			# Get the original file and add the index of the file to it
			original: str = self.augmented_files[file]
			original_to_indices[original].append(i)

			# Add the label to the original file
			if original not in original_labels:
				original_labels[original] = class_indices[i]

		return original_to_indices, original_labels

	def get_indices_from_originals(
		self,
		original_to_indices: dict[str, list[int]],
		originals: tuple[str, ...] | list[str]
	) -> list[int]:
		""" Get flattened list of indices for given original files.

		Args:
			original_to_indices (dict[str, list[int]]): Mapping from originals to indices
			originals           (tuple[str, ...]):      List of original files to get indices for

		Returns:
			list[int]: Flattened list of all indices associated with the originals

		Examples:
			>>> xy = XyTuple(X=[1, 2, 3, 4], y=["a", "b", "c", "d"],
			...              filepaths=(("file1.jpg",), ("file2.jpg",), ("file1_aug_1.jpg",), ("file3.jpg",)))
			>>> orig_to_idx, _ = xy.group_by_original()
			>>> sorted(xy.get_indices_from_originals(orig_to_idx, ["file1.jpg", "file3.jpg"]))
			[0, 2, 3]
			>>> xy.get_indices_from_originals(orig_to_idx, ["file2.jpg"])
			[1]
			>>> xy.get_indices_from_originals(orig_to_idx, [])
			[]
		"""
		return [idx for orig in originals for idx in original_to_indices[orig]]

	def create_subset(self, indices: Iterable[int]) -> XyTuple:
		""" Create a new XyTuple containing only the specified indices.

		Args:
			indices (list[int]): List of indices to include in the subset

		Returns:
			XyTuple: New instance containing only the specified data points

		Examples:
			>>> xy = XyTuple(X=[10, 20, 30, 40], y=["a", "b", "c", "d"],
			...              filepaths=(("f1.jpg",), ("f2.jpg",), ("f3.jpg",), ("f4.jpg",)))
			>>> subset = xy.create_subset([0, 2])
			>>> subset.X
			[[10], [30]]
			>>> subset.y
			['a', 'c']
			>>> subset.filepaths
			(('f1.jpg',), ('f3.jpg',))
			>>> xy.create_subset([]).X
			[]
		"""
		return XyTuple(
			X=[self.X[i] for i in indices],
			y=[self.y[i] for i in indices],
			filepaths=tuple(self.filepaths[i] for i in indices) if self.filepaths else ()
		)

	def remove_augmented_files(self) -> XyTuple:
		""" Remove augmented files from the dataset, keeping only original files.

		This method identifies augmented files by checking if the file path contains
		the augmentation suffix and creates a new dataset without them.

		Returns:
			XyTuple: A new XyTuple instance containing only non-augmented files

		Examples:
			>>> xy = XyTuple(X=[1, 2, 3], y=[0, 1, 0],
			...              filepaths=(("file1.jpg",), ("file2.jpg",), ("file1_aug_1.jpg",)))
			>>> non_aug = xy.remove_augmented_files()
			>>> len(non_aug.X)
			2
			>>> non_aug.filepaths
			(('file1.jpg',), ('file2.jpg',))
		"""
		if len(self.filepaths) == 0:
			return self

		# Find indices of all non-augmented files
		indices_to_keep: list[int] = []
		for i, file_list in enumerate(self.filepaths):
			if DataScienceConfig.AUGMENTED_FILE_SUFFIX not in file_list[0]:
				indices_to_keep.append(i)

		# Create a new dataset with only the non-augmented files
		return self.create_subset(indices_to_keep)

	def split(
		self,
		test_size: float,
		seed: int | np.random.RandomState | None = None,
		num_classes: int | None = None,
		remove_augmented: bool = True
	) -> tuple[XyTuple, XyTuple]:
		""" Stratified split of the dataset ensuring original files and their augmented versions stay together.

		This function splits the dataset into train and test sets while keeping
		augmented versions of the same image together. It works in several steps:

		1. Groups samples by original file and collects corresponding labels
		2. Performs stratified split on the original files to maintain class distribution
		3. Creates new XyTuple instances for train and test sets using the split indices

		Args:
			test_size        (float):               Proportion of dataset to include in test split
			seed             (int | RandomState):   Controls shuffling for reproducible output
			num_classes      (int | None):          Number of classes in the dataset (If None, auto-calculate)
			remove_augmented (bool):                Whether to remove augmented files from the test set
		Returns:
			tuple[XyTuple, XyTuple]: Train and test splits containing (features, labels, file paths)

		Examples:
			>>> xy = XyTuple(X=np.arange(10), y=[0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
			...              filepaths=(("f1.jpg",), ("f2.jpg",), ("f3.jpg",), ("f4.jpg",), ("f5.jpg",),
			...                         ("f6.jpg",), ("f7.jpg",), ("f8.jpg",), ("f9.jpg",), ("f10.jpg",)))
			>>> train, test = xy.split(test_size=0.3, seed=42)
			>>> len(train.X), len(test.X)
			(7, 3)
			>>> train, test = xy.split(test_size=0.0)
			>>> len(train.X), len(test.X)
			(10, 0)
			>>> train, test = xy.split(test_size=1.0)
			>>> len(train.X), len(test.X)
			(0, 10)
		"""
		# Assertions
		assert 0 <= test_size <= 1, f"test_size must be between 0 and 1, got {test_size}"

		# Special cases (no test set or no train set)
		if test_size == 0.0:
			return self, XyTuple.empty()
		if test_size == 1.0:
			return XyTuple.empty(), self

		# Step 1: Group samples using protected method
		original_to_indices, original_labels = self.group_by_original()
		originals: tuple[str, ...] = tuple(original_to_indices.keys())

		# Step 2: Prepare labels for stratified split
		labels: list[Any] = [original_labels[orig] for orig in originals]

		# Check if we have enough samples for stratification
		if num_classes is None:
			num_classes = len(np.unique(labels))
		assert (num_classes / len(originals)) < test_size, (
			f"Not enough samples ({len(originals)}) in order to stratify the test set ({test_size}). In your case, "
			f"test size should be at least {num_classes / len(originals)} because you have {num_classes} classes."
		)

		# Perform stratified split on original files (we'll add the augmented files later)
		train_orig: tuple[str, ...]
		test_orig: tuple[str, ...]
		train_orig, test_orig = train_test_split(
			originals,
			test_size=test_size,
			random_state=seed,
			stratify=labels
		)

		# Step 3: Create train/test splits while keeping augmented files together
        # For each original file in train_orig, get all indices of the augmented files
		train_indices: list[int] = self.get_indices_from_originals(original_to_indices, train_orig)
		test_indices: list[int] = self.get_indices_from_originals(original_to_indices, test_orig)

		# Create new XyTuple instances for train and test sets
		train: XyTuple = self.create_subset(train_indices)
		test: XyTuple = self.create_subset(test_indices)

		if remove_augmented:
			test = test.remove_augmented_files()

		return train, test

	def kfold_split(
		self,
		n_splits: int,
		remove_augmented: bool = True,
		shuffle: bool = True,
		random_state: int | None = None,
		verbose: int = 1
	) -> Generator[tuple[XyTuple, XyTuple], None, None]:
		""" Perform stratified k-fold splits while keeping original and augmented data together.

		If filepaths are not provided, performs a regular stratified k-fold split on the data.

		Args:
			n_splits          (int): Number of folds, will use LeaveOneOut if -1 or too big, -X will use LeavePOut
			remove_augmented  (bool): Whether to remove augmented files from the validation sets
			shuffle           (bool): Whether to shuffle before splitting
			random_state      (int | None): Seed for reproducible shuffling
			verbose           (int): Whether to print information about the splits

		Returns:
			list[tuple[XyTuple, XyTuple]]: List of train/test splits

		Raises:
			ValueError: If there are fewer original files than requested splits

		Examples:
			>>> xy = XyTuple(X=np.arange(8), y=[[1, 0], [0, 1], [1, 0], [0, 1], [1, 0], [0, 1], [1, 0], [0, 1]],
			...              filepaths=(("f1.jpg",), ("f2.jpg",), ("f3.jpg",), ("f4.jpg",), ("f5.jpg",),
			...                          ("f6.jpg",), ("f7.jpg",), ("f8.jpg",)))
			>>> splits = list(xy.kfold_split(n_splits=2, random_state=42, verbose=0))
			>>> len(splits)
			2
			>>> len(splits[0][0].X), len(splits[0][1].X)  # First fold: train size, test size
			(4, 4)

			>>> xy = XyTuple(X=np.arange(8), y=[[1, 0], [0, 1], [1, 0], [0, 1], [1, 0], [0, 1], [1, 0], [0, 1]])
			>>> splits = list(xy.kfold_split(n_splits=2, random_state=42, verbose=0))
			>>> len(splits)
			2
			>>> len(splits[0][0].X), len(splits[0][1].X)  # First fold: train size, test size
			(4, 4)

			>>> xy = XyTuple(X=np.arange(4), y=[[0], [1], [0], [1]])
			>>> splits = list(xy.kfold_split(n_splits=2, random_state=42, verbose=0))
			>>> len(splits)
			2
			>>> len(splits[0][0].X), len(splits[0][1].X)
			(2, 2)

			>>> xy_few = XyTuple(X=[1, 2], y=[0, 1], filepaths=(("f1.jpg",), ("f2.jpg",)))
			>>> splits = list(xy_few.kfold_split(n_splits=1, verbose=0))
			>>> splits[0][0].X
			[[1], [2]]
			>>> splits[0][1].X
			[]

			>>> # Fallback to LeaveOneOut since n_splits is too big, so n_splits becomes -> 2
			>>> xy_few = XyTuple(X=[1, 2], y=[0, 1], filepaths=(("f1.jpg",), ("f2.jpg",)))
			>>> splits = list(xy_few.kfold_split(n_splits=516416584, shuffle=False, verbose=0))
			>>> len(splits)
			2
			>>> splits[1][0].X
			[[1]]
			>>> splits[1][1].X
			[[2]]

			>>> # Fallback to LeavePOut since n_splits is negative
			>>> xy_few = XyTuple(X=[1, 2, 3, 4], y=[0, 1, 0, 1])
			>>> splits = list(xy_few.kfold_split(n_splits=-2, shuffle=False, verbose=1))
			>>> len(splits)
			6
			>>> splits[0][0].X
			[[3], [4]]
			>>> splits[0][1].X
			[[1], [2]]
		"""
		if n_splits in (0, 1):
			if verbose > 0:
				warning("n_splits must be different from 0 and 1, assuming 100% train set and 0% test set")
			yield (self, XyTuple.empty())
			return

		# Create stratified k-fold splitter
		kf: BaseCrossValidator
		if n_splits == -1 or n_splits >= len(self.X):
			kf = LeaveOneOut()
		elif n_splits < -1:
			kf = LeavePOut(p=-n_splits)
		else:
			kf = StratifiedKFold(
				n_splits=n_splits,
				shuffle=shuffle,
				random_state=random_state
			)

		# Check if filepaths are provided
		if not self.filepaths:
			# Handle case with no filepaths - use regular StratifiedKFold on the data directly
			class_indices: NDArray[Any] = Utils.convert_to_class_indices(self.y)
			x_indices: NDArray[Any] = np.arange(len(self.X))

			# If LeaveOneOut, tell the user how many folds there are
			if verbose > 0 and n_splits == -1:
				info(f"Performing LeaveOneOut with {kf.get_n_splits(x_indices, class_indices)} folds")

			# Generate splits based on indices directly
			for train_idx, test_idx in kf.split(x_indices, class_indices):
				train_set: XyTuple = self.create_subset(train_idx)
				test_set: XyTuple = self.create_subset(test_idx)
				if remove_augmented:
					test_set = test_set.remove_augmented_files()
				yield (train_set, test_set)
			return

		# Group samples using protected method
		original_to_indices, original_labels = self.group_by_original()
		originals: list[str] = list(original_to_indices.keys())
		labels: list[Any] = [original_labels[orig] for orig in originals]

		# If n_splits is greater than the number of originals, use LeaveOneOut
		if len(originals) < n_splits or n_splits == -1:
			kf = LeaveOneOut()

		# Verbose
		new_n_splits: int = kf.get_n_splits(originals, labels) # pyright: ignore [reportArgumentType]
		if verbose > 0:
			info(f"Performing {new_n_splits}-fold cross-validation with {len(originals)} samples")

		# Convert labels to a format compatible with StratifiedKFold
		unique_labels: NDArray[Any] = np.unique(labels)
		label_mapping: dict[Any, int] = {label: i for i, label in enumerate(unique_labels)}
		encoded_labels: NDArray[Any] = np.array([label_mapping[label] for label in labels])

		# Generate splits based on original files
		for train_orig_idx, val_orig_idx in kf.split(originals, encoded_labels):

			# Get original files for this fold
			train_originals = [originals[i] for i in train_orig_idx]
			val_originals = [originals[i] for i in val_orig_idx]

			# Collect indices for this fold
			train_indices = self.get_indices_from_originals(original_to_indices, train_originals)
			val_indices = self.get_indices_from_originals(original_to_indices, val_originals)

			# Create splits
			new_train_set: XyTuple = self.create_subset(train_indices)
			new_val_set: XyTuple = self.create_subset(val_indices)
			if remove_augmented:
				new_val_set = new_val_set.remove_augmented_files()

			# Yield the splits
			yield (new_train_set, new_val_set)
		return

	def ungrouped_array(self) -> tuple[NDArray[Any], NDArray[Any], tuple[tuple[str, ...], ...]]:
		""" Ungroup data to flatten the structure.

		Converts from grouped format to ungrouped format:

		- Grouped: X: list[list[Any]], y: list[Any]
		- Ungrouped: X: NDArray[Any], y: NDArray[Any]

		Returns:
			tuple[NDArray[Any], NDArray[Any], tuple[tuple[str, ...], ...]]:
				A tuple containing (X, y, filepaths) in ungrouped format

		Examples:
			>>> xy = XyTuple(X=[[np.array([1])], [np.array([2]), np.array([3])], [np.array([4])]],
			...              y=[np.array(0), np.array(1), np.array(2)],
			...              filepaths=(("file1.png",), ("file2.png", "file3.png"), ("file4.png", "file5.png")))
			>>> X, y, filepaths = xy.ungrouped_array()
			>>> len(X)
			4
			>>> len(y)
			4
			>>> filepaths
			(('file1.png',), ('file2.png',), ('file3.png',), ('file4.png', 'file5.png'))
		"""
		# Pre-allocate lists with known sizes to avoid resizing
		total_items: int = sum(len(group) for group in self.X)
		X_ungrouped: list[Any] = [None] * total_items
		y_ungrouped: list[Any] = [None] * total_items
		filepaths_ungrouped: list[tuple[str, ...]] = [()] * total_items if self.filepaths else []

		idx: int = 0
		for i, group in enumerate(self.X):
			# Get the label for this group
			label = self.y[i]

			# Add each item in the group
			for j, item in enumerate(group):
				X_ungrouped[idx] = item
				y_ungrouped[idx] = label

				# Add filepaths if provided
				if self.filepaths:

					# If len(group) > 1, meaning each member of the group have one single filepath, add it for each member
					if len(group) > 1:
						filepaths_ungrouped[idx] = (self.filepaths[i][j],)

					# Else (len(group) == 1), one member in the group could have multiple filepaths so we add all of them
					else:
						filepaths_ungrouped[idx] = self.filepaths[i]

				idx += 1

		return np.array(X_ungrouped), np.array(y_ungrouped), tuple(filepaths_ungrouped)



	## Static methods
	@staticmethod
	def empty() -> XyTuple:
		""" Create an empty XyTuple.

		Returns:
			XyTuple: An empty XyTuple with empty lists for X, y, and filepaths

		Examples:
			>>> empty = XyTuple.empty()
			>>> empty.X
			[]
			>>> empty.y
			[]
			>>> empty.filepaths
			()
		"""
		return XyTuple(X=[], y=[], filepaths=())

