"""
This module provides functions for creating and managing archives.
- make_archive: Make an archive with consistency using FILES_TO_WRITE variable
- repair_zip_file: Try to repair a corrupted zip file (NOT IMPLEMENTED)
"""

# Imports
from .io import *
from .print import *
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

# Function that makes an archive with consistency (same zip file each time)
@handle_error()
def make_archive(
	source: str,
	destinations: list[str]|str = [],
	override_time: None | tuple[int, int, int, int, int, int] = None,
	create_dir: bool = False
) -> bool:
	""" Make an archive with consistency using FILES_TO_WRITE variable

	Args:
		source				(str):						The source folder to archive
		destinations		(list[str]|str):			The destination folder(s) or file(s) to copy the archive to
		override_time		(None | tuple[int, ...]):	The constant time to use for the archive (e.g. (2024, 1, 1, 0, 0, 0) for 2024-01-01 00:00:00)
		create_dir			(bool):						Whether to create the destination directory if it doesn't exist (default: False)
	Returns:
		bool: Always returns True unless any strong error
	"""
	# Fix copy_destinations type if needed
	if destinations and isinstance(destinations, str):
		destinations = [destinations]
	if not destinations:
		raise ValueError("destinations must be a list of at least one destination")

	# Create the archive
	destination: str = clean_path(destinations[0])
	destination = destination if ".zip" in destination else destination + ".zip"
	with ZipFile(destination, "w", compression=ZIP_DEFLATED, compresslevel=9) as zip:
		for root, _, files in os.walk(source):
			for file in files:
				file_path: str = clean_path(os.path.join(root, file))
				info: ZipInfo = ZipInfo(file_path)
				info.compress_type = ZIP_DEFLATED
				if override_time:
					info.date_time = override_time
				with open(file_path, "rb") as f:
					zip.writestr(info, f.read())

	# Copy the archive to the destination(s)
	for dest_folder in destinations:
		@handle_error(Exception, message=f"Unable to copy '{destination}' to '{dest_folder}'", error_log=LogLevels.WARNING)
		def internal(src: str, dest: str) -> None:
			super_copy(src, dest, create_dir=create_dir)
		internal(destination, clean_path(dest_folder))

	return True



# Function that repair a corrupted zip file (ignoring some of the errors)
from .dont_look.zip_file_override import ZipFileOverride
@handle_error()
def repair_zip_file(file_path: str, destination: str) -> bool:
	""" Try to repair a corrupted zip file by ignoring some of the errors

	Args:
		file_path		(str):	Path of the zip file to repair
		destination		(str):	Destination of the new file
	Returns:
		bool: Always returns True unless any strong error
	"""
	# Check
	if not os.path.exists(file_path):
		raise FileNotFoundError(f"File '{file_path}' not found")
	dirname: str = os.path.dirname(destination)
	if dirname and not os.path.exists(dirname):
		raise FileNotFoundError(f"Directory '{dirname}' not found")

	# Read it
	with ZipFileOverride(file_path, "r") as zip_file:

		# Get a list of all the files in the ZIP file
		file_list: list[str] = zip_file.namelist()

		# Create a new ZIP file at the destination
		with ZipFileOverride(destination, "w", compression=ZIP_DEFLATED) as new_zip_file:
			for file_name in file_list:
				try:
					new_zip_file.writestr(file_name, zip_file.read(file_name))
				except KeyboardInterrupt:
					continue
	
	return True


