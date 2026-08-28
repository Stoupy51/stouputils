
# Lazy imports (PEP 810), ignored before Python 3.15
from ...lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import contextlib
import os
from dataclasses import dataclass, field
from typing import ClassVar
from zipfile import ZIP_DEFLATED, ZipFile

from ...decorators.error_handling import handle_error
from .scanner import CentralEntry, ZipScanner


# Classes
@dataclass
class RecoveredArchive:
	""" Archive being rebuilt, which decides what each recovered entry is named. """
	METADATA_NAME: ClassVar[str] = "pack.mcmeta"
	""" Entry worth a second recovery pass, since a pack is worthless without it. """
	SUPPORTED_METHODS: ClassVar[tuple[int, ...]] = (0, 8)
	""" Compression methods this module can decode, stored and deflated. """

	scanner: ZipScanner
	""" View over the damaged archive. """
	zip_file: ZipFile
	""" Archive being written. """
	seen_names: set[str] = field(default_factory=set[str])
	""" Names already written, so a duplicate never silently replaces an entry. """
	entry_index: int = 0
	""" Counter naming the entries whose own name did not survive. """

	def unique_name(self, name: str) -> str:
		""" Make a name that no written entry uses yet.

		Args:
			name: Name the entry would like to take
		Returns:
			Same name, or a suffixed variant when it is already taken
		Examples:
			>>> import io
			>>> with ZipFile(io.BytesIO(), "w") as zip_file:
			...     archive = RecoveredArchive(scanner=ZipScanner(b""), zip_file=zip_file, seen_names={"a.png"})
			...     archive.unique_name("a.png")
			'a_recovered.png'
		"""
		if name not in self.seen_names:
			return name

		base_name, dot, extension = name.rpartition(".")
		if dot:
			return f"{base_name}_recovered.{extension}"
		return f"{name}_recovered"

	def write(self, name: str, content: bytes) -> None:
		""" Write one recovered entry.

		Args:
			name:    Name to write the entry under
			content: Decompressed content
		"""
		self.seen_names.add(name)
		self.zip_file.writestr(name, content)

	def write_central_entry(self, entry: CentralEntry) -> None:
		""" Recover one entry from its central directory metadata, doing nothing when it cannot be read.

		Args:
			entry: Entry announced by the central directory
		"""
		with contextlib.suppress(Exception):
			header = self.scanner.read_local_header(self.scanner.find_local_header_near(entry.local_offset))
			if header is None:
				return

			name: str = self.scanner.sanitize_name(entry.name, self.entry_index)
			local_name: str = self.scanner.sanitize_name(header.name, self.entry_index)
			self.entry_index += 1

			# The directory sometimes announces a directory where the local header knows a real file
			if name.endswith("/") and not local_name.endswith("/"):
				name = local_name

			method: int = entry.method if entry.method in self.SUPPORTED_METHODS else header.method
			for size_hint in (entry.csize, header.csize if header.csize >= 0 else None, None):
				content = self.scanner.extract_content(method, header.data_start, size_hint)
				if content is not None:
					self.write(self.unique_name(name), content[0])
					return

	def recover_metadata(self) -> None:
		""" Scan the local headers for the metadata entry, used when the central directory is too damaged. """
		idx: int = 0
		while True:
			idx = self.scanner.data.find(self.scanner.LOCAL_SIGNATURE, idx)
			if idx == -1:
				break

			header = self.scanner.read_local_header(idx)
			idx += 4
			if header is None:
				continue

			name: str = self.scanner.sanitize_name(header.name, self.entry_index)
			self.entry_index += 1
			if name.lower() != self.METADATA_NAME:
				continue

			for size_hint in (header.csize, None):
				content = self.scanner.extract_content(header.method, header.data_start, size_hint)
				if content is not None:
					self.write(self.METADATA_NAME, content[0])
					return


# Functions
@handle_error
def repair_zip_file(file_path: str, destination: str) -> bool:
	""" Try to repair a corrupted zip file by ignoring some of the errors

	This function manually parses the ZIP file structure to extract files
	even when the ZIP file is corrupted. It reads the central directory
	entries and attempts to decompress each file individually.

	Args:
		file_path:   Path of the zip file to repair
		destination: Destination of the new file
	Returns:
		Always returns True unless any strong error
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
		scanner = ZipScanner(f.read())

	# Recover entries primarily from central directory metadata
	with ZipFile(destination, "w", compression=ZIP_DEFLATED) as new_zip_file:
		archive = RecoveredArchive(scanner=scanner, zip_file=new_zip_file)
		for entry in scanner.central_entries():
			archive.write_central_entry(entry)

		if RecoveredArchive.METADATA_NAME not in archive.seen_names:
			archive.recover_metadata()

	return True

