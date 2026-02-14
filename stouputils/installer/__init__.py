""" Installer module for stouputils.

Provides functions for platform-agnostic installation tasks by dispatching
to platform-specific implementations (Windows, Linux/macOS).

It handles getting installation paths, adding programs to the PATH environment variable,
and installing programs from local zip files or URLs.

Main functions:

- :py:func:`~downloader.check_executable`: Check if an executable exists and offer to download it
- :py:func:`~downloader.download_executable`: Download and install a program from GitHub releases
- :py:func:`~main.install_program`: Install a program from a local archive or URL
- :py:func:`~main.get_install_path`: Get the appropriate installation path for the current platform
- :py:func:`~main.add_to_path`: Add a directory to the system PATH

Example usage from the upscaler application:

.. code-block:: python

    from stouputils.installer import check_executable

    # Define download URLs for different platforms
    WAIFU2X_RELEASES = {
        "Windows": "https://github.com/nihui/waifu2x-ncnn-vulkan/releases/download/20220728/waifu2x-ncnn-vulkan-20220728-windows.zip",
        "Linux": "https://github.com/nihui/waifu2x-ncnn-vulkan/releases/download/20220728/waifu2x-ncnn-vulkan-20220728-ubuntu.zip",
        "Darwin": "https://github.com/nihui/waifu2x-ncnn-vulkan/releases/download/20220728/waifu2x-ncnn-vulkan-20220728-macos.zip"
    }

    # Check if the executable exists, download if needed
    check_executable(
        "waifu2x-ncnn-vulkan",
        "waifu2x-ncnn-vulkan",  # Help text to verify the executable
        WAIFU2X_RELEASES
    )

    # For executables in a subdirectory (e.g., FFmpeg in bin/)
    FFMPEG_RELEASES = {
        "Windows": "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
        "Linux": "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz",
    }
    check_executable(
        "ffmpeg",
        "ffmpeg version",
        FFMPEG_RELEASES,
        append_to_path="bin"  # Executables are in the bin/ subdirectory
    )

Manual installation example:

.. code-block:: python

    from stouputils.installer import install_program, get_install_path, add_to_path

    # Get the appropriate installation path
    install_path = get_install_path(
        "my-program",
        ask_global=0,  # Ask user: 0=ask, 1=force global, 2=force local
        add_path=True,
        append_to_path="bin"
    )

    # Install from a URL
    success = install_program(
        "https://example.com/program.zip",
        install_path=install_path,
        program_name="my-program",
        add_path=True,
        append_to_path="bin"
    )

    # Or install from a local file
    success = install_program(
        "/path/to/program.zip",
        install_path=install_path,
        program_name="my-program"
    )

    # Manually add to PATH if needed
    if success:
        add_to_path(f"{install_path}/bin")
"""

# Imports
from .common import *
from .downloader import *
from .linux import *
from .main import *
from .windows import *

