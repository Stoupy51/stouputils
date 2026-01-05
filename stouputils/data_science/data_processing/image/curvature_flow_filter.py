
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnusedImport=false
# ruff: noqa: F401

# Imports
import SimpleITK as Sitk

from .common import Any, NDArray, check_image, np


# Functions
def curvature_flow_filter_image(
	image: NDArray[Any],
	time_step: float = 0.05,
	number_of_iterations: int = 5,
	ignore_dtype: bool = False,
) -> NDArray[Any]:
	""" Apply a curvature flow filter to an image.

	Args:
		image                (NDArray[Any]):  Image to apply the curvature flow filter
		time_step            (float):       Time step for the curvature flow filter
		number_of_iterations (int):         Number of iterations for the curvature flow filter
		ignore_dtype         (bool):        Ignore the dtype check
	Returns:
		NDArray[Any]: Image with the curvature flow filter applied

	>>> ## Basic tests
	>>> image = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]], dtype=np.uint8)
	>>> filtered = curvature_flow_filter_image(image, 0.05, 5)
	>>> filtered.tolist()[0][0]
	1.2910538407309702
	>>> filtered.shape == image.shape
	True
	>>> filtered.dtype == image.dtype
	False

	>>> rgb = np.full((3,3,3), 128, dtype=np.uint8)
	>>> rgb[1,1] = [50, 100, 150]
	>>> filtered_rgb = curvature_flow_filter_image(rgb, 0.05, 5)
	>>> filtered_rgb.shape == (3,3,3)
	True

	>>> ## Test invalid inputs
	>>> curvature_flow_filter_image("not an image")
	Traceback (most recent call last):
		...
	AssertionError: Image must be a numpy array

	>>> curvature_flow_filter_image(image, time_step="not a float")
	Traceback (most recent call last):
		...
	AssertionError: time_step must be a float

	>>> curvature_flow_filter_image(image, number_of_iterations="not an integer")
	Traceback (most recent call last):
		...
	AssertionError: number_of_iterations must be an integer
	"""
	# Check input data
	check_image(image, ignore_dtype=ignore_dtype)
	assert isinstance(time_step, float), "time_step must be a float"
	assert isinstance(number_of_iterations, int), "number_of_iterations must be an integer"
	assert time_step > 0, "time_step must be greater than 0"
	assert number_of_iterations > 0, "number_of_iterations must be greater than 0"

	# Apply the curvature flow filter
	image_Sitk: Sitk.Image = Sitk.GetImageFromArray(image)
	image_Sitk = Sitk.CurvatureFlow(image_Sitk, timeStep=time_step, numberOfIterations=number_of_iterations)
	return Sitk.GetArrayFromImage(image_Sitk)

