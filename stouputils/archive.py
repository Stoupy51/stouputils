"""
This module provides functions for creating and managing archives.

- make_archive: Create a zip archive from a source directory with consistent file timestamps.
- repair_zip_file: Try to repair a corrupted zip file by ignoring some of the errors

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/archive_module.gif
  :alt: stouputils archive examples
"""

# pyright: reportUnusedVariable=false
# Imports
import fnmatch
import os
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from .decorators import LogLevels, handle_error
from .io import clean_path, super_copy


# Function that makes an archive with consistency (same zip file each time)
@handle_error()
def make_archive(
	source: str,
	destinations: list[str] | str | None = None,
	override_time: None | tuple[int, int, int, int, int, int] = None,
	create_dir: bool = False,
	ignore_patterns: str | None = None,
) -> bool:
	""" Create a zip archive from a source directory with consistent file timestamps.
	(Meaning deterministic zip file each time)

	Creates a zip archive from the source directory and copies it to one or more destinations.
	The archive will have consistent file timestamps across runs if override_time is specified.
	Uses maximum compression level (9) with ZIP_DEFLATED algorithm.

	Args:
		source				(str):						The source folder to archive
		destinations		(list[str]|str):			The destination folder(s) or file(s) to copy the archive to
		override_time		(None | tuple[int, ...]):	The constant time to use for the archive
			(e.g. (2024, 1, 1, 0, 0, 0) for 2024-01-01 00:00:00)
		create_dir			(bool):						Whether to create the destination directory if it doesn't exist
		ignore_patterns		(str | None):				Glob pattern(s) to ignore files. Can be a single pattern or comma-separated patterns (e.g. "*.pyc" or "*.pyc,__pycache__,*.log")
	Returns:
		bool: Always returns True unless any strong error
	Examples:

	.. code-block:: python

		> make_archive("/path/to/source", "/path/to/destination.zip")
		> make_archive("/path/to/source", ["/path/to/destination.zip", "/path/to/destination2.zip"])
		> make_archive("src", "hello_from_year_2085.zip", override_time=(2085,1,1,0,0,0))
		> make_archive("src", "output.zip", ignore_patterns="*.pyc")
		> make_archive("src", "output.zip", ignore_patterns="__pycache__")
		> make_archive("src", "output.zip", ignore_patterns="*.pyc,__pycache__,*.log")
	"""
	# Fix copy_destinations type if needed
	if destinations is None:
		destinations = []
	if destinations and isinstance(destinations, str):
		destinations = [destinations]
	if not destinations:
		raise ValueError("destinations must be a list of at least one destination")

	# Create directories if needed
	if create_dir:
		for dest_file in destinations:
			dest_file = clean_path(dest_file)
			parent_dir = os.path.dirname(dest_file)
			if parent_dir and not os.path.exists(parent_dir):
				os.makedirs(parent_dir, exist_ok=True)

	# Create the archive
	destination: str = clean_path(destinations[0])
	destination = destination if ".zip" in destination else destination + ".zip"

	# Parse ignore patterns (can be a single pattern or comma-separated patterns)
	ignore_pattern_list: list[str] = []
	if ignore_patterns:
		ignore_pattern_list = [pattern.strip() for pattern in ignore_patterns.split(',')]

	def should_ignore(path: str) -> bool:
		"""Check if a file or directory path should be ignored based on patterns."""
		if not ignore_pattern_list:
			return False
		for pattern in ignore_pattern_list:
			if fnmatch.fnmatch(os.path.basename(path), pattern) or fnmatch.fnmatch(path, pattern):
				return True
		return False

	with ZipFile(destination, "w", compression=ZIP_DEFLATED, compresslevel=9) as zip:
		for root, dirs, files in os.walk(source):
			# Filter out ignored directories in-place to prevent walking into them
			dirs[:] = [d for d in dirs if not should_ignore(d)]

			for file in files:
				file_path: str = clean_path(os.path.join(root, file))
				rel_path = os.path.relpath(file_path, source)

				# Skip files that match any ignore pattern
				if should_ignore(file) or should_ignore(rel_path):
					continue

				info: ZipInfo = ZipInfo(rel_path)
				info.compress_type = ZIP_DEFLATED
				if override_time:
					info.date_time = override_time
				with open(file_path, "rb") as f:
					zip.writestr(info, f.read())

	# Copy the archive to the destination(s)
	for dest_file in destinations[1:]:
		@handle_error(Exception, message=f"Unable to copy '{destination}' to '{dest_file}'", error_log=LogLevels.WARNING)
		def internal(src: str, dest: str) -> None:
			super_copy(src, dest, create_dir=create_dir)
		internal(destination, clean_path(dest_file))

	return True



