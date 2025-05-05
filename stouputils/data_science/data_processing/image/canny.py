
# Imports
from .common import Any, NDArray, check_image, cv2, np


# Functions
def canny_image(
	image: NDArray[Any],
	threshold1: float,
	threshold2: float,
	aperture_size: int = 3,
	sigma: float = 3,
	stop_at_nms: bool = False,
	ignore_dtype: bool = False,
) -> NDArray[Any]:
	""" Apply Canny edge detection to an image.

	Args:
		image           (NDArray[Any]):  Image to apply Canny edge detection
		threshold1      (float):       First threshold for hysteresis (between 0 and 1)
		threshold2      (float):       Second threshold for hysteresis (between 0 and 1)
		aperture_size   (int):         Aperture size for Sobel operator (3, 5, or 7)
		sigma           (float):       Standard deviation for Gaussian blur
		stop_at_nms     (bool):        Stop at non-maximum suppression step (don't apply thresholding)
		ignore_dtype    (bool):        Ignore the dtype check
	Returns:
		NDArray[Any]: Image with Canny edge detection applied

	>>> ## Basic tests
	>>> image = np.array([[100, 150, 200], [50, 125, 175], [25, 75, 225]])
	>>> edges = canny_image(image.astype(np.uint8), 0.1, 0.2)
	>>> edges.shape == image.shape[:2]  # Canny returns single channel
	True
	>>> set(np.unique(edges).tolist()) <= {0, 255}  # Only contains 0 and 255
	True

	>>> rgb = np.random.randint(0, 256, (3,3,3), dtype=np.uint8)
	>>> edges_rgb = canny_image(rgb, 0.1, 0.2)
	>>> edges_rgb.shape == rgb.shape[:2]  # Canny returns single channel
	True

	>>> ## Test invalid inputs
	>>> canny_image("not an image", 0.1, 0.2)
	Traceback (most recent call last):
		...
	AssertionError: Image must be a numpy array

	>>> canny_image(image.astype(np.uint8), 1.5, 0.2)
	Traceback (most recent call last):
		...
	AssertionError: threshold1 must be between 0 and 1, got 1.5
	"""
	# Check input data
	check_image(image, ignore_dtype=ignore_dtype)
	assert 0 <= threshold1 <= 1, f"threshold1 must be between 0 and 1, got {threshold1}"
	assert 0 <= threshold2 <= 1, f"threshold2 must be between 0 and 1, got {threshold2}"
	assert aperture_size in (3, 5, 7), f"aperture_size must be 3, 5 or 7, got {aperture_size}"

	# Convert to grayscale if needed
	if len(image.shape) > 2:
		image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

	# Convert thresholds to 0-255 range
	t1: int = int(threshold1 * 255)
	t2: int = int(threshold2 * 255)

	if not stop_at_nms:
		# Apply full Canny edge detection
		return cv2.Canny(image, t1, t2, apertureSize=aperture_size)
	else:
		# Manual implementation up to non-maximum suppression
		# 1. Apply Gaussian blur to reduce noise
		blurred: NDArray[Any] = cv2.GaussianBlur(image, (5, 5), sigma)

		# 2. Calculate gradients using Sobel
		# Use constant value 6 for 64-bit float depth (CV_64F)
		gx: NDArray[Any] = cv2.Sobel(blurred, 6, 1, 0, ksize=aperture_size)
		gy: NDArray[Any] = cv2.Sobel(blurred, 6, 0, 1, ksize=aperture_size)

		# Calculate gradient magnitude and direction
		magnitude: NDArray[Any] = np.sqrt(gx**2 + gy**2)
		direction: NDArray[Any] = np.arctan2(gy, gx) * 180 / np.pi

		# 3. Non-maximum suppression
		nms: NDArray[Any] = np.zeros_like(magnitude, dtype=np.uint8)
		height, width = magnitude.shape

		for i in range(1, height - 1):
			for j in range(1, width - 1):
				# Get gradient direction
				angle: float = direction[i, j]
				if angle < 0:
					angle += 180

				# Round to 0, 45, 90, or 135 degrees
				if (0 <= angle < 22.5) or (157.5 <= angle <= 180):
					neighbors = [magnitude[i, j-1], magnitude[i, j+1]]
				elif 22.5 <= angle < 67.5:
					neighbors = [magnitude[i-1, j-1], magnitude[i+1, j+1]]
				elif 67.5 <= angle < 112.5:
					neighbors = [magnitude[i-1, j], magnitude[i+1, j]]
				else:  # 112.5 <= angle < 157.5
					neighbors = [magnitude[i-1, j+1], magnitude[i+1, j-1]]

				# Check if current pixel is local maximum
				if magnitude[i, j] >= max(neighbors):
					nms[i, j] = np.uint8(min(magnitude[i, j], 255))

		return nms

