"""
This module provides utilities for backup management.
- get_file_hash: Computes the SHA-256 hash of a file
- create_delta_backup: Creates a ZIP delta backup, saving only modified or new files while tracking deleted files
- consolidate_backups: Consolidates the files from the given backup and all previous ones into a new ZIP file
- backup_cli: Main entry point for command line usage
"""

# Standard library imports
import os
import hashlib
import zipfile
import datetime
import fnmatch

# Local imports
from .parallel import multithreading
from .decorators import measure_time, handle_error
from .print import info, warning, progress
from .io import clean_path

# Function to compute the SHA-256 hash of a file
def get_file_hash(file_path: str) -> str | None:
	""" Computes the SHA-256 hash of a file.

	Args:
		file_path (str): Path to the file
	Returns:
		str | None: SHA-256 hash as a hexadecimal string or None if an error occurs
	"""
	try:
		with open(file_path, "rb") as f:
			return hashlib.sha256(f.read()).hexdigest()
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
		all_before (str | None): Path to the latest backup ZIP file (If endswith "/latest.zip" or "/", the latest backup will be used)
	Returns:
		dict[str, dict[str, str]]: Dictionary mapping backup file paths to dictionaries of {file_path: file_hash}
	"""
	backups: dict[str, dict[str, str]] = {}
	list_dir: list[str] = sorted([clean_path(os.path.join(backup_folder, f)) for f in os.listdir(backup_folder)])

	# If all_before is provided, don't include backups after it
	if isinstance(all_before, str) and not (all_before.endswith("/latest.zip") or all_before.endswith("/") or os.path.isdir(all_before)):
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

	files_to_process: list[tuple[str, str, dict[str, dict[str, str]]]] = []

	# Collect files to process - either from directory or single file
	if os.path.isdir(source_path):
		for root, _, files in os.walk(source_path):
			for file in files:
				full_path: str = clean_path(os.path.join(root, file))
				arcname: str = clean_path(os.path.relpath(full_path, start=os.path.dirname(source_path)))
				
				# Skip file if it matches any exclude pattern
				if exclude_patterns:
					should_exclude: bool = any(fnmatch.fnmatch(arcname, pattern) for pattern in exclude_patterns)
					if should_exclude:
						continue
				
				files_to_process.append((full_path, arcname, previous_backups))
	else:
		arcname: str = clean_path(os.path.basename(source_path))
		files_to_process.append((source_path, arcname, previous_backups))

	# Function to process a single file for backup
	def _process_file(full_path: str, arcname: str, previous_backups: dict[str, dict[str, str]]) -> tuple[str, str, bool, str | None]:
		""" Processes a file by computing its hash and checking if it exists in previous backups.

		Args:
			full_path (str): The absolute path of the file
			arcname (str): The relative path of the file inside the backup
			previous_backups (dict[str, dict[str, str]]): Dictionary mapping backup zip paths to their stored file hashes
		Returns:
			str:     full_path
			str:     arcname
			bool:    should_backup
			str:     file_hash
		"""
		file_hash: str | None = get_file_hash(full_path)
		if file_hash is None:
			return full_path, arcname, False, None
		should_backup: bool = not is_file_in_any_previous_backup(arcname, file_hash, previous_backups)
		return full_path, arcname, should_backup, file_hash

	# Process files in parallel to compute hashes and check backups
	processed_files: list[tuple[str, str, bool, str]] = [
		x
		for x in multithreading(_process_file, files_to_process, use_starmap=True, desc="Processing files", verbose_depth=1)
		if x[3] is not None
	]
	current_files: set[str] = set(arcname for _, arcname, _, _ in processed_files)
	deleted_files: set[str] = previous_files - current_files

	# Only create backup if there are changes (new, modified, or deleted files)
	if deleted_files or any(should_backup for _, _, should_backup, _ in processed_files):
		with zipfile.ZipFile(destination_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
			for full_path, arcname, should_backup, file_hash in processed_files:
				if should_backup:
					try:
						zip_info: zipfile.ZipInfo = zipfile.ZipInfo(arcname)
						zip_info.compress_type = zipfile.ZIP_DEFLATED
						zip_info.comment = file_hash.encode()  # Store hash in comment
						with open(full_path, "rb") as f:
							zipf.writestr(zip_info, f.read(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
					except Exception as e:
						warning(f"Error writing file {full_path} to backup: {e}")

			# Track deleted files in special file
			if deleted_files:
				zipf.writestr("__deleted_files__.txt", "\n".join(deleted_files), compress_type=zipfile.ZIP_DEFLATED)
		info(f"Backup created: '{destination_zip}'")
	else:
		info(f"No files to backup, skipping creation of backup '{destination_zip}'")


# Function to consolidate multiple backups into one comprehensive backup
@measure_time(message="Consolidating backups")
def consolidate_backups(zip_path: str, destination_zip: str) -> None:
	""" Consolidates the files from the given backup and all previous ones into a new ZIP file,
	ensuring that the most recent version of each file is kept and deleted files are not restored.

	Args:
		zip_path (str): Path to the latest backup ZIP file (If endswith "/latest.zip" or "/", the latest backup will be used)
		destination_zip (str): Path to the destination ZIP file where the consolidated backup will be saved
	"""
	zip_path = clean_path(os.path.abspath(zip_path))
	destination_zip = clean_path(os.path.abspath(destination_zip))
	zip_folder: str = clean_path(os.path.dirname(zip_path))

	# Get all previous backups up to the specified one
	previous_backups: dict[str, dict[str, str]] = get_all_previous_backups(zip_folder, all_before=zip_path)

	deleted_files: set[str] = set()
	final_files: set[str] = set()
	files_to_process: list[tuple[str, str]] = []

	# Process each backup, tracking deleted files and collecting files to consolidate
	for backup_path in previous_backups:
		with zipfile.ZipFile(backup_path, "r") as zipf_in:
			# If the backup contains a __deleted_files__.txt file, add the deleted files to the set
			if "__deleted_files__.txt" in zipf_in.namelist():
				backup_deleted_files: list[str] = zipf_in.read("__deleted_files__.txt").decode().splitlines()
				deleted_files.update(backup_deleted_files)

			# Process the files in the backup
			for inf in zipf_in.infolist():
				filename: str = inf.filename
				if filename \
					and filename != "__deleted_files__.txt" \
					and filename not in final_files \
					and filename not in deleted_files:
					final_files.add(filename)
					files_to_process.append((filename, backup_path))

	# Helper function to read file content from backup
	def _process_consolidation_file(filename: str, backup_path: str) -> tuple[str, bytes]:
		with zipfile.ZipFile(backup_path, "r") as zipf_in:
			file_content: bytes = zipf_in.read(filename)
		return filename, file_content

	# Process files in parallel and write consolidated backup
	processed_files: list[tuple[str, bytes]] = multithreading(_process_consolidation_file, files_to_process, use_starmap=True, desc="Processing files", verbose_depth=1)

	with zipfile.ZipFile(destination_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipf_out:
		for filename, file_content in processed_files:
			zipf_out.writestr(filename, file_content, compress_type=zipfile.ZIP_DEFLATED)

	info(f"Consolidated backup created: {destination_zip}")

# Main entry point for command line usage
@measure_time(progress)
def backup_cli():
	""" Main entry point for command line usage.

	Example:
		# Create a delta backup, excluding libraries and cache folders
		python -m stouputils.backup delta /path/to/source /path/to/backups -x "libraries/*" "cache/*"

		# Consolidate backups into a single file
		python -m stouputils.backup consolidate /path/to/backups/latest.zip /path/to/consolidated.zip
	"""
	import argparse

	# Setup command line argument parser
	parser: argparse.ArgumentParser = argparse.ArgumentParser(description="Backup and consolidate files using delta compression.")
	subparsers = parser.add_subparsers(dest="command", required=True)

	# Create delta command and its arguments
	delta_parser = subparsers.add_parser("delta", help="Create a new delta backup")
	delta_parser.add_argument("source", type=str, help="Path to the source directory or file")
	delta_parser.add_argument("destination", type=str, help="Path to the destination folder for backups")
	delta_parser.add_argument("-x", "--exclude", type=str, nargs="+", help="Glob patterns to exclude from backup", default=[])

	# Create consolidate command and its arguments
	consolidate_parser = subparsers.add_parser("consolidate", help="Consolidate existing backups into one")
	consolidate_parser.add_argument("backup_zip", type=str, help="Path to the latest backup ZIP file")
	consolidate_parser.add_argument("destination_zip", type=str, help="Path to the destination consolidated ZIP file")

	# Parse arguments and execute appropriate command
	args: argparse.Namespace = parser.parse_args()

	if args.command == "delta":
		create_delta_backup(args.source, args.destination, args.exclude)
	elif args.command == "consolidate":
		consolidate_backups(args.backup_zip, args.destination_zip)

if __name__ == "__main__":
	backup_cli()

