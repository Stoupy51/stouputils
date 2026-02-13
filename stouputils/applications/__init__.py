""" Application-specific utilities and tools.

This module provides higher-level utilities for specific application needs:

Automatic Documentation:

- Automatic documentation generation with Sphinx: :py:func:`~stouputils.applications.automatic_docs.update_documentation`
- Support for multi-version documentation
- GitHub Pages integration
- Markdown to RST conversion

Upscaler:

- Utilities to upscale **images** and **videos** using external tools (defaults to ``waifu2x-ncnn-vulkan`` and ``ffmpeg``).
- Image utilities: :py:func:`~stouputils.applications.upscaler.image.upscale`, :py:func:`~stouputils.applications.upscaler.image.upscale_images`, :py:func:`~stouputils.applications.upscaler.image.upscale_folder`, :py:func:`~stouputils.applications.upscaler.image.convert_frame`, and helpers to manage temporary folders and resume partial work.
- Video utilities: extract frames with ``ffmpeg``, upscale frames, recombine frames into a final video (preserves audio),
  compute recommended bitrates using YouTube recommendations, and a :py:func:`~stouputils.applications.upscaler.video.video_upscaler_cli` convenience entry point for batch processing.
- Configuration and installer helpers: :py:class:`~stouputils.applications.upscaler.config.Config`, release lists like :py:data:`~stouputils.applications.upscaler.config.WAIFU2X_NCNN_VULKAN_RELEASES` and :py:data:`~stouputils.applications.upscaler.config.FFMPEG_RELEASES`, and :py:data:`~stouputils.applications.upscaler.config.YOUTUBE_BITRATE_RECOMMENDATIONS` mapping for bitrate selection.

Example usage:

.. code-block:: python

	# Upscale images
	from stouputils.applications.upscaler import upscale, upscale_folder

	# Upscale videos (CLI helper)
	import stouputils.applications.upscaler as upscaler
	upscaler.video_upscaler_cli("input", "progress", "output")
"""  # noqa: E501
# Imports
from .automatic_docs import *
from .upscaler import *

