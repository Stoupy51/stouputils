
# Imports
from .io import *
from .print import *
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

# Function that makes an archive with consistency (same zip file each time)
@handle_error(ValueError, message="destinations must be a list of at least one destination")
def make_archive(
	source: str,
	destinations: list[str]|str = [],
	override_time: None | tuple[int, int, int, int, int, int] = None
) -> bool:
	""" Make an archive with consistency using FILES_TO_WRITE variable\n
	Args:
		source				(str):						The source folder to archive
		destinations		(list[str]|str):			The destination folder(s) or file(s) to copy the archive to
		override_time		(None | tuple[int, ...]):	The constant time to use for the archive (e.g. (2024, 1, 1, 0, 0, 0) for 2024-01-01 00:00:00)
	"""
	# Fix copy_destinations type if needed
	if destinations and isinstance(destinations, str):
		destinations = [destinations]
	if not destinations:
		raise ValueError("destinations must be a list of at least one destination")

	# Get all files that are not in FILES_TO_WRITE
	not_known_files: list[str] = []
	for root, _, files in os.walk(source):
		for file in files:
			file_path: str = clean_path(os.path.join(root, file))
			if file_path not in FILES_TO_WRITE:
				not_known_files.append(file_path)

	# Create the archive
	destination: str = destinations[0]
	destination = destination if ".zip" in destination else destination + ".zip"
	with ZipFile(destination, "w", compression=ZIP_DEFLATED, compresslevel=9) as zip:

		# Write every not-known file with the fixed date/time
		for file in not_known_files:
			if source not in file:
				continue
			base_path: str = file.replace(source, "").strip("/")
			info = ZipInfo(base_path)
			info.compress_type = ZIP_DEFLATED
			if override_time:
				info.date_time = override_time
			with open(file, "rb") as f:
				zip.writestr(info, f.read())
		
		# Write every known file with the fixed date/time
		for file in FILES_TO_WRITE:
			if source not in file:
				continue
			base_path: str = file.replace(source, "").strip("/")
			info: ZipInfo = ZipInfo(base_path)
			info.compress_type = ZIP_DEFLATED
			if override_time:
				info.date_time = override_time
			zip.writestr(info, FILES_TO_WRITE[file])

	# Copy the archive to the destination(s)
	for dest_folder in destinations:
		try:
			dest_folder = clean_path(dest_folder)
			if dest_folder.endswith("/"):
				file_name = destination.split("/")[-1]
				shutil.copy(clean_path(destination), f"{dest_folder}/{file_name}")
			else:	# Else, it's not a folder but a file path
				shutil.copy(clean_path(destination), dest_folder)
		except Exception as e:
			warning(f"Unable to copy '{clean_path(destination)}' to '{dest_folder}', reason: {e}")

	return True

