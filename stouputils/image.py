
# Imports
from PIL import Image
from typing import Callable
from numpy.typing import NDArray
import numpy as np


# Functions
def image_resize(
	image: Image.Image | NDArray[np.uint8],
	max_result_size: int,
	resampling: Image.Resampling = Image.Resampling.LANCZOS,
	min_or_max: Callable[[int, int], int] = max,
	return_type: type[Image.Image | NDArray[np.uint8]] = Image.Image,
) -> Image.Image | NDArray[np.uint8]:
	""" Resize an image while preserving its aspect ratio.
	Scales the image so that its largest dimension equals max_result_size.
	
	Args:
		image             (Image.Image | np.ndarray): The image to resize.
		max_result_size   (int):                      Maximum size for the largest dimension.
		resampling        (Image.Resampling):         PIL resampling filter to use.
		min_or_max        (Callable):                 Function to use to get the minimum or maximum of the two ratios.
		return_type       (type):                     Type of the return value (Image.Image or np.ndarray).
	Returns:
		Image.Image: The resized image with preserved aspect ratio.
	Examples:
		>>> # Test with (height x width x channels) numpy array
		>>> import numpy as np
		>>> array: np.ndarray = np.random.randint(0, 255, (100, 50, 3), dtype=np.uint8)
		>>> image_resize(array, 100).size
		(50, 100)
		>>> image_resize(array, 100, min_or_max=max).size
		(50, 100)
		>>> image_resize(array, 100, min_or_max=min).size
		(100, 200)

		>>> # Test with PIL Image
		>>> from PIL import Image
		>>> pil_image: Image.Image = Image.new('RGB', (200, 100))
		>>> image_resize(pil_image, 50).size
		(50, 25)
		>>> # Test with different return types
		>>> resized_array = image_resize(array, 50, return_type=np.ndarray)
		>>> isinstance(resized_array, np.ndarray)
		True
		>>> resized_array.shape
		(50, 25, 3)
		>>> # Test with different resampling methods
		>>> image_resize(pil_image, 50, resampling=Image.Resampling.NEAREST).size
		(50, 25)
	"""
	if isinstance(image, np.ndarray):
		image = Image.fromarray(image)	# type: ignore

	width: int = image.size[0]
	height: int = image.size[1]
	max_dimension: int = min_or_max(width, height)
	scale: float = max_result_size / max_dimension
	
	new_width: int = int(width * scale)
	new_height: int = int(height * scale)
	new_image: Image.Image = image.resize((new_width, new_height), resampling)
	
	if return_type == np.ndarray:
		return np.array(new_image)
	else:
		return new_image

