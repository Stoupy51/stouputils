"""
This module provides a zip file override to handle some corrupted zip files.

For instance, some Minecraft servers resource packs are slightly corrupted
and cannot be opened with the standard zipfile module.
See the archive.py module for more information.
"""

# Imports
from zipfile import (
	_FH_EXTRA_FIELD_LENGTH,  # type: ignore
	ZipExtFile,
	ZipFile,
	ZipInfo,
	_SharedFile,  # type: ignore
	crc32,  # type: ignore
	sizeFileHeader,  # type: ignore
	struct,  # type: ignore
	structFileHeader,  # type: ignore
)


# Class overrides
class ZipExtFileOverride(ZipExtFile):
	""" Override of the ZipExtFile class """

	def _update_crc(self, newdata) -> None:	# type: ignore
		""" Override of the _update_crc method """
		# Update the CRC using the given data.
		if self._expected_crc is None:	# type: ignore
			# No need to compute the CRC if we don't have a reference value
			return
		self._running_crc = crc32(newdata, self._running_crc)	# type: ignore

class ZipFileOverride(ZipFile):
	""" Override of the ZipFile class """

	def open(self, name, mode="r", pwd=None, *, force_zip64=False):	# type: ignore
		"""Return file-like object for 'name'.

		name is a string for the file name within the ZIP file, or a ZipInfo
		object.

		mode should be 'r' to read a file already in the ZIP file, or 'w' to
		write to a file newly added to the archive.

		pwd is the password to decrypt files (only used for reading).

		When writing, if the file size is not known in advance but may exceed
		2 GiB, pass force_zip64 to use the ZIP64 format, which can handle large
		files.  If the size is known in advance, it is best to pass a ZipInfo
		instance for name, with zinfo.file_size set.
		"""
		if mode not in {"r", "w"}:
			raise ValueError('open() requires mode "r" or "w"')
		if pwd and (mode == "w"):
			raise ValueError("pwd is only supported for reading files")
		if not self.fp:
			raise ValueError(
				"Attempt to use ZIP archive that was already closed")

		# Make sure we have an info object
		if isinstance(name, ZipInfo):
			# 'name' is already an info object
			zinfo = name
		elif mode == 'w':
			zinfo = ZipInfo(name)
			zinfo.compress_type = self.compression
			zinfo._compresslevel = self.compresslevel	# type: ignore
		else:
			# Get info object for name
			zinfo = self.getinfo(name)

		if mode == 'w':
			return self._open_to_write(zinfo, force_zip64=force_zip64)	# type: ignore

		if self._writing:	# type: ignore
			raise ValueError("Can't read from the ZIP file while there "
					"is an open writing handle on it. "
					"Close the writing handle before trying to read.")

		# Open for reading:
		self._fileRefCnt += 1	# type: ignore
		zef_file = _SharedFile(self.fp, zinfo.header_offset,	# type: ignore
								self._fpclose, self._lock, lambda: self._writing)	# type: ignore
		try:
			# Skip the file header:
			fheader = zef_file.read(sizeFileHeader)	# type: ignore
			fheader = struct.unpack(structFileHeader, fheader)	# type: ignore

			if fheader[_FH_EXTRA_FIELD_LENGTH]:
				zef_file.seek(fheader[_FH_EXTRA_FIELD_LENGTH], whence=1)	# type: ignore

			if zinfo.flag_bits & 0x20:
				# Zip 2.7: compressed patched data
				raise NotImplementedError("compressed patched data (flag bit 5)")

			if zinfo.flag_bits & 0x40:
				# strong encryption
				raise NotImplementedError("strong encryption (flag bit 6)")

			# if (zinfo._end_offset is not None and
			# 	zef_file.tell() + zinfo.compress_size > zinfo._end_offset):
			# 	raise BadZipFile(f"Overlapped entries: {zinfo.orig_filename!r} (possible zip bomb)")

			# check for encrypted flag & handle password
			is_encrypted = zinfo.flag_bits & 0x1
			if is_encrypted:
				if not pwd:
					pwd = self.pwd
				if pwd and not isinstance(pwd, bytes):	# type: ignore
					raise TypeError(f"pwd: expected bytes, got {type(pwd).__name__}")
				if not pwd:
					raise RuntimeError(f"File {name!r} is encrypted, password required for extraction")
			else:
				pwd = None

			return ZipExtFileOverride(zef_file, mode, zinfo, pwd, True)	# type: ignore
		except:
			zef_file.close()	# type: ignore
			raise

