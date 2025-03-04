"""
This module is used to run all the doctests for all the modules in a given directory.

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/all_doctests_module.gif
  :alt: stouputils all_doctests examples
"""

# Imports
import os
import sys
from .print import info, error, progress
from .decorators import measure_time, handle_error, LogLevels
from . import decorators
from doctest import TestResults, testmod
from types import ModuleType
import importlib
import pkgutil

def test_module_with_progress(module: ModuleType, separator: str) -> TestResults:
	@measure_time(progress, message=f"Testing module '{module.__name__}' {separator}took")
	def internal() -> TestResults:
		return testmod(m=module)
	return internal()

# Main program
def launch_tests(root_dir: str, importing_errors: LogLevels = LogLevels.WARNING_TRACEBACK, strict: bool = True) -> None:
	""" Main function to launch tests for all modules in the given directory.

	Args:
		root_dir				(str):			Root directory to search for modules
		importing_errors		(LogLevels):	Log level for the errors when importing modules
		strict					(bool):			Modify the force_raise_exception variable to True in the decorators module
	
	Examples:
		>>> launch_tests("unknown_dir")
		Traceback (most recent call last):
			...
		ValueError: No modules found in 'unknown_dir'

	.. code-block:: python

		> launch_tests("/path/to/source")
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


	# Get all modules from folder
	sys.path.insert(0, root_dir)
	modules_file_paths: list[str] = []
	for directory_path, _, _ in os.walk(root_dir):
		for module_info in pkgutil.walk_packages([directory_path]):
			absolute_module_path: str = os.path.join(directory_path, module_info.name)
			path: str = absolute_module_path.split(root_dir, 1)[1].replace(os.sep, ".")[1:]
			if path not in modules_file_paths:
				modules_file_paths.append(path)
	if not modules_file_paths:
		raise ValueError(f"No modules found in '{root_dir}'")

	# Find longest module path for alignment
	max_length: int = max(len(path) for path in modules_file_paths)

	# Dynamically import all modules from iacob package recursively using pkgutil and importlib
	modules: list[ModuleType] = []
	separators: list[str] = []
	for module_path in modules_file_paths:
		separator: str = " " * (max_length - len(module_path))
		@handle_error(error_log=importing_errors)
		@measure_time(progress, message=f"Importing module '{module_path}' {separator}took")
		def internal() -> None:
			modules.append(importlib.import_module(module_path))
			separators.append(separator)
		internal()

	# Run tests for each module
	info(f"Testing {len(modules)} modules...")
	separators = [s + " "*(len("Importing") - len("Testing")) for s in separators]
	results: list[TestResults] = [test_module_with_progress(module, separator) for module, separator in zip(modules, separators)]

	# Display any error lines for each module at the end of the script
	for module, result in zip(modules, results):
		if result.failed > 0:
			error(f"Errors in module {module.__name__}", exit=False)

	# Reset force_raise_exception back
	decorators.force_raise_exception = strict

