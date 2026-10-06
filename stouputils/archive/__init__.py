"""
📦 This module provides functions for creating and managing archives.

- :py:func:`~repair.repair.repair_zip_file` - Try to repair a corrupted zip file by ignoring some of the errors
- :py:func:`~creation.make_archive` - Create a zip archive from a source directory with consistent file timestamps.
- :py:func:`~cli.archive_cli` - Main entry point for command line usage

.. code-block:: python

	import zipfile
	from pathlib import Path
	import stouputils as stp

	# Create a folder with 50 small text files
	for index in range(50):
		stp.super_open(f"project/notes/note_{index}.txt", "w").write(f"Note {index}. " * 500)

	# Zip the folder
	stp.make_archive("project", "project.zip")

	# Keep only the first two thirds of the zip, like an interrupted download
	content = Path("project.zip").read_bytes()
	two_thirds = len(content) * 2 // 3
	Path("partial.zip").write_bytes(content[:two_thirds])

	# Python's zipfile refuses to open it
	try:
		zipfile.ZipFile("partial.zip")
	except zipfile.BadZipFile as error:
		stp.warning("zipfile cannot open partial.zip:", error)

	# stouputils still recovers the files it can read
	stp.repair_zip_file("partial.zip", "repaired.zip")
	recovered_files = zipfile.ZipFile("repaired.zip").namelist()
	stp.info("Recovered", len(recovered_files), "of 50 files")

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/archive_module.svg
  :alt: Terminal output of the example, the truncated archive failing to open then being repaired
"""

# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
from .cli import (
	archive_cli as archive_cli,
)
from .creation import (
	make_archive as make_archive,
	matches_any as matches_any,
	zip_folder as zip_folder,
)
from .repair import (
	CentralEntry as CentralEntry,
	LocalHeader as LocalHeader,
	RecoveredArchive as RecoveredArchive,
	ZipScanner as ZipScanner,
	repair_zip_file as repair_zip_file,
)

if __name__ == "__main__":
	archive_cli()

