""" Main module of the installer subpackage for stouputils.

Provides functions for installing programs from local zip files or URLs.
It handles downloading, extracting, and setting up programs in a platform-agnostic way.

This module contains the core installation functions that are used by both the Windows
and Linux/macOS specific modules.
"""
# ruff: noqa: F403
# ruff: noqa: F405

# Imports
import os
import platform
import shutil
import tarfile
import zipfile
from collections.abc import Callable
from tempfile import TemporaryDirectory

import requests

from ..decorators import LogLevels, handle_error
from ..print import info, warning
from .common import *
from .linux import *
from .windows import *


# Helper functions
def extract_archive(
	extraction_path: str,
	temp_dir: str,
	extract_func: Callable[[str], None],
	get_file_list_func: Callable[[], list[str]]
) -> None:
	""" Helper function to extract archive files with consistent handling.

	Args:
		extraction_path     (str): Path where files should be extracted
		temp_dir            (str): Temporary directory for intermediate extraction
		extract_func        (Callable[[str], None]): Function to extract the archive
		get_file_list_func  (Callable[[], list[str]]): Function to get the list of files in the archive
	"""
	os.makedirs(extraction_path, exist_ok=True)

	# Check if the archive contains a single folder
	file_list: list[str] = get_file_list_func()
	root_dirs: set[str] = {item.split('/')[0] + '/' for item in file_list if '/' in item}

	# If all files are in a single root directory
	if len(root_dirs) == 1 and all(item.startswith(next(iter(root_dirs))) for item in file_list):
		# Extract to a temporary location first
		temp_extract_path: str = os.path.join(temp_dir, "extracted")
		os.makedirs(temp_extract_path, exist_ok=True)
		extract_func(temp_extract_path)

		# Move contents from the single folder to the final path
		single_folder_path: str = os.path.join(temp_extract_path, next(iter(root_dirs)).rstrip('/'))
		for item in os.listdir(single_folder_path):
			src_path: str = os.path.join(single_folder_path, item)
			dst_path: str = os.path.join(extraction_path, item)
			if os.path.isdir(src_path):
				shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
			else:
				shutil.copy2(src_path, dst_path)
		debug(f"Extracted program contents from single folder to '{extraction_path}'")
	else:
		# Normal extraction if not a single folder
		extract_func(extraction_path)
		debug(f"Extracted program to '{extraction_path}'")


# Functions
def get_install_path(
	program_name: str,
	platform_str: str = platform.system(),
	ask_global: int = 0,
	add_path: bool = True,
	append_to_path: str = "",
	) -> str:
	""" Get the installation path for the program on the current platform.

	Args:
		program_name  (str):  The name of the program to install.
		platform_str  (str):  The platform to get the installation path for.
		ask_global    (int):  Whether to ask the user for a path, 0 = ask, 1 = install globally, 2 = install locally.
		add_path      (bool): Whether to add the program to the PATH environment variable.
		append_to_path (str):  String to append to the installation path when adding to PATH.
			(ex: "bin" if executables are in the bin folder)

	Returns:
		str: The installation path for the program.
	"""
	platform_str = str(platform_str).lower()
	if platform_str == "windows":
		return get_install_path_windows(program_name, ask_global, add_path=add_path, append_to_path=append_to_path)
	elif platform_str == "linux":
		return get_install_path_linux(program_name, ask_global, add_path=add_path, append_to_path=append_to_path)
	else:
		warning(f"Unsupported platform for automatic install path: {platform_str}")
		return ""

def add_to_path(install_path: str, platform_str: str = platform.system()) -> bool:
	""" Add the program to the PATH environment variable.

	Args:
		install_path  (str):  The path to the program to add to the PATH environment variable.
		platform_str  (str):  The platform you are running on (ex: "Windows", "Linux", "Darwin", ...),
			we use this to determine the installation path if not provided.

	Returns:
		bool: True if add to PATH was successful, False otherwise.
	"""
	platform_str = str(platform_str).lower()
	if platform_str == "windows":
		return add_to_path_windows(install_path) is True
	elif platform_str == "linux":
		return add_to_path_linux(install_path) is True
	else:
		warning(f"Unsupported platform for automatic add to PATH: {platform_str}")
		return False

