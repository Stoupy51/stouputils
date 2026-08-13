"""
This module provides little utilities for image processing.

- :py:func:`~cropping.auto_crop` - Automatically crop an image to remove zero/uniform regions.
- :py:func:`~segments_export.numpy_segments_to_obj` - Generate a '.obj' file from multiple 3D segmentation arrays, each with its own color.
- :py:func:`~gif_export.numpy_to_gif` - Generate a '.gif' file from a 3D numpy array for visualization.
- :py:func:`~obj_export.numpy_to_obj` - Generate a '.obj' file from a 3D numpy array using marching cubes.
- :py:func:`~resize.image_resize` - Resize an image while preserving its aspect ratio by default.
"""

# Lazy imports (PEP 810), ignored before Python 3.15
__lazy_modules__: frozenset[str] = frozenset({
	"stouputils.image.cropping",
	"stouputils.image.gif_export",
	"stouputils.image.obj_export",
	"stouputils.image.resize",
	"stouputils.image.segments_export",
})

# Imports
from .cropping import (
	T as T,
	auto_crop as auto_crop,
)
from .gif_export import (
	numpy_to_gif as numpy_to_gif,
)
from .obj_export import (
	extract_verts_faces_from_segment as extract_verts_faces_from_segment,
	numpy_to_obj as numpy_to_obj,
)
from .resize import (
	image_resize as image_resize,
)
from .segments_export import (
	add_default_colors_to_segments as add_default_colors_to_segments,
	numpy_segments_to_obj as numpy_segments_to_obj,
)

