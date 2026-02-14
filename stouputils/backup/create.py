
# Imports
import datetime
import fnmatch
import os
import zipfile

from ..config import StouputilsConfig as Cfg
from ..decorators import handle_error, measure_time
from ..io.path import clean_path
from ..print.message import info, warning
from .hash import get_file_hash
from .retrieve import get_all_previous_backups, is_file_in_any_previous_backup


# Main backup function that creates a delta backup (only changed files)
@measure_time(message="Creating ZIP backup")
@handle_error
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

							# Read and write file in chunks with larger buffer
							with open(full_path, "rb") as f:
								with zipf.open(zip_info, "w", force_zip64=True) as zf:
									while True:
										chunk = f.read(Cfg.CHUNK_SIZE)
										if not chunk:
											break
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
							while True:
								chunk = f.read(Cfg.CHUNK_SIZE)
								if not chunk:
									break
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

