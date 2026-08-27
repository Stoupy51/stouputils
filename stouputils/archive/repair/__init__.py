"""
This module provides the recovery of zip archives that the standard library refuses to open.

- :py:func:`~repair.repair_zip_file` - Try to repair a corrupted zip file by ignoring some of the errors
- :py:class:`~scanner.ZipScanner` - Byte level view over a damaged archive, tolerant to broken offsets
"""

# Lazy imports (PEP 810), ignored before Python 3.15
from ...lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
from .repair import (
	RecoveredArchive as RecoveredArchive,
	repair_zip_file as repair_zip_file,
)
from .scanner import (
	CentralEntry as CentralEntry,
	LocalHeader as LocalHeader,
	ZipScanner as ZipScanner,
)

