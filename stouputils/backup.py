"""
This module provides utilities for backup management.

- get_file_hash: Computes the SHA-256 hash of a file
- create_delta_backup: Creates a ZIP delta backup, saving only modified or new files while tracking deleted files
- consolidate_backups: Consolidates the files from the given backup and all previous ones into a new ZIP file
- backup_cli: Main entry point for command line usage

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/backup_module.gif
  :alt: stouputils backup examples
"""

# Standard library imports
import datetime
import fnmatch
import hashlib
import os
import zipfile

# Local imports
from .decorators import handle_error, measure_time
from .io import clean_path
from .print import info, progress, warning


# Function to compute the SHA-256 hash of a file
def get_file_hash(file_path: str) -> str | None:
	""" Computes the SHA-256 hash of a file.

	Args:
		file_path (str): Path to the file
	Returns:
		str | None: SHA-256 hash as a hexadecimal string or None if an error occurs
	"""
	try:
		sha256_hash = hashlib.sha256()
		with open(file_path, "rb") as f:
			for chunk in iter(lambda: f.read(4096), b""):
				sha256_hash.update(chunk)
		return sha256_hash.hexdigest()
	except Exception as e:
		warning(f"Error computing hash for file {file_path}: {e}")
		return None

# Function to extract the stored hash from a ZipInfo object's comment
def extract_hash_from_zipinfo(zip_info: zipfile.ZipInfo) -> str | None:
	""" Extracts the stored hash from a ZipInfo object's comment.

	Args:
		zip_info (zipfile.ZipInfo): The ZipInfo object representing a file in the ZIP
	Returns:
		str | None: The stored hash if available, otherwise None
	"""
	comment: bytes | None = zip_info.comment
	comment_str: str | None = comment.decode() if comment else None
	return comment_str if comment_str and len(comment_str) == 64 else None  # Ensure it's a valid SHA-256 hash

# Function to retrieve all previous backups in a folder
@measure_time(message="Retrieving previous backups")
def get_all_previous_backups(backup_folder: str, all_before: str | None = None) -> dict[str, dict[str, str]]:
	""" Retrieves all previous backups in a folder and maps each backup to a dictionary of file paths and their hashes.

	Args:
		backup_folder (str): The folder containing previous backup zip files
		all_before (str | None): Path to the latest backup ZIP file
			(If endswith "/latest.zip" or "/", the latest backup will be used)
	Returns:
		dict[str, dict[str, str]]: Dictionary mapping backup file paths to dictionaries of {file_path: file_hash}
	"""
	backups: dict[str, dict[str, str]] = {}
	list_dir: list[str] = sorted([clean_path(os.path.join(backup_folder, f)) for f in os.listdir(backup_folder)])

	# If all_before is provided, don't include backups after it
	if isinstance(all_before, str) and not (
		all_before.endswith("/latest.zip") or all_before.endswith("/") or os.path.isdir(all_before)
	):
		list_dir = list_dir[:list_dir.index(all_before) + 1]

	# Get all the backups
	for filename in list_dir:
		if filename.endswith(".zip"):
			zip_path: str = clean_path(os.path.join(backup_folder, filename))
			file_hashes: dict[str, str] = {}

			try:
				with zipfile.ZipFile(zip_path, "r") as zipf:
					for inf in zipf.infolist():
						if inf.filename != "__deleted_files__.txt":
							stored_hash: str | None = extract_hash_from_zipinfo(inf)
							if stored_hash is not None:  # Only store if hash exists
								file_hashes[inf.filename] = stored_hash

					backups[zip_path] = file_hashes
			except Exception as e:
				warning(f"Error reading backup {zip_path}: {e}")

	return dict(reversed(backups.items()))

# Function to check if a file exists in any previous backup
def is_file_in_any_previous_backup(file_path: str, file_hash: str, previous_backups: dict[str, dict[str, str]]) -> bool:
	""" Checks if a file with the same hash exists in any previous backup.

	Args:
		file_path (str): The relative path of the file
		file_hash (str): The SHA-256 hash of the file
		previous_backups (dict[str, dict[str, str]]): Dictionary mapping backup zip paths to their stored file hashes
	Returns:
		bool: True if the file exists unchanged in any previous backup, False otherwise
	"""
	for file_hashes in previous_backups.values():
		if file_hashes.get(file_path) == file_hash:
			return True
	return False


