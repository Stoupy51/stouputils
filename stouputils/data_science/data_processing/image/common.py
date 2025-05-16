

# pyright: reportUnusedImport=false
# ruff: noqa: F401

# Imports
from typing import Any

import cv2
import numpy as np
from numpy.typing import NDArray


# Functions
def check_image(image: NDArray[Any], ignore_dtype: bool = False) -> None:
	""" Check if the image is valid

	Args:
		image         (NDArray[Any]):  Image to check
		ignore_dtype  (bool):        Ignore the dtype check
	"""
	# Check input data
	assert isinstance(image, np.ndarray), "Image must be a numpy array"
	assert len(image.shape) >= 2, "Image must have at least 2 dimensions"

	# Check dtype
	if not ignore_dtype:
		dtypes: list[type] = [np.uint8, np.int16, np.float32, np.float64]
		assert image.dtype in dtypes, f"Image must be of type {dtypes}"

