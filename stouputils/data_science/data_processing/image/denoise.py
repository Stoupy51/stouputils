
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false

# Imports
from typing import Literal

from .common import Any, NDArray, check_image, cv2, np
from ....ctx import Muffle


# Functions
def nlm_denoise_image(
	image: NDArray[Any],
	h: float = 10,
	template_window_size: int = 7,
	search_window_size: int = 21,
	ignore_dtype: bool = False
) -> NDArray[Any]:
	""" Apply Non-Local Means denoising to an image.

	This algorithm replaces each pixel with an average of similar pixels
	found anywhere in the image. It is highly effective for removing Gaussian noise
	while preserving edges and details.

	Args:
		image                  (NDArray[Any]):  Image to denoise
		h                      (float):       Filter strength (higher values remove more noise but may blur details)
		template_window_size   (int):         Size of the template window for patch comparison (should be odd)
		search_window_size     (int):         Size of the search window (should be odd)
		ignore_dtype           (bool):        Ignore the dtype check
	Returns:
		NDArray[Any]: Denoised image

	>>> ## Basic tests
	>>> image = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
	>>> denoised = nlm_denoise_image(image.astype(np.uint8), 10, 3, 5)
	>>> denoised.shape == image.shape
	True

	>>> ## Test with colored image
	>>> rgb = np.random.randint(0, 256, (10, 10, 3), dtype=np.uint8)
	>>> denoised_rgb = nlm_denoise_image(rgb, 10, 5, 11)
	>>> denoised_rgb.shape == rgb.shape
	True

	>>> ## Test invalid inputs
	>>> nlm_denoise_image("not an image", 10)
	Traceback (most recent call last):
		...
	AssertionError: Image must be a numpy array

	>>> nlm_denoise_image(image.astype(np.uint8), "10")
	Traceback (most recent call last):
		...
	AssertionError: h must be a number, got <class 'str'>

	>>> nlm_denoise_image(image.astype(np.uint8), 10, 4)
	Traceback (most recent call last):
		...
	AssertionError: template_window_size must be odd, got 4
	"""
	# Check input data
	check_image(image, ignore_dtype=ignore_dtype)
	assert isinstance(h, float | int), f"h must be a number, got {type(h)}"
	assert template_window_size % 2 == 1, f"template_window_size must be odd, got {template_window_size}"
	assert search_window_size % 2 == 1, f"search_window_size must be odd, got {search_window_size}"

	# Apply Non-Local Means denoising based on image type
	if len(image.shape) == 2 or image.shape[2] == 1:  # Grayscale
		return cv2.fastNlMeansDenoising(
			image, None, float(h), template_window_size, search_window_size
		)
	else:  # Color
		return cv2.fastNlMeansDenoisingColored(
			image, None, float(h), float(h), template_window_size, search_window_size
		)


def bilateral_denoise_image(
	image: NDArray[Any],
	d: int = 9,
	sigma_color: float = 75,
	sigma_space: float = 75,
	ignore_dtype: bool = False
) -> NDArray[Any]:
	""" Apply Bilateral Filter denoising to an image.

	Bilateral filtering smooths images while preserving edges by considering
	both spatial proximity and color similarity between pixels.

	Args:
		image         (NDArray[Any]):  Image to denoise
		d             (int):         Diameter of each pixel neighborhood
		sigma_color   (float):       Filter sigma in the color space
		sigma_space   (float):       Filter sigma in the coordinate space
		ignore_dtype  (bool):        Ignore the dtype check
	Returns:
		NDArray[Any]: Denoised image

	>>> ## Basic tests
	>>> image = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
	>>> denoised = bilateral_denoise_image(image.astype(np.uint8))
	>>> denoised.shape == image.shape
	True

	>>> ## Test with colored image
	>>> rgb = np.random.randint(0, 256, (10, 10, 3), dtype=np.uint8)
	>>> denoised_rgb = bilateral_denoise_image(rgb)
	>>> denoised_rgb.shape == rgb.shape
	True

	>>> ## Test invalid inputs
	>>> bilateral_denoise_image("not an image")
	Traceback (most recent call last):
		...
	AssertionError: Image must be a numpy array

	>>> bilateral_denoise_image(image.astype(np.uint8), "9")
	Traceback (most recent call last):
		...
	AssertionError: d must be a number, got <class 'str'>
	"""
	# Check input data
	check_image(image, ignore_dtype=ignore_dtype)
	assert isinstance(d, int), f"d must be a number, got {type(d)}"
	assert isinstance(sigma_color, float | int), f"sigma_color must be a number, got {type(sigma_color)}"
	assert isinstance(sigma_space, float | int), f"sigma_space must be a number, got {type(sigma_space)}"

	# Apply bilateral filter
	return cv2.bilateralFilter(image, d, sigma_color, sigma_space)


