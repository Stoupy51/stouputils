
# Imports
import os
from typing import TYPE_CHECKING, Any

from ..io.path import super_open
from ..print.message import debug, info
from ..typing import is_generic_instance
from .numpy_to_obj import extract_verts_faces_from_segment

if TYPE_CHECKING:
	from numpy.typing import NDArray

# Functions
def add_default_colors_to_segments(
	segments: "list[NDArray[Any]]",
	skip_unique_color: bool = False
) -> "list[tuple[NDArray[Any], tuple[float, float, float, float]]]":
	""" Ensure all segments have an associated RGB color. If a segment is provided as a bare array, assign it a default color.

	Args:
		segments (list): List of segments, where each segment is either a 3D array or a tuple of (array, rgba_color).
		skip_unique_color (bool): If True, do not assign a unique color to the first segment.
	Returns:
		list[tuple[NDArray, tuple[float, float, float, float]]]: List of segments as (array, rgba_color) tuples, with default colors assigned where needed.
	"""
	from ..config import StouputilsConfig
	cycle = StouputilsConfig.SEGMENTS_COLOR_CYCLE
	colored_segments: list[tuple[NDArray[Any], tuple[float, float, float, float]]] = []
	for idx, seg in enumerate(segments):
		if not skip_unique_color:
			color = StouputilsConfig.SEGMENTS_UNIQUE_COLOR if idx == 0 else cycle[(idx - 1) % len(cycle)]
		else:
			color = cycle[idx % len(cycle)]
		colored_segments.append((seg, color))
	return colored_segments

def numpy_segments_to_obj(
	path: str,
	segments: "list[tuple[NDArray[Any], tuple[float, float, float, float]]] | list[NDArray[Any]]",
	spacing: tuple[float, float, float] = (1.0, 1.0, 1.0),
	threshold: float = 0.5,
	step_size: int = 1,
	pad_array: bool = True,
	verbose: int = 0
) -> None:
	""" Generate a '.obj' file from multiple segmentation arrays, each with its own color.

	Args:
		path      (str):  Path to the output .obj file (a .mtl file is created alongside it).
		segments  (list): List of (array, rgb_color) tuples. Each array is a 3D segmentation mask.
			RGB values should be floats in [0.0, 1.0].
		spacing   (tuple): Voxel spacing along each axis, passed to marching cubes.
		threshold (float): Iso-surface threshold for marching cubes (0.5 for binary masks).
		step_size (int):   Step size for marching cubes (higher = coarser mesh, faster).
		pad_array (bool):  Pad each array with zeros to close border surfaces.
		verbose   (int):   Verbosity level.
	Examples:
		.. code-block:: python
			> numpy_segments_to_obj(
			>     "brain_segs.obj",
			>     segments=[
			>         (white_matter, (1.0, 1.0, 1.0)),
			>         (grey_matter,  (0.7, 0.5, 0.5)),
			>         (tumor,        (1.0, 0.0, 0.0)),
			>     ],
			>     spacing=(0.5, 0.5, 1.0),
			> )
	"""
	# Imports & Assertions
	import numpy as np
	from numpy.typing import NDArray
	assert len(segments) > 0, "At least one segment must be provided."
	if is_generic_instance(segments, list[NDArray[Any]]):
		segments = add_default_colors_to_segments(segments)
	assert all(isinstance(seg, tuple) and len(seg) == 2 for seg in segments), "Each segment must be a tuple of (array, rgb_color)."
	assert all(array.ndim == 3 for array, _ in segments), "All input arrays must be 3D."
	assert len(spacing) == 3, f"Spacing must have length 3 for a 3D array, got {len(spacing)}."
	assert step_size > 0, f"Step size must be positive, got {step_size}."
	if verbose > 1:
		debug(
			f"Generating 3D mesh from {len(segments)} segments, "
			f"spacing={spacing}, threshold={threshold}, step_size={step_size}, "
			f"pad_array={pad_array}."
		)

	# Prepare output paths
	mtl_path: str = os.path.splitext(path)[0] + ".mtl"
	mtl_name: str = os.path.basename(mtl_path)

	# Initialize OBJ and MTL content
	obj_lines: list[str] = [
		"# OBJ file generated from segmentation arrays",
		f"# Segments: {len(segments)}",
		f"mtllib {mtl_name}",
		"",
	]
	mtl_lines: list[str] = ["# MTL file for segmentation colors", ""]

	# Process each segment
	vertex_offset: int = 0  # running total of vertices written so far
	for seg_idx, (array, (r, g, b, a)) in enumerate(segments):

		# Name for this segment's material (used in MTL and referenced in OBJ)
		mat_name: str = f"seg_{seg_idx}"
		assert array.ndim == 3, f"Segment {seg_idx}: array must be 3D, got shape {array.shape}."
		if verbose > 1:
			debug(f"Processing segment {seg_idx}: shape={array.shape}, color=({r},{g},{b},{a}), non-zero={np.count_nonzero(array):,}")

		# Extract vertices and faces using marching cubes
		verts, faces = extract_verts_faces_from_segment(array, spacing, threshold, step_size, pad_array)

		if verbose > 1:
			debug(f"Segment {seg_idx}: {len(verts):,} vertices, {len(faces):,} faces")

		# --- MTL entry for this segment ---
		mtl_lines += [
			f"newmtl {mat_name}",
			f"Kd {r:.6f} {g:.6f} {b:.6f}",  # diffuse
			f"Ka {r*0.1:.6f} {g*0.1:.6f} {b*0.1:.6f}",  # ambient (10% of diffuse)
			"Ks 0.0 0.0 0.0",               # no specular
			f"d {a:.6f}",                   # alpha (transparency)
			f"Tr {1.0 - a:.6f}",            # transparency (inverted alpha) (for compatibility with some software)
			"illum 2",                      # use default lighting
			"",
		]

		# --- OBJ entries for this segment ---
		obj_lines += [
			f"# Segment {seg_idx}",
			f"g seg_{seg_idx}",       # group (useful in Blender/MeshLab)
			f"usemtl {mat_name}",
			"",
		]
		obj_lines.extend(f"v {x:.6f} {y:.6f} {z:.6f}" for x, y, z in verts)
		# Faces are offset by all previously written vertices
		obj_lines.extend(f"f {a+1+vertex_offset} {b+1+vertex_offset} {c+1+vertex_offset}" for a, b, c in faces)
		obj_lines.append("")

		vertex_offset += len(verts)

	# --- Write files ---
	with super_open(path, "w") as f:
		f.write("\n".join(obj_lines) + "\n")

	with super_open(mtl_path, "w") as f:
		f.write("\n".join(mtl_lines) + "\n")

	if verbose > 0:
		info(f"Exported {len(segments)} segments to '{path}' + '{mtl_path}'")

