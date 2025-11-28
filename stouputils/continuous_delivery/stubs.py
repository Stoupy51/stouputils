""" This module contains utilities for generating stub files using stubgen.

- generate_stubs: Generate stub files for a Python package using stubgen
- stubs_full_routine: Generate stub files for a Python package

"""

# Imports
import os
from collections.abc import Callable

from ..decorators import LogLevels, handle_error


def generate_stubs(
	package_name: str,
	extra_args: str = "--include-docstrings --include-private",
) -> int:
	""" Generate stub files for a Python package using stubgen.

	Note: stubgen generates stubs in the 'out' directory by default in the current working directory.

	Args:
		package_name  (str): Name of the package to generate stubs for.
		extra_args    (str): Extra arguments to pass to stubgen. Defaults to "--include-docstrings --include-private".
	Returns:
		int: Return code of the os.system call.
	"""
	from mypy.stubgen import main as stubgen_main
	try:
		stubgen_main(["-p", package_name, *extra_args.split()])
		return 0
	except Exception:
		return 1

def clean_stubs_directory(output_directory: str, package_name: str) -> None:
	""" Clean the stubs directory by deleting all .pyi files.

	Args:
		output_directory  (str): Directory to clean.
		package_name      (str): Package name subdirectory. Only cleans output_directory/package_name.
	"""
	target_dir: str = os.path.join(output_directory, package_name)
	if os.path.exists(target_dir):
		for root, _, files in os.walk(target_dir):
			for file in files:
				if file.endswith(".pyi"):
					os.remove(os.path.join(root, file))

@handle_error(message="Error while doing the stubs full routine", error_log=LogLevels.ERROR_TRACEBACK)
def stubs_full_routine(
	package_name: str,
	output_directory: str = "typings",
	extra_args: str = "--include-docstrings --include-private",
	clean_before: bool = False,

	generate_stubs_function: Callable[[str, str], int] = generate_stubs,
	clean_stubs_function: Callable[[str, str], None] = clean_stubs_directory,
) -> None:
	""" Generate stub files for a Python package using stubgen.

	Note: stubgen generates stubs in the 'out' directory by default in the current working directory.

	Args:
		package_name              (str):                       Name of the package to generate stubs for.
		output_directory          (str):                       Directory to clean before generating stubs. Defaults to "typings".
			This parameter is used for cleaning the directory before stub generation.
		extra_args                (str):                       Extra arguments to pass to stubgen. Defaults to "--include-docstrings --include-private".
		clean_before              (bool):                      Whether to clean the output directory before generating stubs. Defaults to False.
		generate_stubs_function   (Callable[[str, str], int]): Function to generate stubs.
			Defaults to :func:`generate_stubs`.
		clean_stubs_function      (Callable[[str], None]):     Function to clean the stubs directory.
			Defaults to :func:`clean_stubs_directory`.
	Raises:
		Exception: If stub generation fails.
	"""
	if clean_before:
		clean_stubs_function(output_directory, package_name)
	extra_args += f" -o {output_directory}"

	if generate_stubs_function(package_name, extra_args) != 0:
		raise Exception(f"Error while generating stubs for {package_name}")

