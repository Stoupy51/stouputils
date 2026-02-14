"""
This module provides utilities for file management.

- :py:func:`~json.json_dump`: Writes the provided data to a JSON file with a specified indentation depth.
- :py:func:`~json.json_load`: Load a JSON file from the given path
- :py:func:`~csv.csv_dump`: Writes data to a CSV file with customizable options
- :py:func:`~csv.csv_load`: Load a CSV file from the given path
- :py:func:`~path.get_root_path`: Get the absolute path of the directory
- :py:func:`~path.relative_path`: Get the relative path of a file relative to a given directory
- :py:func:`~path.super_copy`: Copy a file (or a folder) from the source to the destination (always create the directory)
- :py:func:`~path.super_open`: Open a file with the given mode, creating the directory if it doesn't exist (only if writing)
- :py:func:`~path.replace_tilde`: Replace the "~" by the user's home directory
- :py:func:`~path.clean_path`: Clean the path by replacing backslashes with forward slashes and simplifying the path
- :py:func:`~redirect.copytree_with_progress`: Copy a directory tree with a colored progress bar
- :py:func:`~redirect.redirect_folder`: Move a folder and create a junction/symlink at the original location
- :py:func:`~utils.safe_close`: Safely close a file descriptor or file object after flushing, ignoring any exceptions

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/io_module.gif
  :alt: stouputils io examples
"""

# Imports
from .csv import *
from .json import *
from .path import *
from .redirect import *
from .utils import *

