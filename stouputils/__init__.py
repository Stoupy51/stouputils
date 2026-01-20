""" Stouputils is a collection of utility modules designed to simplify and enhance the development process.
It includes a range of tools for tasks such as execution of doctests, display utilities, decorators, as well as context managers.

Check the documentation for more details: https://stoupy51.github.io/stouputils/
"""
# Version (handle case where the package is not installed)
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as importlib_version

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
from .typing import *
from .version_pkg import *

try:
	__version__: str = importlib_version("stouputils")
except PackageNotFoundError:
	__version__: str = "0.0.0-dev"

