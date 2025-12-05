""" A collection of utility modules designed to simplify and enhance the development process.

This package provides various tools and utilities for common development tasks including:

Key Features:
- Continuous delivery utilities (GitHub, PyPI)
- Display and logging utilities (print)
- File and I/O management (io)
- Decorators for common patterns
- Context managers
- Archive and backup tools
- Parallel processing helpers
- Collection utilities
- Doctests utilities

"""
# ruff: noqa: F403

# Version (handle case where the package is not installed)
from importlib.metadata import PackageNotFoundError, version

# Imports
from ._deprecated import *
from .all_doctests import *
from .archive import *
from .backup import *
from .collections import *
from .continuous_delivery import *
from .ctx import *
from .decorators import *
from .image import *
from .io import *
from .parallel import *
from .print import *

try:
	__version__: str = version("stouputils")
except PackageNotFoundError:
	__version__: str = "0.0.0-dev"

