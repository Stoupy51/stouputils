"""
This module provides functions for creating and managing archives.

- :py:func:`~repair_zip_file.repair_zip_file` - Try to repair a corrupted zip file by ignoring some of the errors
- :py:func:`~make_archive.make_archive` - Create a zip archive from a source directory with consistent file timestamps.
- :py:func:`~cli.archive_cli` - Main entry point for command line usage

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/archive_module.gif
  :alt: stouputils archive examples
"""

# Lazy imports (PEP 810), ignored before Python 3.15
__lazy_modules__: frozenset[str] = frozenset({
	"stouputils.archive.cli",
})

# Imports
from .cli import (
	archive_cli as archive_cli,
)
from .make_archive import (
	make_archive as make_archive,
)
from .repair_zip_file import (
	repair_zip_file as repair_zip_file,
)

if __name__ == "__main__":
	archive_cli()

