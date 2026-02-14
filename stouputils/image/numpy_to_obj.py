
# Imports
from typing import TYPE_CHECKING, cast

from ..io.path import super_open
from ..print.message import debug, info

if TYPE_CHECKING:
	import numpy as np
	from numpy.typing import NDArray

# Functions
def numpy_to_obj(
	path: str,
	array: "NDArray[np.integer | np.floating | np.bool_]",
	threshold: float = 0.5,
	step_size: int = 1,
	pad_array: bool = True,
	verbose: int = 0
) -> None:
	""" Generate a '.obj' file from a numpy array for 3D visualization using marching cubes.

	Args:
		path      (str):     Path to the output .obj file.
		array     (NDArray): Numpy array to be dumped (must be 3D).
		threshold (float):   Threshold level for marching cubes (0.5 for binary data).
		step_size (int):     Step size for marching cubes (higher = simpler mesh, faster generation).
		pad_array (bool):    If True, pad array with zeros to ensure closed volumes for border cells.
		verbose   (int):     Verbosity level (0 = no output, 1 = some output, 2 = full output).

	Examples:

		.. code-block:: python

			> array = np.random.rand(64, 64, 64) > 0.5  # Binary volume
			> numpy_to_obj("output_mesh.obj", array, threshold=0.5, step_size=2, pad_array=True, verbose=1)

			> array = my_3d_data  # Some 3D numpy array (e.g. human lung scan)
			> numpy_to_obj("output_mesh.obj", array, threshold=0.3)
	"""
	# Imports
	import numpy as np
	from skimage import measure

	# Assertions
	assert array.ndim == 3, f"The input array must be 3D, got shape {array.shape} instead."
	assert step_size > 0, f"Step size must be positive, got {step_size}."
	if verbose > 1:
		debug(
			f"Generating 3D mesh from array of shape {array.shape}, "
			f"threshold={threshold}, step_size={step_size}, pad_array={pad_array}, "
			f"non-zero voxels={np.count_nonzero(array):,}"
		)

	# Convert to float for marching cubes, if needed
	volume: NDArray[np.floating] = array.astype(np.float32)
	if np.issubdtype(array.dtype, np.bool_):
		threshold = 0.5
	elif np.issubdtype(array.dtype, np.integer):
		# For integer arrays, normalize to 0-1 range
		array = array.astype(np.float32)
		min_val, max_val = np.min(array), np.max(array)
		if min_val != max_val:
			volume = (array - min_val) / (max_val - min_val)

	# Pad array with zeros to ensure closed volumes for border cells
	if pad_array:
		volume = np.pad(volume, pad_width=step_size, mode='constant', constant_values=0.0)

	# Apply marching cubes algorithm to extract mesh
	verts, faces, _, _ = cast(
        "tuple[NDArray[np.floating], NDArray[np.integer], NDArray[np.floating], NDArray[np.floating]]",
		measure.marching_cubes(volume, level=threshold, step_size=step_size, allow_degenerate=False) # type: ignore
	)

	# Shift vertices back by step_size to account for padding
	if pad_array:
		verts = verts - step_size

	if verbose > 1:
		debug(f"Generated mesh with {len(verts):,} vertices and {len(faces):,} faces")
		if step_size > 1:
			debug(f"Mesh complexity reduced by ~{step_size ** 3}x compared to step_size=1")

	# Build content using list for better performance
	content_lines: list[str] = [
		"# OBJ file generated from 3D numpy array",
		f"# Array shape: {array.shape}",
		f"# Threshold: {threshold}",
		f"# Step size: {step_size}",
		f"# Vertices: {len(verts)}",
		f"# Faces: {len(faces)}",
		""
	]

	# Add vertices
	content_lines.extend(f"v {a:.6f} {b:.6f} {c:.6f}" for a, b, c in verts)

	# Add faces (OBJ format is 1-indexed, simple format without normals)
	content_lines.extend(f"f {a+1} {b+1} {c+1}" for a, b, c in faces)

	# Write to .obj file
	with super_open(path, "w") as f:
		f.write("\n".join(content_lines) + "\n")

	if verbose > 0:
		info(f"Successfully exported 3D mesh to: '{path}'")

