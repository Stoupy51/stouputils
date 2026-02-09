""" Application-specific utilities and tools.

This module provides higher-level utilities for specific application needs:

Automatic Documentation:

- Automatic documentation generation with Sphinx: `update_documentation(...)`
- Support for multi-version documentation
- GitHub Pages integration
- Markdown to RST conversion

Upscaler:

- Utilities to upscale **images** and **videos** using external tools (defaults to `waifu2x-ncnn-vulkan` and `ffmpeg`).
- Image utilities: `upscale()`, `upscale_images()`, `upscale_folder()`, `convert_frame()`, and helpers to manage temporary folders and resume partial work.
- Video utilities: extract frames with `ffmpeg`, upscale frames, recombine frames into a final video (preserves audio),
  compute recommended bitrates using YouTube recommendations, and a `video_upscaler_cli()` convenience entry point for batch processing.
- Configuration and installer helpers: `Config`, release lists like `WAIFU2X_NCNN_VULKAN_RELEASES` and `FFMPEG_RELEASES`, and `YOUTUBE_BITRATE_RECOMMENDATIONS` mapping for bitrate selection.

Example usage:

.. code-block:: python

	# Upscale images
	from stouputils.applications.upscaler import upscale, upscale_folder

	# Upscale videos (CLI helper)
	import stouputils.applications.upscaler as upscaler
	upscaler.video_upscaler_cli("input", "progress", "output")
"""
# Imports
from .automatic_docs import *
from .upscaler import *

