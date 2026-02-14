
# Imports
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
	import numpy as np
	from numpy.typing import NDArray
	from PIL import Image

# Functions
def image_resize[T: "Image.Image | NDArray[np.number]"](
	image: T,
	max_result_size: int,
	resampling: "Image.Resampling | None" = None,
	min_or_max: Callable[[int, int], int] = max,
	return_type: type[T] | str = "same",
	keep_aspect_ratio: bool = True,
) -> Any:
	""" Resize an image while preserving its aspect ratio by default.
	Scales the image so that its largest dimension equals max_result_size.

	Args:
		image             (Image.Image | NDArray):    The image to resize.
		max_result_size   (int):                      Maximum size for the largest dimension.
		resampling        (Image.Resampling | None):  PIL resampling filter to use (default: Image.Resampling.LANCZOS).
		min_or_max        (Callable):                 Function to use to get the minimum or maximum of the two ratios.
		return_type       (type | str):               Type of the return value (Image.Image, np.ndarray, or "same" to match input type).
		keep_aspect_ratio (bool):                     Whether to keep the aspect ratio.
	Returns:
		Image.Image | NDArray[np.number]: The resized image with preserved aspect ratio.
	Examples:
		>>> # Test with (height x width x channels) numpy array
		>>> import numpy as np
		>>> array = np.random.randint(0, 255, (100, 50, 3), dtype=np.uint8)
		>>> image_resize(array, 100).shape
		(100, 50, 3)
		>>> image_resize(array, 100, min_or_max=max).shape
		(100, 50, 3)
		>>> image_resize(array, 100, min_or_max=min).shape
		(200, 100, 3)

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
	# Imports
	import numpy as np
	from PIL import Image

	# Set default resampling method if not provided
	if resampling is None:
		resampling = Image.Resampling.LANCZOS

	# Store original type for later conversion
	original_was_pil: bool = isinstance(image, Image.Image)

	# Convert numpy array to PIL Image if needed
	if not original_was_pil:
		image = Image.fromarray(image) # type: ignore

	if keep_aspect_ratio:

		# Get original image dimensions
		width: int = image.size[0]
		height: int = image.size[1]

		# Determine which dimension to use for scaling based on min_or_max function
		max_dimension: int = min_or_max(width, height)

		# Calculate scaling factor
		scale: float = max_result_size / max_dimension

		# Calculate new dimensions while preserving aspect ratio
		new_width: int = int(width * scale)
		new_height: int = int(height * scale)

		# Resize the image with the calculated dimensions
		new_image: Image.Image = image.resize((new_width, new_height), resampling)
	else:
		# If not keeping aspect ratio, resize to square with max_result_size
		new_image: Image.Image = image.resize((max_result_size, max_result_size), resampling)

	# Return the image in the requested format
	if return_type == "same":
		# Return same type as input
		if original_was_pil:
			return new_image
		else:
			return np.array(new_image)
	elif return_type != Image.Image:
		return np.array(new_image)
	else:
		return new_image

