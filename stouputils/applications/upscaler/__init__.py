"""
This module provides utilities for upscaling images and videos using waifu2x-ncnn-vulkan (by default).

It includes functions to upscale individual images, batches of images in a folder,
and videos by processing them frame by frame. It also handles configuration and
installation of required dependencies.

.. video:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/applications/upscaler.mp4
  :alt: stouputils upscaler example
"""
# ruff: noqa: F403

# Imports
from .config import *
from .image import *
from .video import *

