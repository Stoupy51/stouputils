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

# Imports
from .all_doctests import *
from .archive import *
from .backup import *
from .collections import *

# Folders
from .continuous_delivery import *
from .ctx import *
from .decorators import *
from .image import *
from .io import *
from .parallel import *
from .print import *

# Version (handle case where the package is not installed)
import importlib.metadata

try:
	__version__: str = importlib.metadata.version("stouputils")
except importlib.metadata.PackageNotFoundError:
	__version__: str = "0.0.0-dev"

