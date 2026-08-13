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

# Lazy imports (PEP 810), ignored before Python 3.15
__lazy_modules__: frozenset[str] = frozenset({
	"stouputils.io.csv",
	"stouputils.io.json",
	"stouputils.io.path",
	"stouputils.io.redirect",
	"stouputils.io.utils",
})

# Imports
from .csv import (
	csv_dump as csv_dump,
	csv_load as csv_load,
)
from .json import (
	json_dump as json_dump,
	json_load as json_load,
)
from .path import (
	clean_path as clean_path,
	get_root_path as get_root_path,
	read_file as read_file,
	relative_path as relative_path,
	replace_tilde as replace_tilde,
	super_copy as super_copy,
	super_open as super_open,
)
from .redirect import (
	copytree_with_progress as copytree_with_progress,
	create_bind_mount as create_bind_mount,
	create_junction as create_junction,
	is_junction as is_junction,
	redirect_cli as redirect_cli,
	redirect_folder as redirect_folder,
)
from .utils import (
	safe_close as safe_close,
)

