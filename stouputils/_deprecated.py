""" Deprecated functions and classes.
::deprecated:: vX.Y.Z - Description of deprecation reason and alternative (if applicable)

This module contains deprecated functions that have been replaced by new implementations
These functions are retained for backward compatibility and will log deprecation warnings when used.
"""

# Imports
from typing import Any

from .decorators import LogLevels, deprecated
from .io.csv import csv_dump, csv_load
from .io.json import json_dump, json_load


# Deprecated functions
@deprecated(message="super_csv_dump has been renamed to csv_dump.", version="v1.8.0", error_log=LogLevels.WARNING)
def super_csv_dump(*args: Any, **kwargs: Any) -> Any:
	""" Deprecated function, use :py:func:`~stouputils.io.csv.csv_dump` instead. """
	return csv_dump(*args, **kwargs)


@deprecated(message="super_csv_load has been renamed to csv_load.", version="v1.8.0", error_log=LogLevels.WARNING)
def super_csv_load(*args: Any, **kwargs: Any) -> Any:
	""" Deprecated function, use :py:func:`~stouputils.io.csv.csv_load` instead. """
	return csv_load(*args, **kwargs)


@deprecated(message="super_json_dump has been renamed to json_dump.", version="v1.8.0", error_log=LogLevels.WARNING)
def super_json_dump(*args: Any, **kwargs: Any) -> Any:
	""" Deprecated function, use :py:func:`~stouputils.io.json.json_dump` instead. """
	return json_dump(*args, **kwargs)


@deprecated(message="super_json_load has been renamed to json_load.", version="v1.8.0", error_log=LogLevels.WARNING)
def super_json_load(*args: Any, **kwargs: Any) -> Any:
	""" Deprecated function, use :py:func:`~stouputils.io.json.json_load` instead. """
	return json_load(*args, **kwargs)

