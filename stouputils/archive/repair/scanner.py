""" Byte level scanning of a zip archive whose structure cannot be trusted.

The standard library refuses to open a damaged archive, so every offset here is treated as a hint:
signatures are searched for, headers are bounds checked, and anything unreadable is reported as None.
"""
# Lazy imports (PEP 810), ignored before Python 3.15
from ...lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import bisect
import struct
import zlib
from dataclasses import dataclass, field
from typing import ClassVar


# Classes
@dataclass(frozen=True)
class LocalHeader:
	""" Local file header, once read and bounds checked. """
	method: int
	""" Compression method, 0 for stored and 8 for deflated. """
	csize: int
	""" Compressed size announced by the header, often wrong in a damaged archive. """
	flags: int
	""" General purpose bit flags. """
	name: str
	""" Entry name as decoded from the header. """
	data_start: int
	""" Offset of the first compressed byte, right after the name and extra fields. """

@dataclass(frozen=True)
class CentralEntry:
	""" Central directory entry, which usually survives better than the local headers. """
	name: str
	""" Entry name as decoded from the directory. """
	method: int
	""" Compression method announced by the directory. """
	csize: int
	""" Compressed size announced by the directory. """
	local_offset: int
	""" Announced offset of the matching local header, used as a hint only. """

@dataclass
class ZipScanner:
	""" Read only view over the bytes of an archive, with every lookup tolerant to corruption.

	Examples:
		>>> import io, zipfile
		>>> buffer = io.BytesIO()
		>>> with zipfile.ZipFile(buffer, "w") as archive:
		...     archive.writestr("pack.mcmeta", '{"pack": {}}')
		>>> scanner = ZipScanner(buffer.getvalue())
		>>> [entry.name for entry in scanner.central_entries()]
		['pack.mcmeta']
	"""
	LOCAL_SIGNATURE: ClassVar[bytes] = b"PK\x03\x04"
	""" Magic bytes starting a local file header. """
	CENTRAL_SIGNATURE: ClassVar[bytes] = b"PK\x01\x02"
	""" Magic bytes starting a central directory entry. """
	EOCD_SIGNATURE: ClassVar[bytes] = b"PK\x05\x06"
	""" Magic bytes starting the end of central directory record. """
	LOCAL_HEADER_SIZE: ClassVar[int] = 30
	""" Size of a local file header, before its variable length name and extra fields. """
	CENTRAL_HEADER_SIZE: ClassVar[int] = 46
	""" Size of a central directory entry, before its variable length name, extra and comment fields. """
	UTF8_NAME_FLAG: ClassVar[int] = 0x0800
	""" General purpose bit telling that the entry name is utf-8 encoded instead of cp437. """
	SEARCH_BACKWARD: ClassVar[int] = 32
	""" How far before a broken offset hint a local header is looked for. """
	SEARCH_FORWARD: ClassVar[int] = 8192
	""" How far after a broken offset hint a local header is looked for. """

	data: bytes
	""" Whole archive, read in memory once. """
	signature_positions: list[int] = field(init=False)
	""" Sorted offsets of every zip signature, used to guess where a compressed stream ends. """

	def __post_init__(self) -> None:
		self.signature_positions = sorted(set(
			self.find_all(self.LOCAL_SIGNATURE) + self.find_all(self.CENTRAL_SIGNATURE) + self.find_all(self.EOCD_SIGNATURE)
		))

	@property
	def size(self) -> int:
		""" Total number of bytes of the archive. """
		return len(self.data)

	def find_all(self, signature: bytes) -> list[int]:
		""" Collect every offset where the signature appears.

		Args:
			signature (bytes): Magic bytes to look for
		Returns:
			list[int]: Offsets in increasing order
		"""
		positions: list[int] = []
		idx: int = self.data.find(signature)
		while idx != -1:
			positions.append(idx)
			idx = self.data.find(signature, idx + 1)
		return positions

	def next_signature(self, start: int) -> int:
		""" Offset of the first zip signature at or after the given position, or the end of the archive.

		Args:
			start (int): Offset to search from
		Returns:
			int: Offset of the next signature, or the archive size when there is none
		"""
		position: int = bisect.bisect_left(self.signature_positions, start)
		if position >= len(self.signature_positions):
			return self.size
		return self.signature_positions[position]

	@staticmethod
	def decode_name(raw_name: bytes, flags: int) -> str:
		""" Decode an entry name with the encoding announced by the header flags.

		Args:
			raw_name (bytes): Name as stored in the archive
			flags    (int):   General purpose bit flags of the entry
		Returns:
			str: Decoded name, with unreadable bytes replaced

		Examples:
			>>> ZipScanner.decode_name(b"assets/", 0)
			'assets/'
		"""
		if flags & ZipScanner.UTF8_NAME_FLAG:
			return raw_name.decode("utf-8", errors="replace")
		return raw_name.decode("cp437", errors="replace")

	@staticmethod
	def sanitize_name(name: str, fallback_index: int) -> str:
		""" Turn a possibly damaged entry name into a name safe to write in the repaired archive.

		Args:
			name           (str): Decoded entry name
			fallback_index (int): Index used to name an entry whose name is empty
		Returns:
			str: Sanitized name

		Examples:
			>>> ZipScanner.sanitize_name("\\\\assets\\\\icon.png", 0)
			'assets/icon.png'
			>>> ZipScanner.sanitize_name("", 7)
			'recovered_7'
		"""
		sanitized: str = name.replace("\\", "/").lstrip("/")

		# A metadata file should not be a directory; this helps common pack corruption cases.
		if sanitized.lower() in {"pack.mcmeta", "pack.mcmeta/"}:
			return "pack.mcmeta"

		if sanitized.endswith("/") and "." in sanitized.rsplit("/", 1)[-1]:
			sanitized = sanitized.rstrip("/")

		if not sanitized:
			sanitized = f"recovered_{fallback_index}"

		return sanitized

	def find_local_header_near(self, offset_hint: int) -> int:
		""" Look for a local header around an offset announced by the central directory.

		Args:
			offset_hint (int): Offset announced by the central directory
		Returns:
			int: Offset of the closest local header, or -1 when none is found nearby
		"""
		if 0 <= offset_hint <= self.size - 4 and self.data[offset_hint:offset_hint + 4] == self.LOCAL_SIGNATURE:
			return offset_hint
		if 0 <= offset_hint + 4 <= self.size - 4 and self.data[offset_hint + 4:offset_hint + 8] == self.LOCAL_SIGNATURE:
			return offset_hint + 4

		end: int = min(self.size, offset_hint + self.SEARCH_FORWARD)
		candidates: list[int] = []
		search_at: int = max(0, offset_hint - self.SEARCH_BACKWARD)
		while True:
			position: int = self.data.find(self.LOCAL_SIGNATURE, search_at, end)
			if position == -1:
				break
			candidates.append(position)
			search_at = position + 1

		if not candidates:
			return -1
		return min(candidates, key=lambda position: abs(position - offset_hint))

	def read_local_header(self, offset: int) -> LocalHeader | None:
		""" Read the local header at the given offset.

		Args:
			offset (int): Offset of the local signature
		Returns:
			LocalHeader | None: Header, or None when the bytes there cannot be read as one
		"""
		if offset < 0 or offset + self.LOCAL_HEADER_SIZE > self.size:
			return None
		if self.data[offset:offset + 4] != self.LOCAL_SIGNATURE:
			return None

		try:
			(
				_sig, _ver, flags, method, _mtime, _mdate, _crc, csize, _usize, name_len, extra_len,
			) = struct.unpack("<4s5H3L2H", self.data[offset:offset + self.LOCAL_HEADER_SIZE])
		except struct.error:
			return None

		name_start: int = offset + self.LOCAL_HEADER_SIZE
		name_end: int = name_start + name_len
		extra_end: int = name_end + extra_len
		if extra_end > self.size:
			return None

		return LocalHeader(
			method=int(method),
			csize=int(csize),
			flags=int(flags),
			name=self.decode_name(self.data[name_start:name_end], int(flags)),
			data_start=extra_end,
		)

	def decode_range(self, method: int, data_start: int, end: int) -> tuple[bytes, int] | None:
		""" Decompress a candidate byte range.

		Args:
			method     (int): Compression method, 0 for stored and 8 for deflated
			data_start (int): Offset of the first compressed byte
			end        (int): Offset where the compressed stream is assumed to end
		Returns:
			tuple[bytes, int] | None: Content and offset right after it, or None when it does not decode
		"""
		compressed: bytes = self.data[data_start:end]
		try:
			if method == 0:
				return compressed, end

			if method == 8:
				decompressor = zlib.decompressobj(-zlib.MAX_WBITS)
				content: bytes = decompressor.decompress(compressed) + decompressor.flush()
				used: int = len(compressed) - len(decompressor.unused_data)
				if used > 0:
					return content, data_start + used
				return content, end
		except Exception:
			return None

		return None

	def extract_content(self, method: int, data_start: int, size_hint: int | None) -> tuple[bytes, int] | None:
		""" Decompress an entry, trying the announced size first and then guessed ends.

		Args:
			method     (int):       Compression method, 0 for stored and 8 for deflated
			data_start (int):       Offset of the first compressed byte
			size_hint  (int | None): Compressed size announced by a header, when there is one
		Returns:
			tuple[bytes, int] | None: Content and offset right after it, or None when nothing decodes
		"""
		if data_start < 0 or data_start > self.size:
			return None

		ends: list[int] = []
		if size_hint is not None and size_hint >= 0 and data_start + size_hint <= self.size:
			ends.append(data_start + size_hint)

		next_signature: int = self.next_signature(data_start)
		if next_signature > data_start:
			ends.append(next_signature)
		if next_signature != self.size:
			ends.append(self.size)

		for end in ends:
			content = self.decode_range(method, data_start, end)
			if content is not None:
				return content

		return None

	def central_entries(self) -> list[CentralEntry]:
		""" Read every readable central directory entry.

		Returns:
			list[CentralEntry]: Entries in the order they appear in the archive
		"""
		entries: list[CentralEntry] = []
		idx: int = 0
		while True:
			idx = self.data.find(self.CENTRAL_SIGNATURE, idx)
			if idx == -1 or idx + self.CENTRAL_HEADER_SIZE > self.size:
				break

			try:
				(
					_sig, _ver_made, _ver_needed, flags, method, _mtime, _mdate, _crc, csize, _usize,
					name_len, extra_len, comment_len, _disk_start, _int_attr, _ext_attr, local_offset,
				) = struct.unpack("<4s6H3L5H2L", self.data[idx:idx + self.CENTRAL_HEADER_SIZE])
			except struct.error:
				idx += 4
				continue

			name_start: int = idx + self.CENTRAL_HEADER_SIZE
			name_end: int = name_start + name_len
			block_end: int = name_end + extra_len + comment_len
			if block_end > self.size:
				idx += 4
				continue

			entries.append(CentralEntry(
				name=self.decode_name(self.data[name_start:name_end], int(flags)),
				method=int(method),
				csize=int(csize),
				local_offset=int(local_offset),
			))
			idx = block_end

		return entries

