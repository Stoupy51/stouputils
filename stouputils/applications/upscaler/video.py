"""
This module provides utility functions for upscaling videos using waifu2x-ncnn-vulkan.

It extracts frames from videos, upscales them individually, and then recombines them
into a high-quality output video. The process preserves audio from the original video
and handles configuration of video encoding parameters like bitrate and framerate.

Main functionalities:

- Extracting frames from videos using FFmpeg
- Upscaling frames using waifu2x-ncnn-vulkan
- Recombining frames into videos with optimized bitrates
- Handling partially processed videos to resume interrupted operations
- Calculating recommended bitrates based on resolution and framerate

The module includes YouTube's recommended bitrate settings for different resolutions,
framerates, and HDR/SDR content types, ensuring optimal quality for various outputs.

Example usage:

.. code-block:: python

	# Imports
	import stouputils.applications.upscaler as app
	from stouputils.io import get_root_path

	# Constants
	ROOT: str = get_root_path(__file__) + "/upscaler"
	INPUT_FOLDER: str = f"{ROOT}/input"
	PROGRESS_FOLDER: str = f"{ROOT}/progress"
	OUTPUT_FOLDER: str = f"{ROOT}/output"

	# Main
	if __name__ == "__main__":
		app.video_upscaler_cli(INPUT_FOLDER, PROGRESS_FOLDER, OUTPUT_FOLDER)
"""

# Imports
import os
import shutil
import subprocess
import sys
from typing import Literal

from PIL import Image

from ...installer import check_executable
from ...io import clean_path
from ...parallel import colored_for_loop, multithreading
from ...print import debug, error, info, warning
from .config import FFMPEG_RELEASES, YOUTUBE_BITRATE_RECOMMENDATIONS, Config
from .image import convert_frame, get_all_files, upscale_folder


# Functions
def get_recommended_bitrate(
	resolution: tuple[int, int], frame_rate: int = 60, upload_type: Literal["SDR","HDR"] = "SDR"
) -> int:
	""" Get the recommended bitrate (in kbps) for the output video based on the video resolution.

	Args:
		resolution  (tuple[int, int]):       Video resolution (width, height).
		frame_rate  (int):                   Frame rate of the video, default is 60.
		upload_type (Literal["SDR","HDR"]):  Upload type from which the recommendation is made, default is "SDR".

	Returns:
		int:     The recommended bitrate for the output video (in kbps)

	Source: https://support.google.com/youtube/answer/1722171?hl=en#zippy=%2Cbitrate

	Examples:
		>>> # Valid examples
		>>> get_recommended_bitrate((3840, 2160), 60, "SDR")
		68000
		>>> get_recommended_bitrate((1920, 1080), 60, "HDR")
		15000
		>>> get_recommended_bitrate((1920, 1080), 60, "SDR")
		12000
		>>> get_recommended_bitrate((1920, 1080), 30, "SDR")
		8000

		>>> # Invalid examples
		>>> get_recommended_bitrate((1920, 1080), 60, "Ratio")
		Traceback (most recent call last):
			...
		AssertionError: Invalid upload type: 'Ratio'
		>>> get_recommended_bitrate("1920x1080", 60, "SDR")
		Traceback (most recent call last):
			...
		AssertionError: Invalid resolution: 1920x1080, must be a tuple of two integers
		>>> get_recommended_bitrate((1920, 1080), -10, "SDR")
		Traceback (most recent call last):
			...
		AssertionError: Invalid frame rate: -10, must be a positive integer
	"""
	# Assertions
	assert isinstance(resolution, tuple) and len(resolution) == 2, \
		f"Invalid resolution: {resolution}, must be a tuple of two integers"
	assert isinstance(frame_rate, int) and frame_rate > 0, \
		f"Invalid frame rate: {frame_rate}, must be a positive integer"
	assert upload_type in YOUTUBE_BITRATE_RECOMMENDATIONS, \
		f"Invalid upload type: '{upload_type}'"

	# Determine frame rate category
	frame_rate_category: str = "high" if frame_rate >= 48 else "standard"

	# Get the appropriate bitrate dictionary
	resolution_bitrates: dict[int, int] = YOUTUBE_BITRATE_RECOMMENDATIONS[upload_type][frame_rate_category]

	# Find the appropriate bitrate based on resolution
	max_dimension: int = min(*resolution)
	for min_resolution, bitrate in sorted(resolution_bitrates.items(), reverse=True):
		if max_dimension >= min_resolution:
			return bitrate

	# Fallback (should never reach here due to the '0' key in dictionaries)
	return 1000