def tv_denoise_image(
	image: NDArray[Any],
	weight: float = 0.1,
	iterations: int = 30,
	method: Literal["chambolle", "bregman"] = "chambolle",
	ignore_dtype: bool = False
) -> NDArray[Any]:
	""" Apply Total Variation denoising to an image.

	Total Variation denoising removes noise while preserving sharp edges by
	minimizing the total variation of the image.

	Args:
		image         (NDArray[Any]):  Image to denoise
		weight        (float):       Denoising weight (higher values remove more noise)
		iterations    (int):         Number of iterations
		method        (str):         Method to use ("chambolle" or "bregman")
		ignore_dtype  (bool):        Ignore the dtype check
	Returns:
		NDArray[Any]: Denoised image

	>>> ## Basic tests
	>>> image = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
	>>> denoised = tv_denoise_image(image.astype(np.uint8), 0.1, 30)
	>>> denoised.shape == image.shape
	True

	>>> ## Test invalid inputs
	>>> tv_denoise_image("not an image")
	Traceback (most recent call last):
		...
	AssertionError: Image must be a numpy array

	>>> tv_denoise_image(image.astype(np.uint8), "0.1")
	Traceback (most recent call last):
		...
	AssertionError: weight must be a number, got <class 'str'>
	"""
	# Check input data
	check_image(image, ignore_dtype=ignore_dtype)
	assert isinstance(weight, float | int), f"weight must be a number, got {type(weight)}"
	assert isinstance(iterations, int), f"iterations must be an integer, got {type(iterations)}"
	assert method in ["chambolle", "bregman"], f"method must be 'chambolle' or 'bregman', got {method}"

	# Import skimage for TV denoising
	try:
		from skimage.restoration import denoise_tv_bregman, denoise_tv_chambolle
	except ImportError as e:
		raise ImportError("scikit-image is required for TV denoising. Install with 'pip install scikit-image'") from e

	# Normalize image to [0, 1] for skimage functions
	is_int_type = np.issubdtype(image.dtype, np.integer)
	if is_int_type:
		img_norm = image.astype(np.float32) / 255.0
	else:
		img_norm = image.astype(np.float32)

	# Apply TV denoising based on method
	if method == "chambolle":
		denoised = denoise_tv_chambolle(
			img_norm,
			weight=weight,
			max_num_iter=iterations,
			channel_axis=-1 if len(image.shape) > 2 else None
		)
	else:
		denoised = denoise_tv_bregman(
			img_norm,
			weight=weight,
			max_num_iter=iterations,
			channel_axis=-1 if len(image.shape) > 2 else None
		)

	# Convert back to original data type
	if is_int_type:
		denoised = np.clip(denoised * 255, 0, 255).astype(image.dtype)
	else:
		denoised = denoised.astype(image.dtype)

	return denoised


