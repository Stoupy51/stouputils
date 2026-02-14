
# Imports
import os
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
	import numpy as np
	from numpy.typing import NDArray

# Functions
def numpy_to_gif(
	path: str,
	array: "NDArray[np.integer | np.floating | np.bool_]",
	duration: int = 100,
	loop: int = 0,
	mkdir: bool = True,
	**kwargs: Any
) -> None:
	""" Generate a '.gif' file from a numpy array for 3D/4D visualization.

	Args:
		path     (str):     Path to the output .gif file.
		array    (NDArray): Numpy array to be dumped (must be 3D or 4D).
			3D: (depth, height, width) - e.g. (64, 1024, 1024)
			4D: (depth, height, width, channels) - e.g. (50, 64, 1024, 3)
		duration (int):     Duration between frames in milliseconds.
		loop     (int):     Number of loops (0 = infinite).
		mkdir    (bool):    Create the directory if it does not exist.
		**kwargs (Any):     Additional keyword arguments for PIL.Image.save().

	Examples:

		.. code-block:: python

			> # 3D array example
			> array = np.random.randint(0, 256, (10, 100, 100), dtype=np.uint8)
			> numpy_to_gif("output_10_frames_100x100.gif", array, duration=200, loop=0)

			> # 4D array example (batch of 3D images)
			> array_4d = np.random.randint(0, 256, (5, 10, 100, 3), dtype=np.uint8)
			> numpy_to_gif("output_50_frames_100x100.gif", array_4d, duration=200)

			> total_duration = 1000  # 1 second
			> numpy_to_gif("output_1s.gif", array, duration=total_duration // len(array))
	"""
	# Imports
	import numpy as np
	from PIL import Image

	# Assertions
	assert array.ndim in (3, 4), f"The input array must be 3D or 4D, got shape {array.shape} instead."
	if array.ndim == 4:
		assert array.shape[-1] in (1, 3), f"For 4D arrays, the last dimension must be 1 or 3 (channels), got shape {array.shape} instead."

	# Create directory if needed
	if mkdir:
		dirname: str = os.path.dirname(path)
		if dirname != "":
			os.makedirs(dirname, exist_ok=True)

	# Normalize array if outside [0-255] range to [0-1]
	array = array.astype(np.float32)
	mini, maxi = np.min(array), np.max(array)
	if mini < 0 or maxi > 255:
		array = ((array - mini) / (maxi - mini + 1e-8))

	# Scale to [0-255] if in [0-1] range
	mini, maxi = np.min(array), np.max(array)
	if mini >= 0.0 and maxi <= 1.0:
		array = (array * 255)

	# Ensure array is uint8 for PIL compatibility
	array = array.astype(np.uint8)

	# Convert each slice to PIL Image
	pil_images: list[Image.Image] = [
		Image.fromarray(z_slice)
		for z_slice in array
	]

	# Save as GIF
	pil_images[0].save(
		path,
		save_all=True,
		append_images=pil_images[1:],
		duration=duration,
		loop=loop,
		**kwargs
	)

