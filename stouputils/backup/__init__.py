"""
This module provides utilities for backup management.

- :py:func:`~cli.backup_cli` - Main entry point for command line usage
- :py:func:`~create.create_delta_backup` - Creates a ZIP delta backup, saving only modified or new files while tracking deleted files
- :py:func:`~consolidate.consolidate_backups` - Consolidates the files from the given backup and all previous ones into a new ZIP file
- :py:func:`~limiter.limit_backups` - Limits the number of delta backups by consolidating the oldest ones
- :py:func:`~hash.get_file_hash` - Computes the SHA-256 hash of a file
- :py:func:`~hash.extract_hash_from_zipinfo` - Extracts the stored hash from a ZipInfo object's comment
- :py:func:`~retrieve.get_all_previous_backups` - Retrieves all previous backups in a folder and maps each backup to a dictionary of file paths and their hashes
- :py:func:`~retrieve.is_file_in_any_previous_backup` - Checks if a file with the same hash exists in any previous backup

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/backup_module.gif
  :alt: stouputils backup examples
"""

# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
from .cli import (
	backup_cli as backup_cli,
)
from .consolidate import (
	consolidate_backups as consolidate_backups,
)
from .create import (
	add_file_to_zip as add_file_to_zip,
	create_delta_backup as create_delta_backup,
)
from .hash import (
	extract_hash_from_zipinfo as extract_hash_from_zipinfo,
	get_file_hash as get_file_hash,
)
from .limiter import (
	limit_backups as limit_backups,
)
from .retrieve import (
	get_all_previous_backups as get_all_previous_backups,
	get_backup_sort_key as get_backup_sort_key,
	is_file_in_any_previous_backup as is_file_in_any_previous_backup,
)

if __name__ == "__main__":
	backup_cli()

