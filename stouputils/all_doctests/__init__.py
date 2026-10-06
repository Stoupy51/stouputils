"""
✅ This module is used to run all the doctests for all the modules in a given directory.

- :py:func:`~launch.launch_tests` - Main function to launch tests for all modules in the given directory.
- :py:func:`~utils.test_module_with_progress` - Test a module with testmod and measure the time taken with progress printing.

.. code-block:: bash

	# Create a package whose docstring holds two tests, the second one wrong
	mkdir my_package
	cat > my_package/geometry.py <<'EOF'
	def area(width: float, height: float) -> float:
		''' Area of a rectangle.

		>>> area(2, 3)
		6
		>>> area(2.5, 2)
		5
		'''
		return width * height
	EOF

	# Run every doctest of the package
	stouputils all_doctests my_package

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/all_doctests_module.svg
  :alt: Terminal output of the example, one doctest failing
"""

# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
from .launch import (
	filter_modules as filter_modules,
	find_modules as find_modules,
	import_modules as import_modules,
	launch_tests as launch_tests,
	report_results as report_results,
)
from .reexports import (
	find_missing_reexports as find_missing_reexports,
	module_public_names as module_public_names,
)
from .utils import (
	test_module_with_progress as test_module_with_progress,
)

