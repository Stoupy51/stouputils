"""
This module is used to run all the doctests for all the modules in a given directory.

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/all_doctests_module.gif
  :alt: stouputils all_doctests examples
"""

# Imports
import importlib
import os
import pkgutil
import sys
from doctest import TestResults, testmod
from types import ModuleType

from . import decorators
from .decorators import LogLevels, measure_time
from .print import error, info, progress, warning
from .io import clean_path, relative_path


def test_module_with_progress(module: ModuleType, separator: str) -> TestResults:
	@measure_time(progress, message=f"Testing module '{module.__name__}' {separator}took")
	def internal() -> TestResults:
		return testmod(m=module)
	return internal()

# Main program
def launch_tests(root_dir: str, importing_errors: LogLevels = LogLevels.WARNING_TRACEBACK, strict: bool = True) -> int:
	""" Main function to launch tests for all modules in the given directory.

	Args:
		root_dir				(str):			Root directory to search for modules
		importing_errors		(LogLevels):	Log level for the errors when importing modules
		strict					(bool):			Modify the force_raise_exception variable to True in the decorators module

	Returns:
		int: The number of failed tests

	Examples:
		>>> launch_tests("unknown_dir")
		Traceback (most recent call last):
			...
		ValueError: No modules found in 'unknown_dir'

	.. code-block:: python

		> if launch_tests("/path/to/source") > 0:
			sys.exit(1)
		[PROGRESS HH:MM:SS] Importing module 'module1'	took 0.001s
		[PROGRESS HH:MM:SS] Importing module 'module2'	took 0.002s
		[PROGRESS HH:MM:SS] Importing module 'module3'	took 0.003s
		[PROGRESS HH:MM:SS] Importing module 'module4'	took 0.004s
		[INFO HH:MM:SS] Testing 4 modules...
		[PROGRESS HH:MM:SS] Testing module 'module1'	took 0.005s
		[PROGRESS HH:MM:SS] Testing module 'module2'	took 0.006s
		[PROGRESS HH:MM:SS] Testing module 'module3'	took 0.007s
		[PROGRESS HH:MM:SS] Testing module 'module4'	took 0.008s
	"""
	if strict:
		old_value: bool = strict
		decorators.force_raise_exception = True
		strict = old_value
	
	# Get the path of the directory to check modules from
	working_dir: str = clean_path(os.getcwd())
	root_dir = clean_path(os.path.abspath(root_dir))
	dir_to_check: str = os.path.dirname(root_dir) if working_dir != root_dir else root_dir

	# Get all modules from folder
	sys.path.insert(0, dir_to_check)
	modules_file_paths: list[str] = []
	for directory_path, _, _ in os.walk(root_dir):
		directory_path = clean_path(directory_path)
		for module_info in pkgutil.walk_packages([directory_path]):

			# Extract root and module name
			module_root: str = str(module_info.module_finder.path)	# type: ignore
			module_name: str = module_info.name.split(".")[-1]

			# Get the absolute path
			absolute_module_path: str = clean_path(os.path.join(module_root, module_name))

			# Check if the module is in the root directory that we want to check
			if root_dir in absolute_module_path:

				# Get the path of the module like 'stouputils.io'
				path: str = absolute_module_path.split(dir_to_check, 1)[1].replace("/", ".")[1:]

				# If the module is not already in the list, add it
				if path not in modules_file_paths:
					modules_file_paths.append(path)

	# If no modules are found, raise an error
	if not modules_file_paths:
		raise ValueError(f"No modules found in '{relative_path(root_dir)}'")

	# Find longest module path for alignment
	max_length: int = max(len(path) for path in modules_file_paths)

	# Dynamically import all modules from iacob package recursively using pkgutil and importlib
	modules: list[ModuleType] = []
	separators: list[str] = []
	for module_path in modules_file_paths:
		separator: str = " " * (max_length - len(module_path))

		@measure_time(progress, message=f"Importing module '{module_path}' {separator}took")
		def internal(a: str = module_path, b: str = separator) -> None:
			modules.append(importlib.import_module(a))
			separators.append(b)
		
		try:
			internal()
		except Exception as e:
			warning(f"Failed to import module '{module_path}': ({type(e).__name__}) {e}")

	# Run tests for each module
	info(f"Testing {len(modules)} modules...")
	separators = [s + " "*(len("Importing") - len("Testing")) for s in separators]
	results: list[TestResults] = [
		test_module_with_progress(module, separator)
		for module, separator in zip(modules, separators, strict=False)
	]

	# Display any error lines for each module at the end of the script
	nb_failed_tests: int = 0
	for module, result in zip(modules, results, strict=False):
		if result.failed > 0:
			error(f"Errors in module {module.__name__}", exit=False)
			nb_failed_tests += result.failed

	# Reset force_raise_exception back
	decorators.force_raise_exception = strict

	# Return the number of failed tests
	return nb_failed_tests

