
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportAttributeAccessIssue=false
# pyright: reportArgumentType=false
# pyright: reportCallIssue=false

# Imports
from .common import Any, NDArray, check_image, cv2, np


# Functions
def laplacian_image(image: NDArray[Any], kernel_size: int = 3, ignore_dtype: bool = False) -> NDArray[Any]:
	""" Apply Laplacian edge detection to an image.

	Args:
		image         (NDArray[Any]):  Image to apply Laplacian edge detection
		kernel_size   (int):         Size of the kernel (must be odd)
		ignore_dtype  (bool):        Ignore the dtype check
	Returns:
		NDArray[Any]: Image with Laplacian edge detection applied

	>>> ## Basic tests
	>>> image = np.array([[100, 150, 200], [50, 125, 175], [25, 75, 225]])
	>>> edges = laplacian_image(image.astype(np.uint8))
	>>> edges.shape == image.shape[:2]  # Laplacian returns single channel
	True

	>>> rgb = np.random.randint(0, 256, (3,3,3), dtype=np.uint8)
	>>> edges_rgb = laplacian_image(rgb)
	>>> edges_rgb.shape == rgb.shape[:2]  # Laplacian returns single channel
	True

	>>> ## Test invalid inputs
	>>> laplacian_image("not an image")
	Traceback (most recent call last):
		...
	AssertionError: Image must be a numpy array

	>>> laplacian_image(image.astype(np.uint8), kernel_size=2)
	Traceback (most recent call last):
		...
	AssertionError: kernel_size must be odd, got 2
	"""
	# Check input data
	check_image(image, ignore_dtype=ignore_dtype)
	assert kernel_size % 2 == 1, f"kernel_size must be odd, got {kernel_size}"

	# Convert to grayscale if needed
	if len(image.shape) > 2:
		image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

	# Apply Laplacian edge detection
	laplacian: NDArray[Any] = cv2.Laplacian(image, cv2.CV_64F, ksize=kernel_size)

	# Convert back to uint8 and normalize to 0-255 range
	normalized: NDArray[Any] = cv2.normalize(laplacian, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
	return normalized.astype(np.uint8)

