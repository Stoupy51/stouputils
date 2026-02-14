
# Imports
import os

from ..decorators import handle_error, measure_time
from ..io.path import clean_path
from ..print.message import info, warning
from .consolidate import consolidate_backups


# Function to limit the number of delta backups by consolidating the oldest ones
@measure_time(message="Limiting backups")
@handle_error()
def limit_backups(max_backups: int, backup_folder: str, keep_oldest: bool = True) -> None:
	""" Limits the number of delta backups by consolidating the oldest ones.

	If the number of backups exceeds max_backups, the oldest backups are consolidated
	into a single backup file, then deleted, until the count is within the limit.

	Args:
		max_backups (int): Maximum number of delta backups to keep
		backup_folder (str): Path to the folder containing backups
		keep_oldest (bool): If True, never delete the oldest backup (default: True)
	Examples:

	.. code-block:: python

		> limit_backups(5, "/path/to/backups")
		[INFO HH:MM:SS] Limiting backups
		[INFO HH:MM:SS] Consolidated 3 oldest backups into '/path/to/backups/consolidated_YYYY_MM_DD-HH_MM_SS.zip'
		[INFO HH:MM:SS] Deleted 3 old backups
	"""
	backup_folder = clean_path(os.path.abspath(backup_folder))
	if max_backups < 1:
		raise ValueError("max_backups must be at least 1")

	# Get all backup files sorted by date (oldest first), including consolidated ones
	# Sort by timestamp (removing "consolidated_" prefix for proper chronological ordering)
	def get_sort_key(filename: str) -> str:
		basename = os.path.basename(filename)
		return basename.replace("consolidated_", "")

	backup_files: list[str] = sorted([
		clean_path(os.path.join(backup_folder, f))
		for f in os.listdir(backup_folder)
		if f.endswith(".zip")
	], key=get_sort_key)

	backup_count: int = len(backup_files)

	# Check if we need to consolidate
	if backup_count <= max_backups:
		info(f"Current backup count ({backup_count}) is within limit ({max_backups}). No action needed.")
		return

	# Calculate how many backups to consolidate
	num_to_consolidate: int = backup_count - max_backups + 1

	# If keep_oldest is True, exclude the oldest backup from consolidation
	if keep_oldest and backup_count > 1:
		# Start from index 1 instead of 0 to skip the oldest backup
		backups_to_consolidate: list[str] = backup_files[1:num_to_consolidate+1]
	else:
		backups_to_consolidate: list[str] = backup_files[:num_to_consolidate]

	latest_to_consolidate: str = backups_to_consolidate[-1]

	info(f"Found {backup_count} backups, consolidating {num_to_consolidate} oldest backups...")

	# Extract timestamp from the most recent backup being consolidated (last in list)
	latest_backup: str = os.path.basename(backups_to_consolidate[-1])
	latest_timestamp: str = latest_backup.replace("consolidated_", "").replace(".zip", "")

	# Create consolidated backup filename with the most recent consolidated backup's timestamp
	consolidated_filename: str = f"consolidated_{latest_timestamp}.zip"
	consolidated_path: str = clean_path(os.path.join(backup_folder, consolidated_filename))	# Consolidate the oldest backups
	consolidate_backups(latest_to_consolidate, consolidated_path)

	# Delete the old backups that were consolidated
	for backup_path in backups_to_consolidate:
		try:
			os.remove(backup_path)
			info(f"Deleted old backup: {os.path.basename(backup_path)}")
		except Exception as e:
			warning(f"Error deleting backup {backup_path}: {e}")

	info(f"Successfully limited backups to {max_backups}. Consolidated backup: {consolidated_filename}")

