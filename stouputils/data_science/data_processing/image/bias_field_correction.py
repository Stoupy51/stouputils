
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownVariableType=false

# Imports
import SimpleITK as Sitk

from .common import Any, NDArray, check_image, np


# Functions
def bias_field_correction_image(image: NDArray[Any], ignore_dtype: bool = False) -> NDArray[Any]:
	""" Apply a bias field correction to an image. (N4 Filter)

	Args:
		image         (NDArray[Any]):  Image to apply the bias field correction (can't be 8-bit unsigned integer)
		ignore_dtype  (bool):        Ignore the dtype check
	Returns:
		NDArray[Any]: Image with the curvature flow filter applied

	>>> ## Basic tests
	>>> image = np.random.randint(0, 255, size=(10,10), dtype=np.uint8) / 255
	>>> corrected = bias_field_correction_image(image)
	>>> corrected.shape == image.shape
	True
	>>> corrected.dtype == np.float64
	True

	>>> ## Test invalid inputs
	>>> bias_field_correction_image("not an image")
	Traceback (most recent call last):
		...
	AssertionError: Image must be a numpy array
	"""
	# Check input data
	check_image(image, ignore_dtype=ignore_dtype)

	# If the image is 3D, convert to grayscale first
	if image.ndim == 3:
		image = np.mean(image, axis=-1)

	# Convert numpy array to SimpleITK image
	image_sitk: Sitk.Image = Sitk.GetImageFromArray(image)

	# Create binary mask of the head region
	transformed: Sitk.Image = Sitk.RescaleIntensity(image_sitk)  # Normalize intensities
	transformed = Sitk.LiThreshold(transformed, 0, 1)  # Apply Li thresholding
	head_mask: Sitk.Image = transformed

	# Downsample images to speed up bias field estimation
	shrink_factor: int = 4  # Reduce image size by factor of 4
	input_image: Sitk.Image = Sitk.Shrink(
		image_sitk,
		[shrink_factor] * image_sitk.GetDimension()  # Apply shrink factor to all dimensions
	)
	mask_image: Sitk.Image = Sitk.Shrink(
		head_mask,
		[shrink_factor] * image_sitk.GetDimension()
	)

	# Apply N4 bias field correction
	corrector = Sitk.N4BiasFieldCorrectionImageFilter()
	corrector.Execute(input_image, mask_image)

	# Get estimated bias field and apply correction
	log_bias_field: Sitk.Image = Sitk.Cast(
		corrector.GetLogBiasFieldAsImage(image_sitk), Sitk.sitkFloat64
	)
	corrected_image_full_resolution: Sitk.Image = image_sitk / Sitk.Exp(log_bias_field)

	# Convert back to numpy array and return
	return Sitk.GetArrayFromImage(corrected_image_full_resolution)

