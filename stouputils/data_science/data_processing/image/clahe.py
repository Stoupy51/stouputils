
# pyright: reportUnusedImport=false
# ruff: noqa: F401

# Imports
from .common import Any, NDArray, check_image, cv2, np


# Functions
def clahe_image(
	image: NDArray[Any],
	clip_limit: float = 2.0,
	tile_grid_size: int = 8,
	ignore_dtype: bool = False,
) -> NDArray[Any]:
	""" Apply Contrast Limited Adaptive Histogram Equalization (CLAHE) to an image.

	Args:
		image           (NDArray[Any]):  Image to apply CLAHE to
		clip_limit      (float):       Threshold for contrast limiting (1.0-4.0 recommended)
		tile_grid_size  (int):         Size of grid for histogram equalization (2-16 recommended)
		ignore_dtype    (bool):        Ignore the dtype check
	Returns:
		NDArray[Any]: Image with CLAHE applied

	>>> ## Basic tests
	>>> image = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
	>>> clahed = clahe_image(image.astype(np.uint8), 2.0, 1)
	>>> clahed.tolist()
	[[28, 57, 85], [113, 142, 170], [198, 227, 255]]
	>>> clahed.shape == image.shape
	True

	>>> img = np.full((10,10), 128, dtype=np.uint8)
	>>> img[2:8, 2:8] = 200  # Create a bright region
	>>> clahed = clahe_image(img, 2.0, 4)
	>>> bool(np.mean(clahed) > np.mean(img))  # Should enhance contrast
	True
	>>> bool(np.std(clahed) > np.std(img))  # Should enhance contrast
	True

	>>> rgb = np.full((10,10,3), 128, dtype=np.uint8)
	>>> rgb[2:8, 2:8, :] = 50  # Create a dark region
	>>> clahed_rgb = clahe_image(rgb, 2.0, 4)
	>>> bool(np.mean(clahed_rgb) > np.mean(rgb))  # Should enhance contrast
	True
	>>> bool(np.std(clahed_rgb) > np.std(rgb))  # Should enhance contrast
	True
	>>> clahed_rgb.shape == rgb.shape
	True

	>>> ## Test invalid inputs
	>>> clahe_image("not an image", 2.0, 8)
	Traceback (most recent call last):
		...
	AssertionError: Image must be a numpy array

	>>> clahe_image(image.astype(np.uint8), "2.0", 8)
	Traceback (most recent call last):
		...
	AssertionError: clip_limit must be a number, got <class 'str'>

	>>> clahe_image(image.astype(np.uint8), 2.0, -1)
	Traceback (most recent call last):
		...
	AssertionError: tile_grid_size must be positive, got -1
	"""
	# Check input data
	check_image(image, ignore_dtype=ignore_dtype)
	assert isinstance(clip_limit, float | int), f"clip_limit must be a number, got {type(clip_limit)}"
	assert isinstance(tile_grid_size, int), f"tile_grid_size must be an integer, got {type(tile_grid_size)}"
	assert tile_grid_size > 0, f"tile_grid_size must be positive, got {tile_grid_size}"

	# Create CLAHE object
	clahe: cv2.CLAHE = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_grid_size, tile_grid_size))

	# Handle different image types
	if len(image.shape) == 2:
		# Grayscale image
		return clahe.apply(image)
	else:
		# Color image - convert to LAB color space
		lab: NDArray[Any] = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
		channel_l, channel_a, channel_b = cv2.split(lab)

		# Apply CLAHE to L channel
		cl: NDArray[Any] = clahe.apply(channel_l)

		# Merge channels and convert back to BGR
		limg: NDArray[Any] = cv2.merge((cl, channel_a, channel_b))
		return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