def check_ffmpeg_executable() -> None:
	if not Config.ffmpeg_executable_checked:
		check_executable(Config.FFMPEG_EXECUTABLE, Config.FFMPEG_CHECK_HELP_TEXT, FFMPEG_RELEASES, append_to_path="bin")
		Config.ffmpeg_executable_checked = True

# Routine to handle a video file
def upscale_video(video_file: str, input_folder: str, progress_folder: str, output_folder: str) -> None:
	""" Handles a video file. """
	# Prepare paths
	input_path: str = f"{input_folder}/{video_file}"
	progress_path: str = f"{progress_folder}/{video_file}"
	p_extracted_path: str = f"{progress_path}/extracted"
	p_upscaled_path: str = f"{progress_path}/upscaled"
	output_path: str = f"{output_folder}/{video_file}"
	os.makedirs(p_extracted_path, exist_ok = True)
	os.makedirs(p_upscaled_path, exist_ok = True)

	# Check if executable is installed
	check_ffmpeg_executable()

	## Step 1: Check if the video file is already upscaled or partially processed, if not, extract frames
	# If the video file is already upscaled, skip it
	if os.path.exists(output_path):
		warning(f"'{video_file}' has already been processed, remove it from the output folder to reprocess it.")
		return

	# If the video is already in the list of videos that have been partially processed, ask to restart or skip
	is_partially_processed: bool = len(os.listdir(p_extracted_path)) > 0 and len(os.listdir(p_upscaled_path)) > 0
	if is_partially_processed:
		info(f"'{video_file}' has already been partially processed, do you want to resume the process? (Y/n)")
		if input().lower() == "n":
			shutil.rmtree(p_upscaled_path, ignore_errors = True)
			os.makedirs(p_upscaled_path, exist_ok = True)
			is_partially_processed = False

	# If the video is not partially processed, extract frames
	if not is_partially_processed:
		debug(f"Extracting frames from '{video_file}'...")

		# Extract frames using ffmpeg
		command: list[str] = [Config.FFMPEG_EXECUTABLE, "-i", input_path, f"{p_extracted_path}/%09d.png"]
		subprocess.run(command, capture_output = True)

	# Convert all frames to JPG format
	frames_to_convert: list[str] = get_all_files(p_extracted_path, ".png")
	if frames_to_convert:
		multithreading(convert_frame, frames_to_convert, desc="Converting frames to JPG format")


	## Step 2: Upscale the frames
	# Get all the frames in the progress folder
	all_frames: list[str] = get_all_files(p_extracted_path, ".jpg")
	upscaled_frames: list[str] = get_all_files(p_upscaled_path, ".jpg")

	# If there are frames to upscale,
	if len(all_frames) > len(upscaled_frames):

		# Try to get upscaling ratio if any
		upscale_ratio: int = 2
		if upscaled_frames:
			with Image.open(upscaled_frames[0]) as img:
				upscaled_size: tuple[int, int] = img.size
			with Image.open(all_frames[0]) as img:
				extracted_size: tuple[int, int] = img.size
			upscale_ratio = upscaled_size[0] // extracted_size[0]
			info(f"Detected upscaling ratio: {upscale_ratio}")
		else:
			if "--upscale" in sys.argv:
				upscale_index: int = sys.argv.index("--upscale")
				if upscale_index + 1 < len(sys.argv):
					upscale_ratio = int(sys.argv[upscale_index + 1])
				else:
					error(
						"No upscaling ratio provided with --upscale flag. "
						"Please provide a ratio after the flag. (1/2/4/8/16/32)"
					)
			else:
				info("No upscaling ratio provided, please enter one (1/2/4/8/16/32, default=2):")
				upscale_ratio = int(input() or "2")

		# For each frame that hasn't been upscaled yet, upscale it
		upscale_folder(p_extracted_path, p_upscaled_path, upscale_ratio, slightly_faster_mode=Config.SLIGHTLY_FASTER_MODE)

	## Step 3: Convert the upscaled frames to a video
	# Get the video bitrate
	if Config.VIDEO_FINAL_BITRATE == -1:
		upscaled_frame: str = get_all_files(p_upscaled_path, ".jpg")[0]
		with Image.open(upscaled_frame) as img:
			upscaled_size: tuple[int, int] = img.size
		video_bitrate: int = get_recommended_bitrate(upscaled_size)
	else:
		video_bitrate: int = Config.VIDEO_FINAL_BITRATE

	# Get the framerate of the original video
	original_framerate: str = "60"
	ffprobe_command: list[str] = [
		Config.FFPROBE_EXECUTABLE,                    # Path to the ffprobe executable
		"-v", "error",                                # Set verbosity level to error (only show errors)
		"-select_streams", "v:0",                     # Select the first video stream
		"-show_entries", "stream=r_frame_rate",       # Show only the frame rate information
		"-of", "default=noprint_wrappers=1:nokey=1",  # Format output without wrappers and keys
		input_path,                                   # Path to the input video file
	]
	try:
		result = subprocess.run(ffprobe_command, capture_output=True, text=True, check=True)
		framerate: str = result.stdout.strip()
		if not framerate or '/' not in framerate: # Basic validation
			warning(f"Could not reliably determine framerate for '{video_file}'. Falling back to 60.")
			original_framerate = "60"
		else:
			debug(f"Detected original framerate: {framerate}")
			original_framerate = framerate
	except (subprocess.CalledProcessError, FileNotFoundError) as e:
		warning(f"Failed to get framerate using ffprobe for '{video_file}': {e}. Falling back to 60.")


	# Prepare the command to convert the upscaled frames to a video
	subprocess.run([
		Config.FFMPEG_EXECUTABLE,
		"-framerate", original_framerate,    # Use the original video's framerate for input frames
		"-i", f"{p_upscaled_path}/%09d.jpg", # Use p_upscaled_path, not upscaled_path
		"-i", input_path,                    # Input video for sound and metadata
		"-b:v", f"{video_bitrate}k",         # Set the video bitrate (in kbps)
		*Config.FFMPEG_ARGS,			 	 # Additional arguments from the config
		"-r", original_framerate,            # Set the *output* video framerate
		output_path,                         # Output video
	])


