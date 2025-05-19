"""
This module contains utility functions for loading image data from directories.

It provides alternatives to Keras image loading functions, focused on
efficient image loading, resizing, and preprocessing using PIL.
The main functionality allows loading images from directories into
numpy arrays suitable for machine learning model input.
"""
# pyright: reportUnknownMemberType=false

# Imports
from __future__ import annotations

import os
from typing import Any

import numpy as np
from ...decorators import handle_error, LogLevels
from ...parallel import multithreading
from ...print import warning
from ...io import clean_path
from numpy.typing import NDArray
from PIL import Image

# Constants
ALLOWLIST_FORMATS: tuple[str, ...] = tuple(ex for ex, f in Image.registered_extensions().items() if f in Image.OPEN)
""" List of image formats supported by PIL """

# Functions
def load_images_from_directory(
	directory_path: str,
	image_size: tuple[int, int] = (224, 224),
	color_mode: str | None = "RGB",
	resample: Image.Resampling = Image.Resampling.LANCZOS,
	to_float32: bool = True,
	**kwargs: Any
) -> list[tuple[NDArray[Any], str]]:
	""" Load images from a directory using PIL instead of Keras.

	This function loads all images from a directory and its subdirectories, resizes them to the specified size,
	converts them to the specified color mode, and returns them as a list of numpy arrays.
	Unlike Keras' image_dataset_from_directory, this function doesn't create batches or labels.
	If directory_path is a file path, it will load that single image.

	Args:
		directory_path  (str):              Path to the directory containing images or a single image file
		image_size      (tuple[int, int]):  Size to which images should be resized
		color_mode      (str | None):       Color mode to use ("RGB" or "grayscale")
		resample        (Image.Resampling): Resampling filter to use when resizing
		to_float32      (bool):             Whether to convert the image to float32 (between 0 and 1)
		**kwargs        (Any):              Additional arguments (ignored, for compatibility)

	Returns:
		list[tuple[NDArray[Any], str]]: List of tuples containing images
			with shape (height, width, channels) and their file paths
	"""
	# Function to load images from a directory
	def _load_image(img_path: str) -> tuple[NDArray[Any], str]:
		# Open image using PIL and decorate with error handling the Image.open function
		img: Image.Image = handle_error(
			message=f"Failed to open image: '{img_path}'",
			error_log=LogLevels.WARNING_TRACEBACK
		)(Image.open)(img_path)

		# Resize image with proper resampling
		img = img.resize(image_size, resample=resample)

		# If grayscale, convert to grayscale, else convert to correct color mode
		is_grayscale: bool = color_mode is not None and color_mode.lower() == "grayscale"
		img = img.convert("L" if is_grayscale else color_mode)

		# Convert to numpy array to float32 without normalizing (not this function's job)
		img_array: NDArray[Any] = np.array(img, dtype=np.float32) if to_float32 else np.array(img)

		# Add channel dimension if grayscale
		if is_grayscale:
			img_array = np.expand_dims(img_array, axis=-1)  # Add channel dimension, e.g. (224, 224, 1)

		return img_array, img_path

	# If directory_path is a file, return the image
	if os.path.isfile(directory_path):

		# Check if the file is an image
		if any(directory_path.endswith(ext) for ext in ALLOWLIST_FORMATS):
			return [_load_image(directory_path)]

		# If the file is not an image, warn the user
		else:
			warning(f"File '{directory_path}' is not a supported image format")
			return []

	# Find all image files
	image_files: list[str] = []
	for root, _, files in os.walk(directory_path):
		image_files.extend(clean_path(f"{root}/{f}") for f in files if f.endswith(ALLOWLIST_FORMATS))

	# Load and process images in parallel
	return multithreading(_load_image, image_files)

