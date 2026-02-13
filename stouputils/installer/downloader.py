""" Downloader module for the installer subpackage.

Provides functions for downloading and installing programs from URLs.
It handles platform-specific downloads, checking if programs are already installed,
and setting up the downloaded programs for use.

This module works with the main installer module to provide a complete installation
solution for programs that need to be downloaded from the internet.
"""
# Imports
import os
import platform
import subprocess
import sys

from ..print import info, warning
from .main import install_program


# Functions
def download_executable(download_urls: dict[str, str], program_name: str, append_to_path: str = "") -> bool:
	""" Ask the user if they want to download the program (ex: waifu2x-ncnn-vulkan).
	If yes, try to download the program from the GitHub releases page.

	Args:
		download_urls  (dict[str, str]):  The URLs to download the program from.
		program_name   (str):             The name of the program to download.
		append_to_path (str):             String to append to installation path when adding to PATH.

	Returns:
		bool: True if the program is now ready to use, False otherwise.

	Examples:
		.. code-block:: python

			> # Download waifu2x-ncnn-vulkan for the current platform
			> urls = {
			>     "Windows": "https://github.com/.../waifu2x-windows.zip",
			>     "Linux": "https://github.com/.../waifu2x-ubuntu.zip",
			> }
			> success = download_executable(urls, "waifu2x-ncnn-vulkan")
			> # User is prompted: "Program executable not found, would you like to download it? (Y/n)"
			> # If yes, downloads and installs the program

			> # Download FFmpeg with executables in bin/ subdirectory
			> ffmpeg_urls = {
			>     "Windows": "https://github.com/.../ffmpeg-win64.zip",
			>     "Linux": "https://github.com/.../ffmpeg-linux64.tar.xz",
			> }
			> download_executable(ffmpeg_urls, "ffmpeg", append_to_path="bin")
			True
	"""
	# Ask the user if they want to download the upscaler
	program_url: str = next(iter(download_urls.values())).split("/download/")[0]
	warning(
		f"Program executable not found, would you like to download it automatically from GitHub? (Y/n) :\n"
		f"({program_url})"
	)

	# Handle the user's response
	if input().lower() == "n":
		info("User declined to download the upscaler.")
		return False

	# Get the platform
	system: str = platform.system()
	download_url: str = download_urls.get(system, "")
	if not download_url:
		warning(
			f"Unsupported platform: {system}, please download the program manually from the following URL:\n"
			f"  {program_url}"
		)
		return False

	# Download the upscaler
	if not install_program(download_url, program_name=program_name, append_to_path=append_to_path):
		warning("Failed to download the upscaler, please download it manually from the following URL:")
		print(f"  {download_url}")
		return False

	return True

def check_executable(
	executable: str,
	executable_help_text: str,
	download_urls: dict[str, str],
	append_to_path: str = ""
) -> None:
	""" Check if the executable exists, optionally download it if it doesn't.

	This function runs the executable with ``-h`` flag and checks if the help text matches.
	If the executable is not found or the help text doesn't match, it prompts the user
	to download it automatically from the provided URLs.

	Args:
		executable            (str):             The path to the executable.
		executable_help_text  (str):             The help text to check for in the executable's output.
		download_urls         (dict[str, str]):  The URLs to download the executable from.
		append_to_path        (str):             The path to append to the executable's path.
			(ex: "bin" if executables are in the bin folder)

	Examples:
		.. code-block:: python

			> from stouputils.installer import check_executable
			>
			> # Check if waifu2x-ncnn-vulkan is installed
			> WAIFU2X_RELEASES = {
			>     "Windows": "https://github.com/.../waifu2x-windows.zip",
			>     "Linux": "https://github.com/.../waifu2x-ubuntu.zip",
			> }
			> check_executable(
			>     "waifu2x-ncnn-vulkan",
			>     "waifu2x-ncnn-vulkan",  # Text expected in help output
			>     WAIFU2X_RELEASES
			> )
			> # If not found, user is prompted to download

			> # Check FFmpeg (executables in bin/ subdirectory)
			> FFMPEG_RELEASES = {
			>     "Windows": "https://github.com/.../ffmpeg-win64.zip",
			> }
			> check_executable(
			>     "ffmpeg",
			>     "ffmpeg version",
			>     FFMPEG_RELEASES,
			>     append_to_path="bin"
			> )
	"""
	program_name: str = os.path.basename(executable)
	try_download: bool = True

	# Run the command, capture output, don't check exit code immediately
	try:
		result: subprocess.CompletedProcess[str] = subprocess.run(
			[executable, "-h"],
			capture_output=True,
			text=True,  # Decode stdout/stderr as text
			check=False # Don't raise exception on non-zero exit code
		)

		# If the command failed (no help text matching), try to download the upscaler
		try_download: bool = executable_help_text.lower() not in result.stdout.lower()
	except FileNotFoundError:
		try_download: bool = True

	# If the command failed, try to download the upscaler
	if try_download:
		if not download_executable(download_urls, program_name, append_to_path=append_to_path):
			warning(f"'{program_name}' is required but not available. Exiting.")
		else:
			info(f"'{program_name}' downloaded successfully, please restart the script.")
		sys.exit(1)

