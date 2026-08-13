"""
This module provides utilities for upscaling images and videos using waifu2x-ncnn-vulkan (by default).

It includes functions to upscale individual images, batches of images in a folder,
and videos by processing them frame by frame. It also handles configuration and
installation of required dependencies.

.. raw:: html

	<video width="100%" height="auto" controls>
			<source src="https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/applications/upscaler.mp4" type="video/mp4">
			Your browser does not support the video tag.
	</video>

Example of script:

.. code-block:: python

	# Imports
	import stouputils.applications.upscaler as app
	from stouputils.io.path import get_root_path

	# Constants
	ROOT: str = get_root_path(__file__) + "/upscaler"
	INPUT_FOLDER: str = f"{ROOT}/input"
	PROGRESS_FOLDER: str = f"{ROOT}/progress"
	OUTPUT_FOLDER: str = f"{ROOT}/output"

	# Main
	if __name__ == "__main__":
		app.video_upscaler_cli(INPUT_FOLDER, PROGRESS_FOLDER, OUTPUT_FOLDER)
"""

# Lazy imports (PEP 810), ignored before Python 3.15
__lazy_modules__: frozenset[str] = frozenset({
	"stouputils.applications.upscaler.config",
	"stouputils.applications.upscaler.image",
	"stouputils.applications.upscaler.video",
})

# Imports
from .config import (
	FFMPEG_RELEASES as FFMPEG_RELEASES,
	WAIFU2X_NCNN_VULKAN_RELEASES as WAIFU2X_NCNN_VULKAN_RELEASES,
	YOUTUBE_BITRATE_RECOMMENDATIONS as YOUTUBE_BITRATE_RECOMMENDATIONS,
	Config as Config,
)
from .image import (
	check_upscaler_executable as check_upscaler_executable,
	convert_frame as convert_frame,
	create_temp_dir_for_not_upscaled as create_temp_dir_for_not_upscaled,
	get_all_files as get_all_files,
	upscale as upscale,
	upscale_folder as upscale_folder,
	upscale_images as upscale_images,
)
from .video import (
	check_ffmpeg_executable as check_ffmpeg_executable,
	get_recommended_bitrate as get_recommended_bitrate,
	upscale_video as upscale_video,
	video_upscaler_cli as video_upscaler_cli,
)

