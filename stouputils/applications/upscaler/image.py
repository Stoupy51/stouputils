"""
This module provides utility functions for upscaling images using waifu2x-ncnn-vulkan.

It includes functions to upscale individual images, batches of images in a folder,
and handle intermediate operations like converting between image formats.
The module also manages temporary directories for partial processing and tracks
progress of batch operations.

Main functionalities:

- Converting frames between image formats (PNG to JPG)
- Upscaling individual images with configurable upscale ratio
- Batch processing folders of images with progress tracking
- Handling already processed images to resume interrupted operations

Example usage:

.. code-block:: python

    from stouputils.applications.upscaler import upscale, upscale_folder

    # Upscale a single image
    upscale("input.jpg", "output.jpg", 2)

    # Upscale a folder of images
    upscale_folder("input_folder", "output_folder", 2)
"""

# Imports
import os
import shutil
import subprocess
from tempfile import TemporaryDirectory

from PIL import Image

from ...installer import check_executable
from ...io import clean_path
from ...parallel import colored_for_loop, multithreading
from ...print import debug, info
from .config import WAIFU2X_NCNN_VULKAN_RELEASES, Config


# Function to convert a PNG frame to JPG format
def convert_frame(frame_path: str, delete_png: bool = True) -> None:
	""" Convert a PNG frame to JPG format to take less space.

	Args:
		frame_path  (str):   Path to the PNG frame to convert.
		delete_png  (bool):  Whether to delete the original PNG file after conversion.

	Returns:
		None: This function doesn't return anything.

	Example:
		.. code-block:: python

			> convert_frame("input.png", delete_png=True)
			> # input.png will be converted to input.jpg and the original file will be deleted

			> convert_frame("input.png", delete_png=False)
			> # input.png will be converted to input.jpg and the original file will be kept
	"""
	if frame_path.endswith(".png"):
		with Image.open(frame_path) as img:
			img.save(frame_path.replace(".png", ".jpg"), quality=Config.JPG_QUALITY)
		if delete_png:
			os.remove(frame_path)


# Function to get all frames in a folder
def get_all_files(folder: str, suffix: str | tuple[str, ...] = "") -> list[str]:
	""" Get all files paths in a folder, with a specific suffix if provided.

	Args:
		folder     (str):                    Path to the folder containing the files.
		suffix     (str | tuple[str, ...]):  Suffix of the files to get (e.g. ".png", ".jpg", etc.).

	Returns:
		list[str]: List of all files paths in the folder.

	Example:
		>>> files: list[str] = get_all_files("some_folder", ".png")
		>>> len(files)
		0
	"""
	if not os.path.exists(folder):
		return []
	return [f"{folder}/{f}" for f in os.listdir(folder) if f.endswith(suffix)]


# Function to create a temporary directory with not upscaled images
def create_temp_dir_for_not_upscaled(input_path: str, output_path: str) -> TemporaryDirectory[str] | None:
    """ Creates a temporary directory containing only images that haven't been upscaled yet.

    Args:
        input_path  (str):  Path to the folder containing input images.
        output_path (str):  Path to the folder where upscaled images are saved.

    Returns:
        TemporaryDirectory[str] | None: A temporary directory object if there are images to process,
                                        None if all images are already upscaled.
    """
    # Get all input images and the not upscaled images
    all_inputs: list[str] = get_all_files(input_path)
    not_upscaled_images: list[str] = [x for x in all_inputs if not os.path.exists(f"{output_path}/{os.path.basename(x)}")]

    # If all images or none are already upscaled, return None
    if len(not_upscaled_images) == 0 or (len(not_upscaled_images) == len(all_inputs)):
        return None

    # Create a temporary directory and copy the not upscaled images to it
    temp_dir: TemporaryDirectory[str] = TemporaryDirectory()
    debug(f"Creating temporary directory to process {len(not_upscaled_images)} images: {temp_dir.name}")
    for image in not_upscaled_images:
        shutil.copyfile(image, f"{temp_dir.name}/{os.path.basename(image)}")
    return temp_dir


# Helper function to check if the upscaler executable is installed
def check_upscaler_executable() -> None:
	if not Config.upscaler_executable_checked:
		check_executable(Config.UPSCALER_EXECUTABLE, Config.UPSCALER_EXECUTABLE_HELP_TEXT, WAIFU2X_NCNN_VULKAN_RELEASES)
		Config.upscaler_executable_checked = True