def video_upscaler_cli(input_folder: str, progress_folder: str, output_folder: str) -> None:
	""" Upscales videos from an input folder and saves them to an output folder.

	Uses intermediate folders for extracted and upscaled frames within the progress folder.
	**Handles resuming partially processed videos.**

	Args:
		input_folder    (str): Path to the folder containing input videos.
		progress_folder (str): Path to the folder for storing intermediate files (frames).
		output_folder   (str): Path to the folder where upscaled videos will be saved.
	"""
	# Clean paths
	input_folder = clean_path(input_folder)
	progress_folder = clean_path(progress_folder)
	output_folder = clean_path(output_folder)
	os.makedirs(input_folder, exist_ok = True)
	os.makedirs(progress_folder, exist_ok = True)
	os.makedirs(output_folder, exist_ok = True)

	# Ask if we should shutdown the computer after the script is finished
	info("Do you want to shutdown the computer after the script is finished? (y/N)")
	shutdown_after_script: bool = input().lower() == "y"

	# Collect all video files in the input folder
	videos: list[str] = [file for file in os.listdir(input_folder) if not file.endswith(".md")]

	# Handle each video file
	for video in colored_for_loop(videos, desc="Upscaling videos"):
		upscale_video(video, input_folder, progress_folder, output_folder)

	# Shutdown the computer after the script is finished
	if shutdown_after_script:
		info("Shutting down the computer...")
		if os.name == "nt":
			subprocess.run(["shutdown", "/s", "/t", "0", "/f"], capture_output = False)
		else:
			subprocess.run(["shutdown", "now"], capture_output = False)

