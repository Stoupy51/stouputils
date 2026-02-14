
# Imports
import os
import shutil
import zipfile

from ..config import StouputilsConfig as Cfg
from ..decorators import measure_time
from ..io.path import clean_path
from ..print.message import info, warning
from ..print.progress_bar import colored_for_loop
from .retrieve import get_all_previous_backups


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
	backup_paths: list[str] = list(previous_backups.keys())

	# First pass: collect all deleted files and build file registry
	deleted_files: set[str] = set()
	file_registry: dict[str, tuple[str, zipfile.ZipInfo]] = {}  # filename -> (backup_path, zipinfo)

	# Process backups in reverse order (newest first) to prioritize latest versions
	for backup_path in reversed(backup_paths):
		try:
			with zipfile.ZipFile(backup_path, "r") as zipf_in:

				# Get namelist once for efficiency
				namelist: list[str] = zipf_in.namelist()

				# Process deleted files
				if "__deleted_files__.txt" in namelist:
					backup_deleted_files: list[str] = zipf_in.read("__deleted_files__.txt").decode().splitlines()
					deleted_files.update(backup_deleted_files)

				# Process files - only add if not already in registry (newer versions take precedence)
				for inf in zipf_in.infolist():
					filename: str = inf.filename
					if (filename
						and filename != "__deleted_files__.txt"
						and filename not in deleted_files
						and filename not in file_registry):
						file_registry[filename] = (backup_path, inf)
		except Exception as e:
			warning(f"Error processing backup {backup_path}: {e}")
			continue

	# Second pass: copy files efficiently, keeping ZIP files open longer
	open_zips: dict[str, zipfile.ZipFile] = {}

	try:
		with zipfile.ZipFile(destination_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipf_out:
			for filename, (backup_path, inf) in colored_for_loop(file_registry.items(), desc="Making consolidated backup"):
				try:
					# Open ZIP file if not already open
					if backup_path not in open_zips:
						open_zips[backup_path] = zipfile.ZipFile(backup_path, "r")

					zipf_in = open_zips[backup_path]

					# Copy file with optimized strategy based on file size
					with zipf_in.open(inf, "r") as source:
						with zipf_out.open(inf, "w", force_zip64=True) as target:
							# Use shutil.copyfileobj with larger chunks for files >50MB
							if inf.file_size > 52428800:  # 50MB threshold
								shutil.copyfileobj(source, target, length=Cfg.LARGE_CHUNK_SIZE)
							else:
								# Use shutil.copyfileobj with standard chunks for smaller files
								shutil.copyfileobj(source, target, length=Cfg.CHUNK_SIZE)
				except Exception as e:
					warning(f"Error copying file {filename} from {backup_path}: {e}")
					continue

			# Add accumulated deleted files to the consolidated backup
			if deleted_files:
				zipf_out.writestr("__deleted_files__.txt", "\n".join(sorted(deleted_files)), compress_type=zipfile.ZIP_DEFLATED)
	finally:
		# Clean up open ZIP files
		for zipf in open_zips.values():
			try:
				zipf.close()
			except Exception:
				pass

	info(f"Consolidated backup created: {destination_zip}")

