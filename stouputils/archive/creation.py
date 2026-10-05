
# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import fnmatch
import os
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from ..decorators import LogLevels, handle_error
from ..io.path import clean_path, super_copy


# Function that makes an archive with consistency (same zip file each time)
@handle_error
def make_archive(
	source: str,
	destinations: list[str] | str | None = None,
	override_time: tuple[int, int, int, int, int, int] | None = None,
	create_dir: bool = False,
	ignore_patterns: str | None = None,
) -> bool:
	""" Create a zip archive from a source directory with consistent file timestamps.
	(Meaning deterministic zip file each time)

	Creates a zip archive from the source directory and copies it to one or more destinations.
	The archive will have consistent file timestamps across runs if override_time is specified.
	Uses maximum compression level (9) with ZIP_DEFLATED algorithm.

	Args:
		source:          The source folder to archive
		destinations:    The destination folder(s) or file(s) to copy the archive to
		override_time:   The constant time to use for the archive
			(e.g. (2024, 1, 1, 0, 0, 0) for 2024-01-01 00:00:00)
		create_dir:      Whether to create the destination directory if it doesn't exist
		ignore_patterns: Glob pattern(s) of the files to ignore, one pattern or several separated by commas
			(e.g. "*.pyc" or "*.pyc,__pycache__,*.log")
	Returns:
		Always returns True unless any strong error

	.. code-block:: python

		> make_archive("/path/to/source", "/path/to/destination.zip")
		> make_archive("/path/to/source", ["/path/to/destination.zip", "/path/to/destination2.zip"])
		> make_archive("src", "hello_from_year_2085.zip", override_time=(2085,1,1,0,0,0))
		> make_archive("src", "output.zip", ignore_patterns="*.pyc")
		> make_archive("src", "output.zip", ignore_patterns="__pycache__")
		> make_archive("src", "output.zip", ignore_patterns="*.pyc,__pycache__,*.log")
	"""
	if not destinations:
		raise ValueError("destinations must be a list of at least one destination")

	# A destination ending with "/" is a directory, receiving the archive under the source's name
	destinations = [
		os.path.join(dest, os.path.basename(source) + ".zip") if dest.endswith("/") else dest
		for dest in ([destinations] if isinstance(destinations, str) else destinations)
	]

	# Create the archive, the copies creating their own folders when they are made
	destination: str = clean_path(destinations[0])
	destination = destination if ".zip" in destination else destination + ".zip"
	if create_dir and os.path.dirname(destination):
		os.makedirs(os.path.dirname(destination), exist_ok=True)
	ignore_pattern_list: list[str] = [pattern.strip() for pattern in ignore_patterns.split(",")] if ignore_patterns else []
	zip_folder(source, destination, ignore_pattern_list, override_time)

	# Copy the archive to the destination(s)
	for dest_file in destinations[1:]:
		message: str = f"Unable to copy '{destination}' to '{dest_file}'"
		copy = handle_error(super_copy, exceptions=Exception, message=message, error_log=LogLevels.WARNING)
		copy(destination, clean_path(dest_file), create_dir=create_dir)
	return True


def zip_folder(
	source: str, destination: str, ignore_patterns: list[str], override_time: tuple[int, int, int, int, int, int] | None
) -> None:
	""" Write every file under ``source`` into a new zip at maximum compression, at its path relative to ``source``.

	Args:
		ignore_patterns: Glob patterns of the files and folders left out, matched as in :func:`matches_any`.
		override_time:   Timestamp given to every entry, which makes the archive the same byte for byte, None to keep the file dates.
	"""
	with ZipFile(destination, "w", compression=ZIP_DEFLATED, compresslevel=9) as zip:
		for root, dirs, files in os.walk(source):
			# Filter out ignored directories in-place to prevent walking into them
			dirs[:] = [d for d in dirs if not matches_any(d, ignore_patterns)]
			for file in files:
				file_path: str = clean_path(os.path.join(root, file))
				rel_path: str = os.path.relpath(file_path, source)
				if matches_any(file, ignore_patterns) or matches_any(rel_path, ignore_patterns):
					continue
				info: ZipInfo = ZipInfo(rel_path)
				info.compress_type = ZIP_DEFLATED
				if override_time:
					info.date_time = override_time
				with open(file_path, "rb") as f:
					zip.writestr(info, f.read())


def matches_any(path: str, patterns: list[str]) -> bool:
	""" Whether the path, or its last component, matches one of the glob patterns.

	>>> matches_any("src/cache/data.pyc", ["*.pyc"]), matches_any("src/__pycache__", ["__pycache__"]), matches_any("a.py", [])
	(True, True, False)
	"""
	return any(fnmatch.fnmatch(os.path.basename(path), pattern) or fnmatch.fnmatch(path, pattern) for pattern in patterns)

