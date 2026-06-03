
# Imports
import os
import zipfile

from ..decorators import measure_time
from ..io.path import clean_path
from ..print.message import warning
from .hash import extract_hash_from_zipinfo


# Function to sort backup files chronologically, including consolidated backups
def get_backup_sort_key(filename: str) -> str:
	""" Returns a sortable key for backup filenames.

	Args:
		filename (str): Backup filename or path
	Returns:
		str: Filename normalized for chronological sorting
	"""
	basename: str = os.path.basename(filename)
	return basename.removeprefix("consolidated_")


# Function to retrieve all previous backups in a folder
@measure_time(message="Retrieving previous backups")
def get_all_previous_backups(backup_folder: str, all_before: str | None = None) -> dict[str, dict[str, str]]:
	""" Retrieves all previous backups in a folder and maps each backup to a dictionary of file paths and their hashes.

	Args:
		backup_folder (str): The folder containing previous backup zip files
		all_before (str | None): Path to the latest backup ZIP file
			(If endswith "/latest.zip" or "/", the latest backup will be used)
	Returns:
		dict[str, dict[str, str]]: Dictionary mapping backup file paths to dictionaries of {file_path: file_hash}, ordered from newest to oldest
	"""
	backups: dict[str, dict[str, str]] = {}
	backup_folder = clean_path(os.path.abspath(backup_folder))
	list_dir: list[str] = sorted(
		[
			clean_path(os.path.join(backup_folder, f))
			for f in os.listdir(backup_folder)
			if f.endswith(".zip")
		],
		key=get_backup_sort_key,
	)

	# If all_before is provided, don't include backups after it
	if isinstance(all_before, str) and not (
		all_before.endswith("/latest.zip") or all_before.endswith("/") or os.path.isdir(all_before)
	):
		all_before = clean_path(os.path.abspath(all_before))
		list_dir = list_dir[:list_dir.index(all_before) + 1]

	# Get all the backups, resolving each file path to its newest known state
	resolved_files: set[str] = set()
	for zip_path in reversed(list_dir):
		file_hashes: dict[str, str] = {}

		try:
			with zipfile.ZipFile(zip_path, "r") as zipf:
				for inf in zipf.infolist():
					if inf.filename != "__deleted_files__.txt" and inf.filename not in resolved_files:
						stored_hash: str | None = extract_hash_from_zipinfo(inf)
						if stored_hash is not None:  # Only store if hash exists
							file_hashes[inf.filename] = stored_hash
							resolved_files.add(inf.filename)

				if "__deleted_files__.txt" in zipf.namelist():
					deleted_files: list[str] = zipf.read("__deleted_files__.txt").decode().splitlines()
					resolved_files.update(deleted_files)

				backups[zip_path] = file_hashes
		except Exception as e:
			warning(f"Error reading backup {zip_path}: {e}")

	return backups

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