# Function to upscale an image
def upscale(input_path: str, output_path: str, upscale_ratio: int) -> None:
	""" Upscale an input image (or a directory of images) with the upscaler executable.

	Args:
		input_path     (str):  Path to the image to upscale (or a directory).
		output_path    (str):  Path to the output image (or a directory).
		upscale_ratio  (int):  Upscaling ratio.

	Example:
		.. code-block:: python

			> upscale("folder", "folder", 2)
			Traceback (most recent call last):
				...
			AssertionError: Input and output paths cannot be the same, got 'folder'

			> upscale("stouputils", "stouputils/output.jpg", 2)
			Traceback (most recent call last):
				...
			AssertionError: If input is a directory, output must be a directory too, got 'stouputils/output.jpg'


			> upscale("input.jpg", "output.jpg", 2)
			> # The input.jpg will be upscaled to output.jpg with a ratio of 2

			> upscale("input_folder", "output_folder", 2)
			> # The input_folder will be upscaled to output_folder with a ratio of 2
	"""
	check_upscaler_executable()
	is_input_dir: bool = os.path.isdir(input_path)
	is_output_dir: bool = os.path.isdir(output_path)

	# Assertions
	assert input_path != output_path, f"Input and output paths cannot be the same, got '{input_path}'"
	invalid_dir_combination: bool = is_input_dir == True and is_output_dir == False  # noqa: E712
	assert not invalid_dir_combination, f"If input is a directory, output must be a directory too, got '{output_path}'"

	# Convert output_path to a file path if it's a directory
	if is_output_dir and not is_input_dir:

		# Needs to be a PNG file to be converted to JPG later
		output_file_name: str = os.path.basename(input_path).replace(".jpg", ".png")
		output_path = clean_path(f"{output_path}/{output_file_name}")
		is_output_dir = False

	# If both input and output are folders, and there are images already upscaled in the output folder,
	# Then create a temporary folder with not upscaled images
	temp_dir: TemporaryDirectory[str] | None = None
	if is_input_dir and is_output_dir:
		temp_dir = create_temp_dir_for_not_upscaled(input_path, output_path)
		if temp_dir:
			input_path = temp_dir.name

	# Build the command and run it
	cmd: list[str] = [Config.UPSCALER_EXECUTABLE, *Config.UPSCALER_ARGS]
	cmd[cmd.index("INPUT_PATH")] = input_path	          # Replace the input path
	cmd[cmd.index("OUTPUT_PATH")] = output_path	          # Replace the output path
	cmd[cmd.index("UPSCALE_RATIO")] = str(upscale_ratio)  # Replace the upscaled ratio (if using waifu2x-ncnn-vulkan)
	subprocess.run(cmd, capture_output=True)

	# If the input was a temporary folder, delete it
	if temp_dir:
		temp_dir.cleanup()

	# Convert the output frames to JPG format
	if not is_output_dir:
		convert_frame(output_path)
	else:
		frames_to_convert: list[str] = get_all_files(output_path, ".png")
		if frames_to_convert:
			multithreading(convert_frame, frames_to_convert, desc="Converting frames to JPG format")


# Function to upscale multiple images
def upscale_images(images: list[str], output_folder: str, upscale_ratio: int, desc: str = "Upscaling images") -> None:
	""" Upscale multiple images from a list.

	Args:
		images        (list[str]): List of paths to the images to upscale.
		output_folder (str):       Path to the output folder where the upscaled images will be saved.
		upscale_ratio (int):       Upscaling ratio.
		desc          (str):       Description of the function execution displayed in the progress bar.
			No progress bar will be displayed if desc is empty.

	Returns:
		None: This function doesn't return anything.
	"""
	for image_path in (colored_for_loop(images, desc=desc) if desc != "" else images):
		upscale(image_path, output_folder, upscale_ratio)

# Function to upscale a folder of images
def upscale_folder(
	input_folder: str,
	output_folder: str,
	upscale_ratio: int,
	slightly_faster_mode: bool = True,
	desc: str = "Upscaling folder"
) -> None:
	""" Upscale all images in a folder.

	Args:
		input_folder          (str):   Path to the input folder containing the images to upscale.
		output_folder         (str):   Path to the output folder where the upscaled images will be saved.
		upscale_ratio         (int):   Upscaling ratio.
		slightly_faster_mode  (bool):  Whether to use the slightly faster mode (no progress bar),
			one call to the upscaler executable.
		desc                  (str):   Description of the function execution displayed in the progress bar.
			No progress bar will be displayed if desc is empty.

	Returns:
		None: This function doesn't return anything.
	"""
	info(f"Upscaling '{input_folder}' to '{output_folder}' with a ratio of {upscale_ratio}...")
	if slightly_faster_mode:
		upscale(input_folder, output_folder, upscale_ratio)
	else:
		inputs: list[str] = get_all_files(input_folder)
		not_upscaled_images: list[str] = [x for x in inputs if not os.path.exists(f"{output_folder}/{os.path.basename(x)}")]
		upscale_images(not_upscaled_images, output_folder, upscale_ratio, desc=desc)