@handle_error(message="Failed during program installation", error_log=LogLevels.WARNING_TRACEBACK)
def install_program(
	input_path: str,
	install_path: str = "",
	platform_str: str = platform.system(),
	program_name: str = "",
	add_path: bool = True,
	append_to_path: str = "",
	) -> bool:
	""" Install a program to a specific path from a local zip file or URL.

	Args:
		input_path     (str):  Path to a zip file or a download URL.
		install_path   (str):  The directory to extract the program into, we ask user for a path if not provided.
		platform_str   (str):  The platform you are running on (ex: "Windows", "Linux", "Darwin", ...),
			we use this to determine the installation path if not provided.
		add_path       (bool): Whether to add the program to the PATH environment variable.
		program_name   (str):  Override the program name, we get it from the input path if not provided.
		append_to_path (str):  String to append to the installation path when adding to PATH.
			(ex: "bin" if executables are in the bin folder)

	Returns:
		bool: True if installation was successful, False otherwise.
	"""
	# Get program name from input path if not provided
	# (ex: "https://example.com/program.zip" -> "program", "/var/www/program.exe" -> "program")
	if not program_name:
		program_name = os.path.splitext(os.path.basename(input_path))[0]

	# If no install path is provided, ask the user for one
	final_install_path: str = install_path
	if not install_path:
		final_install_path = get_install_path(program_name, platform_str, add_path=add_path, append_to_path=append_to_path)
		if not final_install_path:
			warning("Failed to get installation path, please provide a path to install the program to.")
			return False

	# Create a temporary directory
	with TemporaryDirectory() as temp_dir:
		temp_dir: str
		program_path: str = ""

		# Download the program if it's a URL
		if input_path.startswith("http"):
			info(f"Downloading program from '{input_path}'")
			response: requests.Response = requests.get(input_path)
			if response.status_code != 200:
				warning(f"Failed to download program from '{input_path}', reason: {response.reason}")
				return False

			# Save the program to a temporary directory
			temp_file: str = os.path.join(temp_dir, "program.zip")
			with open(temp_file, "wb") as f:
				f.write(response.content)
			program_path = temp_file
			debug(f"Downloaded program to '{program_path}'")
		else:
			program_path = input_path
			debug(f"Using local program path '{program_path}'")

		# Extract the program if it's a zip file
		if program_path.endswith(".zip"):
			with zipfile.ZipFile(program_path, "r") as zip_ref:
				extract_archive(
					final_install_path,
					temp_dir,
					lambda path: zip_ref.extractall(path),
					lambda: zip_ref.namelist()
				)

		# Extract the program if it's a tar.xz file
		elif program_path.endswith(".tar.xz"):
			with tarfile.open(program_path, "r:xz") as tar_ref:
				extract_archive(
					final_install_path,
					temp_dir,
					lambda path: tar_ref.extractall(path),
					lambda: tar_ref.getnames()
				)

		# Else, it's a directory so we just need to copy it
		elif os.path.isdir(program_path):
			shutil.copytree(program_path, final_install_path)

		else:
			warning(f"Failed to install program, input path is not a zip, tar.xz file or directory: '{program_path}'")
			return False

	# If add_path is True, and the installation path was provided, we add it to the PATH environment variable
	if add_path and install_path:
		if not add_to_path(os.path.join(final_install_path, append_to_path), platform_str):
			warning(
				f"Failed to add program to PATH, please add it manually to your PATH environment variable:\n"
				f"{final_install_path}"
			)
			return False

	# If we get here, the program was installed successfully
	return True

