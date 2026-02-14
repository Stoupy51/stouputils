"""
This module provides functions for creating and managing archives.

- :py:func:`~repair_zip_file.repair_zip_file` - Try to repair a corrupted zip file by ignoring some of the errors
- :py:func:`~make_archive.make_archive` - Create a zip archive from a source directory with consistent file timestamps.
- :py:func:`~cli.archive_cli` - Main entry point for command line usage

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/archive_module.gif
  :alt: stouputils archive examples
"""

# Imports
from .cli import *
from .make_archive import *
from .repair_zip_file import *  # pyright: ignore[reportGeneralTypeIssues]

if __name__ == "__main__":
	archive_cli()

