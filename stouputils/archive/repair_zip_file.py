
# Imports
import os
from zipfile import ZIP_DEFLATED, ZipFile

from ..decorators.handle_error import handle_error


# Function that repair a corrupted zip file (ignoring some of the errors)
@handle_error
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
	# Check
	if not os.path.exists(file_path):
		raise FileNotFoundError(f"File '{file_path}' not found")
	dirname: str = os.path.dirname(destination)
	if dirname and not os.path.exists(dirname):
		raise FileNotFoundError(f"Directory '{dirname}' not found")

	import struct
	import zlib

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
				_sig,
				_ver_made, _ver_needed, _flags, comp_method, _mtime, _mdate,
				crc, csize, usize,
				name_len, extra_len, _comm_len,
				_disk_start, _int_attr,
				_ext_attr, local_off
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

