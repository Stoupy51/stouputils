""" This module contains utilities for PyPI.

- pypi_full_routine: Upload the most recent file(s) to PyPI after updating pip and required packages and building the package

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/continuous_delivery/pypi_module.gif
  :alt: stouputils pypi examples
"""

# Imports
import os
import sys
from collections.abc import Callable

from ..decorators import LogLevels, handle_error


def update_pip_and_required_packages() -> int:
	""" Update pip and required packages.

	Returns:
		int: Return code of the os.system call.
	"""
	return os.system(f"{sys.executable} -m pip install --upgrade pip setuptools build twine pkginfo packaging")

def build_package() -> int:
	""" Build the package.

	Returns:
		int: Return code of the os.system call.
	"""
	return os.system(f"{sys.executable} -m build")

def upload_package(repository: str, filepath: str) -> int:
	""" Upload the package to PyPI.

	Args:
		repository  (str): Repository to upload to.
		filepath    (str): Path to the file to upload.

	Returns:
		int: Return code of the os.system call.
	"""
	return os.system(f"{sys.executable} -m twine upload --verbose -r {repository} {filepath}")

@handle_error(message="Error while doing the pypi full routine", error_log=LogLevels.ERROR_TRACEBACK)
def pypi_full_routine(
	repository: str,
	dist_directory: str,
	last_files: int = 1,
	endswith: str = ".tar.gz",

	update_all_function: Callable[[], int] = update_pip_and_required_packages,
	build_package_function: Callable[[], int] = build_package,
	upload_package_function: Callable[[str, str], int] = upload_package,
) -> None:
	""" Upload the most recent file(s) to PyPI after updating pip and required packages and building the package.

	Args:
		repository               (str):                        Repository to upload to.
		dist_directory           (str):                        Directory to upload from.
		last_files               (int):                        Number of most recent files to upload. Defaults to 1.
		endswith                 (str):                        End of the file name to upload. Defaults to ".tar.gz".
		update_all_function      (Callable[[], int]):          Function to update pip and required packages.
			Defaults to :func:`update_pip_and_required_packages`.
		build_package_function   (Callable[[], int]):          Function to build the package.
			Defaults to :func:`build_package`.
		upload_package_function  (Callable[[str, str], int]):  Function to upload the package.
			Defaults to :func:`upload_package`.

	Returns:
		int: Return code of the command.
	"""
	if update_all_function() != 0:
		raise Exception("Error while updating pip and required packages")

	if build_package_function() != 0:
		raise Exception("Error while building the package")

	# Get list of tar.gz files in dist directory sorted by modification time
	files: list[str] = sorted(
		[x for x in os.listdir(dist_directory) if x.endswith(endswith)],	# Get list of tar.gz files in dist directory
		key=lambda x: os.path.getmtime(f"{dist_directory}/{x}"),			# Sort by modification time
		reverse=True														# Sort in reverse order
	)

	# Upload the most recent file(s)
	for file in files[:last_files]:
		upload_package_function(repository, f"{dist_directory}/{file}")