def wavelet_denoise_image(
	image: NDArray[Any],
	sigma: float | None = None,
	wavelet: str = 'db1',
	mode: str = 'soft',
	wavelet_levels: int = 3,
	ignore_dtype: bool = False
) -> NDArray[Any]:
	""" Apply Wavelet denoising to an image.

	Wavelet denoising decomposes the image into wavelet coefficients,
	applies thresholding, and reconstructs the image with reduced noise.

	Args:
		image          (NDArray[Any]):  Image to denoise
		sigma          (float):       Noise standard deviation. If None, it's estimated from the image.
		wavelet        (str):         Wavelet to use
		mode           (str):         Thresholding mode ('soft' or 'hard')
		wavelet_levels (int):         Number of wavelet decomposition levels
		ignore_dtype   (bool):        Ignore the dtype check
	Returns:
		NDArray[Any]: Denoised image

	>>> ## Basic tests
	>>> import importlib.util
	>>> has_pywt = importlib.util.find_spec('pywt') is not None
	>>> image = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
	>>> if has_pywt:
	...     denoised = wavelet_denoise_image(image.astype(np.uint8))
	...     denoised.shape == image.shape
	... else:
	...     True
	True

	>>> ## Test invalid inputs
	>>> wavelet_denoise_image("not an image")
	Traceback (most recent call last):
		...
	AssertionError: Image must be a numpy array

	>>> wavelet_denoise_image(image.astype(np.uint8), wavelet=123)
	Traceback (most recent call last):
		...
	AssertionError: wavelet must be a string, got <class 'int'>
	"""
	# Check input data
	check_image(image, ignore_dtype=ignore_dtype)
	if sigma is not None:
		assert isinstance(sigma, float | int), f"sigma must be a number or None, got {type(sigma)}"
	assert isinstance(wavelet, str), f"wavelet must be a string, got {type(wavelet)}"
	assert mode in ["soft", "hard"], f"mode must be 'soft' or 'hard', got {mode}"
	assert isinstance(wavelet_levels, int), f"wavelet_levels must be an integer, got {type(wavelet_levels)}"

	# Import skimage for wavelet denoising
	try:
		from skimage.restoration import denoise_wavelet

		# Check for PyWavelets dependency specifically
		try:
			import pywt  # type: ignore
		except ImportError as e:
			raise ImportError(
				"PyWavelets (pywt) is required for wavelet denoising. Install with 'pip install PyWavelets'", name="pywt"
			) from e
	except ImportError as e:
		if e.name != "pywt":
			raise ImportError("skimage is required for wavelet denoising. Install with 'pip install scikit-image'") from e
		else:
			raise e

	# Normalize image to [0, 1] for skimage functions
	is_int_type = np.issubdtype(image.dtype, np.integer)
	if is_int_type:
		img_norm = image.astype(np.float32) / 255.0
	else:
		img_norm = image.astype(np.float32)

	# Apply wavelet denoising
	with Muffle(mute_stderr=True):
		denoised = denoise_wavelet(
			img_norm, sigma=sigma, wavelet=wavelet, mode=mode,
			wavelet_levels=wavelet_levels, channel_axis=-1 if len(image.shape) > 2 else None
		)

	# Convert back to original data type
	if is_int_type:
		denoised = np.clip(denoised * 255, 0, 255).astype(image.dtype)
	else:
		denoised = denoised.astype(image.dtype)

	return denoised


def adaptive_denoise_image(
	image: NDArray[Any],
	method: Literal["nlm", "bilateral", "tv", "wavelet"] | str = "nlm",
	strength: float = 0.5,
	ignore_dtype: bool = False
) -> NDArray[Any]:
	""" Apply adaptive denoising to an image using the specified method.

	This is a convenience function that selects the appropriate denoising method
	and parameters based on the image content and noise level.

	Args:
		image         (NDArray[Any]):  Image to denoise
		method        (str):         Denoising method to use ("nlm", "bilateral", "tv", or "wavelet")
		strength      (float):       Denoising strength (0.0 to 1.0)
		ignore_dtype  (bool):        Ignore the dtype check
	Returns:
		NDArray[Any]: Denoised image

	>>> ## Basic tests
	>>> image = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
	>>> denoised = adaptive_denoise_image(image.astype(np.uint8), "nlm", 0.5)
	>>> denoised.shape == image.shape
	True

	>>> ## Test invalid inputs
	>>> adaptive_denoise_image("not an image")
	Traceback (most recent call last):
		...
	AssertionError: Image must be a numpy array

	>>> adaptive_denoise_image(image.astype(np.uint8), "invalid_method")
	Traceback (most recent call last):
		...
	AssertionError: method must be one of: nlm, bilateral, tv, wavelet
	"""
	# Check input data
	check_image(image, ignore_dtype=ignore_dtype)
	valid_methods = ["nlm", "bilateral", "tv", "wavelet"]
	assert method in valid_methods, f"method must be one of: {', '.join(valid_methods)}"
	assert isinstance(strength, float | int), f"strength must be a number, got {type(strength)}"
	assert 0 <= strength <= 1, f"strength must be between 0 and 1, got {strength}"

	# Scale parameters based on strength
	if method == "bilateral":
		# sigma parameters scale from 30 (minimal) to 150 (strong)
		sigma = 30 + strength * 120
		return bilateral_denoise_image(
			image, d=9, sigma_color=sigma, sigma_space=sigma, ignore_dtype=ignore_dtype
		)

	elif method == "tv":
		# weight scales from 0.05 (minimal) to 0.5 (strong)
		weight = 0.05 + strength * 0.45
		return tv_denoise_image(
			image, weight=weight, iterations=30, ignore_dtype=ignore_dtype
		)

	elif method == "wavelet":
		# We'll estimate sigma from the image, but scale wavelet levels
		wavelet_levels = max(2, min(5, int(2 + strength * 3)))
		return wavelet_denoise_image(
			image, wavelet_levels=wavelet_levels, ignore_dtype=ignore_dtype
		)

	else:
		# h parameter scales from 5 (minimal) to 20 (strong)
		h = 5 + strength * 15
		return nlm_denoise_image(image, h=h, ignore_dtype=ignore_dtype)