# Function that repair a corrupted zip file (ignoring some of the errors)
@handle_error()
def repair_zip_file(file_path: str, destination: str) -> bool:
	""" Try to repair a corrupted zip file by ignoring some of the errors

	This function manually parses the ZIP file structure to extract files
	even when the ZIP file is corrupted. It reads the central directory
	entries and attempts to decompress each file individually.

	Args:
		file_path		(str):	Path of the zip file to repair
		destination		(str):	Destination of the new file
	Returns:
		bool: Always returns True unless any strong error

	Examples:

	.. code-block:: python

		> repair_zip_file("/path/to/source.zip", "/path/to/destination.zip")
	"""
	import struct
	import zlib

	# Check
	if not os.path.exists(file_path):
		raise FileNotFoundError(f"File '{file_path}' not found")
	dirname: str = os.path.dirname(destination)
	if dirname and not os.path.exists(dirname):
		raise FileNotFoundError(f"Directory '{dirname}' not found")

	# Read the entire ZIP file into memory
	with open(file_path, 'rb') as f:
		data = f.read()

	# Find central directory entries
	CENTRAL_SIG = b'PK\x01\x02'
	entries: list[dict[str, int | str]] = []
	idx = 0

	while True:
		idx = data.find(CENTRAL_SIG, idx)
		if idx == -1:
			break
		# Ensure enough length for central directory header
		if idx + 46 > len(data):
			break

		header = data[idx:idx+46]
		try:
			(
				sig,
				ver_made, ver_needed, flags, comp_method, mtime, mdate,
				crc, csize, usize,
				name_len, extra_len, comm_len,
				disk_start, int_attr,
				ext_attr, local_off
			) = struct.unpack('<4s6H3L3H2H2L', header)

			name_start = idx + 46
			if name_start + name_len > len(data):
				idx += 4
				continue

			name = data[name_start:name_start+name_len].decode('utf-8', errors='replace')
			entries.append({
				'name': name,
				'comp_method': comp_method,
				'csize': csize,
				'usize': usize,
				'local_offset': local_off,
				'crc': crc
			})
		except (struct.error, UnicodeDecodeError):
			# Skip corrupted entries
			pass

		idx += 4

	# Create a new ZIP file with recovered entries
	with ZipFile(destination, "w", compression=ZIP_DEFLATED) as new_zip_file:
		for entry in entries:
			try:
				# Get the local header to find data start
				lo: int = int(entry['local_offset'])
				if lo + 30 > len(data):
					continue

				lh = data[lo:lo+30]
				try:
					_, _, _, _, _, _, _, _, _, name_len, extra_len = struct.unpack('<4sHHHHHLLLHH', lh)
				except struct.error:
					continue

				data_start: int = lo + 30 + name_len + extra_len
				if data_start + int(entry['csize']) > len(data):
					continue

				comp_data = data[data_start:data_start+int(entry['csize'])]

				# Decompress the data
				try:
					if int(entry['comp_method']) == 0:  # No compression
						content = comp_data[:int(entry['usize'])]
					elif int(entry['comp_method']) == 8:  # Deflate compression
						content = zlib.decompress(comp_data, -zlib.MAX_WBITS)
					else:
						# Unsupported compression method, skip
						continue

					# Write to new ZIP file
					new_zip_file.writestr(str(entry['name']), content)

				except (zlib.error, Exception):
					# If decompression fails, try to write raw data as a fallback
					try:
						new_zip_file.writestr(f"{entry['name']!s}.corrupted", comp_data)
					except Exception:
						# Skip completely corrupted entries
						continue

			except Exception:
				# Skip any entries that cause errors
				continue

	return True


# CLI functionality
if __name__ == "__main__":
	import argparse
	import sys

	parser = argparse.ArgumentParser(description="Archive utilities")
	subparsers = parser.add_subparsers(dest="command", help="Available commands")

	# Repair command
	repair_parser = subparsers.add_parser("repair", help="Repair a corrupted zip file")
	repair_parser.add_argument("input_file", help="Path to the corrupted zip file")
	repair_parser.add_argument("output_file", nargs="?", help="Path to the repaired zip file (optional, defaults to input_file with '_repaired' suffix)")

	# Make archive command
	archive_parser = subparsers.add_parser("make", help="Create a zip archive")
	archive_parser.add_argument("source", help="Source directory to archive")
	archive_parser.add_argument("destination", help="Destination zip file")
	archive_parser.add_argument("--ignore", help="Glob patterns to ignore (comma-separated)")
	archive_parser.add_argument("--create-dir", action="store_true", help="Create destination directory if it doesn't exist")

	args = parser.parse_args()

	if args.command == "repair":
		input_file = args.input_file
		if args.output_file:
			output_file = args.output_file
		else:
			# Generate default output filename
			base, ext = os.path.splitext(input_file)
			output_file = f"{base}_repaired{ext}"

		print(f"Repairing '{input_file}' to '{output_file}'...")
		try:
			repair_zip_file(input_file, output_file)
			print(f"Successfully repaired zip file: {output_file}")
		except Exception as e:
			print(f"Error repairing zip file: {e}", file=sys.stderr)
			sys.exit(1)

	elif args.command == "make":
		print(f"Creating archive from '{args.source}' to '{args.destination}'...")
		try:
			make_archive(
				source=args.source,
				destinations=args.destination,
				create_dir=args.create_dir,
				ignore_patterns=args.ignore
			)
			print(f"Successfully created archive: {args.destination}")
		except Exception as e:
			print(f"Error creating archive: {e}", file=sys.stderr)
			sys.exit(1)

	else:
		parser.print_help()
		sys.exit(1)


