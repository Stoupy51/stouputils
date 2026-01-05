
# pyright: reportUnusedImport=false
# ruff: noqa: F401

# Imports
from .common import Any, NDArray, check_image, cv2, np


# Functions
def zoom_image(image: NDArray[Any], zoom_factor: float, ignore_dtype: bool = False) -> NDArray[Any]:
	""" Zoom into an image.

	Args:
		image         (NDArray[Any]):  Image to zoom
		zoom_factor   (float):       Zoom factor (greater than 1 for zoom in, less than 1 for zoom out)
		ignore_dtype  (bool):        Ignore the dtype check
	Returns:
		NDArray[Any]: Zoomed image

	>>> ## Basic tests
	>>> image = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
	>>> zoomed = zoom_image(image.astype(np.uint8), 1.5)
	>>> zoomed.shape == image.shape
	True

	>>> img = np.eye(4, dtype=np.uint8) * 255
	>>> zoomed_in = zoom_image(img, 2.0)
	>>> zoomed_in.shape == img.shape  # Should preserve size
	True

	>>> zoomed_out = zoom_image(img, 0.5)
	>>> zoomed_out.shape == img.shape  # Should preserve size
	True

	>>> rgb = np.full((4,4,3), 128, dtype=np.uint8)
	>>> zoomed_rgb = zoom_image(rgb, 1.5)
	>>> zoomed_rgb.shape == (4,4,3)
	True

	>>> ## Test invalid inputs
	>>> zoom_image("not an image", 1.5)
	Traceback (most recent call last):
		...
	AssertionError: Image must be a numpy array

	>>> zoom_image(image.astype(np.uint8), "1.5")
	Traceback (most recent call last):
		...
	AssertionError: zoom_factor must be a number, got <class 'str'>

	>>> zoom_image(image.astype(np.uint8), -1)
	Traceback (most recent call last):
		...
	AssertionError: zoom_factor must be greater than 0, got -1
	"""
	# Check input data
	check_image(image, ignore_dtype=ignore_dtype)
	assert isinstance(zoom_factor, float | int), f"zoom_factor must be a number, got {type(zoom_factor)}"
	assert zoom_factor > 0, f"zoom_factor must be greater than 0, got {zoom_factor}"

	# Get image dimensions
	height, width = image.shape[:2]

	# Calculate new dimensions
	new_height, new_width = int(height * zoom_factor), int(width * zoom_factor)

	# Resize image
	zoomed_image: NDArray[Any] = cv2.resize(image, (new_width, new_height))

	# Crop or pad to original size
	if zoom_factor > 1:
		# Crop
		start_x: int = (new_width - width) // 2
		start_y: int = (new_height - height) // 2
		return zoomed_image[start_y:start_y + height, start_x:start_x + width] # pyright: ignore [reportUnknownVariableType]
	else:
		# Pad
		pad_x: int = (width - new_width) // 2
		pad_y: int = (height - new_height) // 2
		# Ensure value list matches number of channels (max 4 for OpenCV)
		value: list[int] = [0] * min(image.shape[-1], 4)
		return cv2.copyMakeBorder(zoomed_image, pad_y, pad_y, pad_x, pad_x, cv2.BORDER_CONSTANT, value=value)