# Main backup function that creates a delta backup (only changed files)
@measure_time(message="Creating ZIP backup")
@handle_error()
def create_delta_backup(source_path: str, destination_folder: str, exclude_patterns: list[str] | None = None) -> None:
	""" Creates a ZIP delta backup, saving only modified or new files while tracking deleted files.

	Args:
		source_path (str): Path to the source file or directory to back up
		destination_folder (str): Path to the folder where the backup will be saved
		exclude_patterns (list[str] | None): List of glob patterns to exclude from backup
	Examples:

	.. code-block:: python

		> create_delta_backup("/path/to/source", "/path/to/backups", exclude_patterns=["libraries/*", "cache/*"])
		[INFO HH:MM:SS] Creating ZIP backup
		[INFO HH:MM:SS] Backup created: '/path/to/backups/backup_2025_02_18-10_00_00.zip'
	"""
	source_path = clean_path(os.path.abspath(source_path))
	destination_folder = clean_path(os.path.abspath(destination_folder))

	# Setup backup paths and create destination folder
	base_name: str = os.path.basename(source_path.rstrip(os.sep)) or "backup"
	backup_folder: str = clean_path(os.path.join(destination_folder, base_name))
	os.makedirs(backup_folder, exist_ok=True)

	# Get previous backups and track all files
	previous_backups: dict[str, dict[str, str]] = get_all_previous_backups(backup_folder)
	previous_files: set[str] = {file for backup in previous_backups.values() for file in backup}  # Collect all tracked files

	# Create new backup filename with timestamp
	timestamp: str = datetime.datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
	zip_filename: str = f"{timestamp}.zip"
	destination_zip: str = clean_path(os.path.join(backup_folder, zip_filename))

	# Create the ZIP file early to write files as we process them
	with zipfile.ZipFile(destination_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
		deleted_files: set[str] = set()
		has_changes: bool = False

		# Process files one by one to avoid memory issues
		if os.path.isdir(source_path):
			for root, _, files in os.walk(source_path):
				for file in files:
					full_path: str = clean_path(os.path.join(root, file))
					arcname: str = clean_path(os.path.relpath(full_path, start=os.path.dirname(source_path)))

					# Skip file if it matches any exclude pattern
					if exclude_patterns and any(fnmatch.fnmatch(arcname, pattern) for pattern in exclude_patterns):
						continue

					file_hash: str | None = get_file_hash(full_path)
					if file_hash is None:
						continue

					# Check if file needs to be backed up
					if not is_file_in_any_previous_backup(arcname, file_hash, previous_backups):
						try:
							zip_info: zipfile.ZipInfo = zipfile.ZipInfo(arcname)
							zip_info.compress_type = zipfile.ZIP_DEFLATED
							zip_info.comment = file_hash.encode()  # Store hash in comment

							# Read and write file in chunks
							with open(full_path, "rb") as f:
								with zipf.open(zip_info, "w", force_zip64=True) as zf:
									for chunk in iter(lambda: f.read(4096), b""):
										zf.write(chunk)
							has_changes = True
						except Exception as e:
							warning(f"Error writing file {full_path} to backup: {e}")

					# Track current files for deletion detection
					if arcname in previous_files:
						previous_files.remove(arcname)
		else:
			arcname: str = clean_path(os.path.basename(source_path))
			file_hash: str | None = get_file_hash(source_path)

			if file_hash is not None and not is_file_in_any_previous_backup(arcname, file_hash, previous_backups):
				try:
					zip_info: zipfile.ZipInfo = zipfile.ZipInfo(arcname)
					zip_info.compress_type = zipfile.ZIP_DEFLATED
					zip_info.comment = file_hash.encode()

					with open(source_path, "rb") as f:
						with zipf.open(zip_info, "w", force_zip64=True) as zf:
							for chunk in iter(lambda: f.read(4096), b""):
								zf.write(chunk)
					has_changes = True
				except Exception as e:
					warning(f"Error writing file {source_path} to backup: {e}")

		# Any remaining files in previous_files were deleted
		deleted_files = previous_files
		if deleted_files:
			zipf.writestr("__deleted_files__.txt", "\n".join(deleted_files), compress_type=zipfile.ZIP_DEFLATED)
			has_changes = True

	# Remove empty backup if no changes
	if not has_changes:
		os.remove(destination_zip)
		info(f"No files to backup, skipping creation of backup '{destination_zip}'")
	else:
		info(f"Backup created: '{destination_zip}'")


# Function to consolidate multiple backups into one comprehensive backup
@measure_time(message="Consolidating backups")
def consolidate_backups(zip_path: str, destination_zip: str) -> None:
	""" Consolidates the files from the given backup and all previous ones into a new ZIP file,
	ensuring that the most recent version of each file is kept and deleted files are not restored.

	Args:
		zip_path (str): Path to the latest backup ZIP file (If endswith "/latest.zip" or "/", the latest backup will be used)
		destination_zip (str): Path to the destination ZIP file where the consolidated backup will be saved
	Examples:

	.. code-block:: python

		> consolidate_backups("/path/to/backups/latest.zip", "/path/to/consolidated.zip")
		[INFO HH:MM:SS] Consolidating backups
		[INFO HH:MM:SS] Consolidated backup created: '/path/to/consolidated.zip'
	"""
	zip_path = clean_path(os.path.abspath(zip_path))
	destination_zip = clean_path(os.path.abspath(destination_zip))
	zip_folder: str = clean_path(os.path.dirname(zip_path))

	# Get all previous backups up to the specified one
	previous_backups: dict[str, dict[str, str]] = get_all_previous_backups(zip_folder, all_before=zip_path)

	deleted_files: set[str] = set()
	final_files: set[str] = set()

	# Create destination ZIP file
	with zipfile.ZipFile(destination_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipf_out:
		# Process each backup, tracking deleted files and consolidating files
		for backup_path in previous_backups:
			with zipfile.ZipFile(backup_path, "r") as zipf_in:
				# Process deleted files
				if "__deleted_files__.txt" in zipf_in.namelist():
					backup_deleted_files: list[str] = zipf_in.read("__deleted_files__.txt").decode().splitlines()
					deleted_files.update(backup_deleted_files)

				# Process files
				for inf in zipf_in.infolist():
					filename: str = inf.filename
					if filename \
						and filename != "__deleted_files__.txt" \
						and filename not in final_files \
						and filename not in deleted_files:
						final_files.add(filename)

						# Copy file in chunks
						with zipf_in.open(inf, "r") as source:
							with zipf_out.open(inf, "w", force_zip64=True) as target:
								for chunk in iter(lambda: source.read(4096), b""):
									target.write(chunk)

	info(f"Consolidated backup created: {destination_zip}")

# Main entry point for command line usage
@measure_time(progress)
def backup_cli():
	""" Main entry point for command line usage.

	Examples:

	.. code-block:: bash

		# Create a delta backup, excluding libraries and cache folders
		python -m stouputils.backup delta /path/to/source /path/to/backups -x "libraries/*" "cache/*"

		# Consolidate backups into a single file
		python -m stouputils.backup consolidate /path/to/backups/latest.zip /path/to/consolidated.zip
	"""
	import argparse

	# Setup command line argument parser
	parser: argparse.ArgumentParser = argparse.ArgumentParser(
		description="Backup and consolidate files using delta compression."
	)
	subparsers = parser.add_subparsers(dest="command", required=True)

	# Create delta command and its arguments
	delta_psr = subparsers.add_parser("delta", help="Create a new delta backup")
	delta_psr.add_argument("source", type=str, help="Path to the source directory or file")
	delta_psr.add_argument("destination", type=str, help="Path to the destination folder for backups")
	delta_psr.add_argument("-x", "--exclude", type=str, nargs="+", help="Glob patterns to exclude from backup", default=[])

	# Create consolidate command and its arguments
	consolidate_psr = subparsers.add_parser("consolidate", help="Consolidate existing backups into one")
	consolidate_psr.add_argument("backup_zip", type=str, help="Path to the latest backup ZIP file")
	consolidate_psr.add_argument("destination_zip", type=str, help="Path to the destination consolidated ZIP file")

	# Parse arguments and execute appropriate command
	args: argparse.Namespace = parser.parse_args()

	if args.command == "delta":
		create_delta_backup(args.source, args.destination, args.exclude)
	elif args.command == "consolidate":
		consolidate_backups(args.backup_zip, args.destination_zip)

if __name__ == "__main__":
	backup_cli()

