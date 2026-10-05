
# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
from typing import TYPE_CHECKING

from ..config import StouputilsConfig as Cfg
from ..ctx.measure_time import MeasureTime
from ..io.path import clean_path, relative_path
from ..print.message import error, info, progress, warning
from .utils import test_module_with_progress

if TYPE_CHECKING:
	from doctest import TestResults
	from types import ModuleType


# Main program
def launch_tests(root_dir: str, strict: bool = True, pattern: str = "*") -> int:
	""" Main function to launch tests for all modules in the given directory.

	Args:
		root_dir: Root directory to search for modules
		strict:   Modify the FORCE_RAISE_EXCEPTION configuration to True
		pattern:  Pattern to filter module names (fnmatch style, e.g., '*typ*', 'io', etc.)
	Returns:
		The number of failed tests
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
	old_value: bool = Cfg.FORCE_RAISE_EXCEPTION
	if strict:
		Cfg.FORCE_RAISE_EXCEPTION = True

	try:
		# Get the path of the directory to check modules from
		import os
		import sys
		working_dir: str = clean_path(os.getcwd())
		root_dir = clean_path(os.path.abspath(root_dir))
		dir_to_check: str = os.path.dirname(root_dir) if working_dir != root_dir else root_dir
		sys.path.insert(0, dir_to_check)

		modules, separators = import_modules(filter_modules(find_modules(root_dir, dir_to_check), pattern, root_dir))
		info(f"Testing {len(modules)} modules...")
		results: list[TestResults] = [
			test_module_with_progress(module, separator + " " * (len("Importing") - len("Testing")))
			for module, separator in zip(modules, separators, strict=True)
		]
		return report_results(modules, results)
	finally:
		Cfg.FORCE_RAISE_EXCEPTION = old_value


def find_modules(root_dir: str, dir_to_check: str) -> list[str]:
	""" Dotted names of the modules under ``root_dir``, the shallowest first and then in alphabetical order.

	Args:
		dir_to_check: Folder the names are relative to, the one put on ``sys.path``.
	Raises:
		ValueError: If ``root_dir`` holds no module.
	"""
	import os
	paths: list[str] = [
		f"{clean_path(root)}/{filename}".removesuffix(".py").removesuffix("/__init__")
		for root, _, files in os.walk(root_dir)
		for filename in files
		if filename.endswith(".py")
	]
	module_paths: list[str] = list(dict.fromkeys(
		path.removeprefix(dir_to_check + "/").replace("/", ".") for path in paths if root_dir in path
	))
	if not module_paths:
		raise ValueError(f"No modules found in '{relative_path(root_dir)}'")
	return sorted(module_paths, key=lambda x: (x.count("."), x))


def filter_modules(module_paths: list[str], pattern: str, root_dir: str) -> list[str]:
	""" The module names matching an fnmatch pattern, ``"*"`` keeping them all.

	>>> filter_modules(["pkg.io", "pkg.io.csv", "pkg.typing"], "*io*", "pkg")
	['pkg.io', 'pkg.io.csv']

	Raises:
		ValueError: If no module matches, naming the candidates.
	"""
	if pattern == "*":
		return module_paths
	import fnmatch
	selected: list[str] = [path for path in module_paths if fnmatch.fnmatch(path, pattern)]
	if not selected:
		raise ValueError(
			f"No modules matching pattern '{pattern}' found in '{relative_path(root_dir)}'.\n"
			f"Candidates were: {', '.join(relative_path(p) for p in module_paths)[:500]}..."
		)
	return selected


def import_modules(module_paths: list[str]) -> "tuple[list[ModuleType], list[str]]":
	""" Import each module, timing it, and warn about the ones that fail.

	Returns:
		The imported modules, and for each one the spaces that align its timing line with the longest name.
	"""
	import importlib
	max_length: int = max(len(path) for path in module_paths)
	modules: list[ModuleType] = []
	separators: list[str] = []
	for module_path in module_paths:
		separator: str = " " * (max_length - len(module_path))
		try:
			with MeasureTime(print_func=progress, message=f"Importing module '{module_path}' {separator}took"):
				modules.append(importlib.import_module(module_path))
			separators.append(separator)
		except Exception as e:
			warning(f"Failed to import module '{module_path}': ({type(e).__name__}) {e}")
	return modules, separators


def report_results(modules: "list[ModuleType]", results: "list[TestResults]") -> int:
	""" Print the modules whose tests failed and the totals across all of them.

	Returns:
		The number of failed tests.
	"""
	for module, result in zip(modules, results, strict=True):
		if result.failed > 0:
			passed: int = result.attempted - result.failed
			error(f"Errors in module {module.__name__} ({passed}/{result.attempted} tests passed)", exit=False)
	total_failed: int = sum(result.failed for result in results)
	total_tests: int = sum(result.attempted for result in results)
	if total_failed == 0:
		info(f"All tests passed for all {len(modules)} modules! ({total_tests}/{total_tests} tests passed)")
	else:
		passed_tests: int = total_tests - total_failed
		error(f"Some tests failed: {passed_tests}/{total_tests} tests passed in total across {len(modules)} modules", exit=False)
	return total_failed

