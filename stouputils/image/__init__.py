"""
This module provides little utilities for image processing.

- :py:func:`~colors.relative_luminance` - Perceived brightness of a colour, as the sRGB relative luminance.
- :py:func:`~colors.readable_text_color` - Pick the text colour that stays readable on a given background.
- :py:func:`~cropping.auto_crop` - Automatically crop an image to remove zero/uniform regions.
- :py:func:`~segments_export.numpy_segments_to_obj` - Generate a '.obj' file from multiple 3D segmentation arrays, each with its own color.
- :py:func:`~gif_export.numpy_to_gif` - Generate a '.gif' file from a 3D numpy array for visualization.
- :py:func:`~obj_export.numpy_to_obj` - Generate a '.obj' file from a 3D numpy array using marching cubes.
- :py:func:`~resize.image_resize` - Resize an image while preserving its aspect ratio by default.
"""

# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
from .colors import (
	readable_text_color as readable_text_color,
	relative_luminance as relative_luminance,
)
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

