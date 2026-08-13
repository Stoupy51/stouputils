"""
This module is used to run all the doctests for all the modules in a given directory.

- :py:func:`~launch.launch_tests` - Main function to launch tests for all modules in the given directory.
- :py:func:`~utils.test_module_with_progress` - Test a module with testmod and measure the time taken with progress printing.

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/all_doctests_module.gif
  :alt: stouputils all_doctests examples
"""

# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
from .launch import (
	launch_tests as launch_tests,
)
from .reexports import (
	find_missing_reexports as find_missing_reexports,
	module_public_names as module_public_names,
)
from .utils import (
	test_module_with_progress as test_module_with_progress,
)

