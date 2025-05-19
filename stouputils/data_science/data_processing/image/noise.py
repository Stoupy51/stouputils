
# Imports
from .common import Any, NDArray, check_image, np


# Functions
def noise_image(image: NDArray[Any], amount: float, ignore_dtype: bool = False) -> NDArray[Any]:
	""" Add Gaussian noise to an image.

	Args:
		image         (NDArray[Any]):  Image to add noise to
		amount        (float):       Amount of noise to add (between 0 and 1)
		ignore_dtype  (bool):        Ignore the dtype check
	Returns:
		NDArray[Any]: Noisy image

	>>> ## Basic tests
	>>> image = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
	>>> noisy = noise_image(image.astype(np.uint8), 0.5)
	>>> noisy.shape == image.shape
	True
	>>> bool(np.all(noisy >= 0) and np.all(noisy <= 255))
	True

	>>> np.random.seed(0)
	>>> image = np.array([[128] * 3] * 3)
	>>> noise_image(image.astype(np.uint8), 0.1).tolist()
	[[172, 138, 152], [185, 175, 104], [152, 125, 126]]

	>>> rgb = np.full((3,3,3), 128, dtype=np.uint8)
	>>> noisy_rgb = noise_image(rgb, 0.1)
	>>> noisy_rgb.shape == (3,3,3)
	True

	>>> ## Test invalid inputs
	>>> noise_image("not an image", 0.5)
	Traceback (most recent call last):
		...
	AssertionError: Image must be a numpy array

	>>> noise_image(image.astype(np.uint8), "0.5")
	Traceback (most recent call last):
		...
	AssertionError: amount must be a number, got <class 'str'>

	>>> noise_image(image.astype(np.uint8), 1.5)
	Traceback (most recent call last):
		...
	AssertionError: amount must be between 0 and 1, got 1.5
	"""
	# Check input data
	check_image(image, ignore_dtype=ignore_dtype)
	assert isinstance(amount, float | int), f"amount must be a number, got {type(amount)}"
	assert 0 <= amount <= 1, f"amount must be between 0 and 1, got {amount}"

	# Generate noise
	noise: NDArray[Any] = np.random.normal(0, amount * 255, image.shape).astype(np.int16)
	return np.clip(image.astype(np.int16) + noise, 0, 255).astype(image.dtype) # pyright: ignore [reportUnknownMemberType]

