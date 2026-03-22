
# Imports
import os
import struct
import zlib
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

	# Read the entire ZIP file into memory
	with open(file_path, "rb") as f:
		data = f.read()

	LOCAL_SIG = b"PK\x03\x04"
	CENTRAL_SIG = b"PK\x01\x02"
	EOCD_SIG = b"PK\x05\x06"

	def _decode_name(raw_name: bytes, flags: int) -> str:
		if flags & 0x0800:
			return raw_name.decode("utf-8", errors="replace")
		return raw_name.decode("cp437", errors="replace")

	def _sanitize_name(name: str, fallback_index: int) -> str:
		sanitized = name.replace("\\", "/").lstrip("/")

		# A metadata file should not be a directory; this helps common pack corruption cases.
		if sanitized.lower() in {"pack.mcmeta", "pack.mcmeta/"}:
			return "pack.mcmeta"

		if sanitized.endswith("/") and "." in sanitized.rsplit("/", 1)[-1]:
			sanitized = sanitized.rstrip("/")

		if not sanitized:
			sanitized = f"recovered_{fallback_index}"

		return sanitized

	def _next_zip_signature(start: int) -> int:
		next_positions = [
			data.find(LOCAL_SIG, start),
			data.find(CENTRAL_SIG, start),
			data.find(EOCD_SIG, start),
		]
		valid_positions = [p for p in next_positions if p != -1]
		if not valid_positions:
			return len(data)
		return min(valid_positions)

	def _find_local_header_near(offset_hint: int) -> int:
		if 0 <= offset_hint <= len(data) - 4 and data[offset_hint:offset_hint + 4] == LOCAL_SIG:
			return offset_hint
		if 0 <= offset_hint + 4 <= len(data) - 4 and data[offset_hint + 4:offset_hint + 8] == LOCAL_SIG:
			return offset_hint + 4

		start = max(0, offset_hint - 32)
		end = min(len(data), offset_hint + 8192)
		best = -1
		best_dist = 10**12
		search_at = start
		while True:
			pos = data.find(LOCAL_SIG, search_at, end)
			if pos == -1:
				break
			dist = abs(pos - offset_hint)
			if dist < best_dist:
				best_dist = dist
				best = pos
			search_at = pos + 1

		return best

	def _read_local_header(offset: int) -> tuple[int, int, int, str, int] | None:
		if offset < 0 or offset + 30 > len(data):
			return None
		if data[offset:offset + 4] != LOCAL_SIG:
			return None

		try:
			(
				_sig,
				_ver,
				flags,
				method,
				_mtime,
				_mdate,
				_crc,
				csize,
				_usize,
				name_len,
				extra_len,
			) = struct.unpack("<4s5H3L2H", data[offset:offset + 30])
		except struct.error:
			return None

		name_start = offset + 30
		name_end = name_start + name_len
		extra_end = name_end + extra_len
		if extra_end > len(data):
			return None

		raw_name = data[name_start:name_end]
		name = _decode_name(raw_name, flags)
		return method, int(csize), flags, name, extra_end

	def _extract_content(method: int, data_start: int, size_hint: int | None) -> tuple[bytes, int] | None:
		if data_start < 0 or data_start > len(data):
			return None

		candidates: list[tuple[int, int]] = []
		if size_hint is not None and size_hint >= 0 and data_start + size_hint <= len(data):
			candidates.append((data_start, data_start + size_hint))

		next_sig = _next_zip_signature(data_start)
		if next_sig > data_start:
			range_by_sig = (data_start, next_sig)
			if range_by_sig not in candidates:
				candidates.append(range_by_sig)

		if not candidates:
			candidates.append((data_start, len(data)))

		for start, end in candidates:
			comp_data = data[start:end]
			try:
				if method == 0:
					return comp_data, end

				if method == 8:
					decompressor = zlib.decompressobj(-zlib.MAX_WBITS)
					content = decompressor.decompress(comp_data) + decompressor.flush()
					used = len(comp_data) - len(decompressor.unused_data)
					if used > 0:
						return content, start + used
					return content, end
			except Exception:
				continue

		return None

	central_entries: list[dict[str, int | str]] = []
	idx = 0
	while True:
		idx = data.find(CENTRAL_SIG, idx)
		if idx == -1:
			break
		if idx + 46 > len(data):
			break

		try:
			(
				_sig,
				_ver_made,
				_ver_needed,
				flags,
				method,
				_mtime,
				_mdate,
				_crc,
				csize,
				_usize,
				name_len,
				extra_len,
				comment_len,
				_disk_start,
				_int_attr,
				_ext_attr,
				local_offset,
			) = struct.unpack("<4s6H3L5H2L", data[idx:idx + 46])
		except struct.error:
			idx += 4
			continue

		name_start = idx + 46
		name_end = name_start + name_len
		block_end = name_end + extra_len + comment_len
		if block_end > len(data):
			idx += 4
			continue

		entry_name = _decode_name(data[name_start:name_end], int(flags))
		central_entries.append({
			"name": entry_name,
			"method": int(method),
			"csize": int(csize),
			"local_offset": int(local_offset),
		})

		idx = block_end

	# Recover entries primarily from central directory metadata.
	seen_names: set[str] = set()
	entry_index = 0
	with ZipFile(destination, "w", compression=ZIP_DEFLATED) as new_zip_file:
		for entry in central_entries:
			try:
				local_offset = _find_local_header_near(int(entry["local_offset"]))
				local_info = _read_local_header(local_offset)
				if local_info is None:
					continue

				local_method, local_csize, _local_flags, local_name_raw, data_start = local_info
				entry_name = _sanitize_name(str(entry["name"]), entry_index)
				local_name = _sanitize_name(local_name_raw, entry_index)
				entry_index += 1

				if entry_name.endswith("/") and not local_name.endswith("/"):
					entry_name = local_name

				method = int(entry["method"])
				if method not in (0, 8):
					method = local_method
				content_info = _extract_content(method, data_start, int(entry["csize"]))
				if content_info is None and local_csize >= 0:
					content_info = _extract_content(method, data_start, local_csize)
				if content_info is None:
					content_info = _extract_content(method, data_start, None)
				if content_info is None:
					continue

				content, _next_offset = content_info

				if entry_name in seen_names:
					base_name, dot, ext = entry_name.rpartition(".")
					if dot:
						entry_name = f"{base_name}_recovered.{ext}"
					else:
						entry_name = f"{entry_name}_recovered"

				seen_names.add(entry_name)
				new_zip_file.writestr(entry_name, content)

			except Exception:
				continue

		# Fallback: recover pack.mcmeta from local entries when central metadata is too damaged.
		if "pack.mcmeta" not in seen_names:
			idx = 0
			while True:
				idx = data.find(LOCAL_SIG, idx)
				if idx == -1:
					break

				local_info = _read_local_header(idx)
				if local_info is None:
					idx += 4
					continue

				method, local_csize, _flags, local_name_raw, data_start = local_info
				entry_name = _sanitize_name(local_name_raw, entry_index)
				entry_index += 1

				if entry_name.lower() != "pack.mcmeta":
					idx += 4
					continue

				content_info = _extract_content(method, data_start, local_csize)
				if content_info is None:
					content_info = _extract_content(method, data_start, None)
				if content_info is None:
					idx += 4
					continue

				content, _next_offset = content_info
				new_zip_file.writestr("pack.mcmeta", content)
				seen_names.add("pack.mcmeta")
				break

				idx += 4

	return True

