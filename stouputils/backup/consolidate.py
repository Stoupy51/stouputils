
# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import os
import shutil
import zipfile
from contextlib import suppress

from ..config import StouputilsConfig as Cfg
from ..decorators import measure_time
from ..io.path import clean_path
from ..print.message import info, warning
from ..print.progress_tqdm import progress_bar
from .retrieve import get_all_previous_backups


# Function to consolidate multiple backups into one comprehensive backup
@measure_time(message="Consolidating backups")
def consolidate_backups(zip_path: str, destination_zip: str) -> None:
	""" Consolidates the files from the given backup and all previous ones into a new ZIP file,
	ensuring that the most recent version of each file is kept and deleted files are not restored.

	Args:
		zip_path:        Path to the latest backup ZIP file (If endswith "/latest.zip" or "/", the latest backup will be used)
		destination_zip: Path to the destination ZIP file where the consolidated backup will be saved

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

	# First pass: the newest version of every file, and the files deleted along the way
	file_registry, deleted_files = build_file_registry(backup_paths)

	# Second pass: copy files efficiently, keeping ZIP files open longer
	open_zips: dict[str, zipfile.ZipFile] = {}

	try:
		with zipfile.ZipFile(destination_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipf_out:
			for filename, (backup_path, inf) in progress_bar(file_registry.items(), desc="Making consolidated backup"):
				try:
					# Open ZIP file if not already open
					if backup_path not in open_zips:
						open_zips[backup_path] = zipfile.ZipFile(backup_path, "r")

					zipf_in = open_zips[backup_path]

					# Files above 50 MB are copied in larger chunks
					chunk_size: int = Cfg.LARGE_CHUNK_SIZE if inf.file_size > 52428800 else Cfg.CHUNK_SIZE
					with zipf_in.open(inf, "r") as source, zipf_out.open(inf, "w", force_zip64=True) as target:
						shutil.copyfileobj(source, target, length=chunk_size)
				except Exception as e:
					warning(f"Error copying file {filename} from {backup_path}: {e}")
					continue

			# Add only unresolved deleted files to the consolidated backup
			active_deleted_files: set[str] = deleted_files - set(file_registry)
			if active_deleted_files:
				zipf_out.writestr("__deleted_files__.txt", "\n".join(sorted(active_deleted_files)), compress_type=zipfile.ZIP_DEFLATED)
	finally:
		# Clean up open ZIP files
		for zipf in open_zips.values():
			with suppress(Exception):
				zipf.close()

	info(f"Consolidated backup created: {destination_zip}")


def build_file_registry(backup_paths: list[str]) -> tuple[dict[str, tuple[str, zipfile.ZipInfo]], set[str]]:
	""" The newest stored version of every file across backups, and the files some backup marked as deleted.

	A file a backup deletes is no longer taken from older backups, while one stored in that same backup still counts.

	Args:
		backup_paths: Backup ZIP files, newest first.
	Returns:
		Each file name mapped to the backup holding it and its entry there, in the order the backups store them.
	"""
	deleted_files: set[str] = set()
	file_registry: dict[str, tuple[str, zipfile.ZipInfo]] = {}
	for backup_path in backup_paths:
		try:
			with zipfile.ZipFile(backup_path, "r") as zipf_in:
				for inf in zipf_in.infolist():
					filename: str = inf.filename
					is_new: bool = filename not in deleted_files and filename not in file_registry
					if filename and filename != "__deleted_files__.txt" and is_new:
						file_registry[filename] = (backup_path, inf)
				if "__deleted_files__.txt" in zipf_in.namelist():
					deleted_files.update(zipf_in.read("__deleted_files__.txt").decode().splitlines())
		except Exception as e:
			warning(f"Error processing backup {backup_path}: {e}")
	return file_registry, deleted_files

