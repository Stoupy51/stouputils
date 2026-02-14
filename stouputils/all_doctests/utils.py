"""
This module is used to run all the doctests for all the modules in a given directory.

- :py:func:`launch_tests` - Main function to launch tests for all modules in the given directory.
- :py:func:`test_module_with_progress` - Test a module with testmod and measure the time taken with progress printing.

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/all_doctests_module.gif
  :alt: stouputils all_doctests examples
"""

# Imports
from typing import TYPE_CHECKING

from ..ctx.measure_time import MeasureTime

if TYPE_CHECKING:
	from doctest import TestResults
	from types import ModuleType


# Main program
def test_module_with_progress(module: "ModuleType", separator: str) -> "TestResults":
	""" Test a module with testmod and measure the time taken with progress printing.

	Args:
		module		(ModuleType):	Module to test
		separator	(str):			Separator string for alignment in output
	Returns:
		TestResults: The results of the tests
	"""
	from doctest import testmod
	with MeasureTime(message=f"Testing module '{module.__name__}' {separator}took"):
		return testmod(m=module)

