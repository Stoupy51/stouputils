
from zipfile import *
from zipfile import _SharedFile, \
	sizeFileHeader, struct, structFileHeader, _FH_FILENAME_LENGTH, _FH_EXTRA_FIELD_LENGTH, _MASK_COMPRESSED_PATCH, \
	_MASK_STRONG_ENCRYPTION, _FH_GENERAL_PURPOSE_FLAG_BITS, _MASK_UTF_FILENAME, _MASK_ENCRYPTED, ZipExtFile, crc32

class ZipExtFileOverride(ZipExtFile):
	def _update_crc(self, newdata):
		# Update the CRC using the given data.
		if self._expected_crc is None:
			# No need to compute the CRC if we don't have a reference value
			return
		self._running_crc = crc32(newdata, self._running_crc)

class ZipFileOverride(ZipFile):

	def open(self, name, mode="r", pwd=None, *, force_zip64=False):
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
			zinfo._compresslevel = self.compresslevel
		else:
			# Get info object for name
			zinfo = self.getinfo(name)

		if mode == 'w':
			return self._open_to_write(zinfo, force_zip64=force_zip64)

		if self._writing:
			raise ValueError("Can't read from the ZIP file while there "
					"is an open writing handle on it. "
					"Close the writing handle before trying to read.")

		# Open for reading:
		self._fileRefCnt += 1
		zef_file = _SharedFile(self.fp, zinfo.header_offset,
								self._fpclose, self._lock, lambda: self._writing)
		try:
			# Skip the file header:
			fheader = zef_file.read(sizeFileHeader)
			fheader = struct.unpack(structFileHeader, fheader)

			fname = zef_file.read(fheader[_FH_FILENAME_LENGTH])
			if fheader[_FH_EXTRA_FIELD_LENGTH]:
				zef_file.seek(fheader[_FH_EXTRA_FIELD_LENGTH], whence=1)

			if zinfo.flag_bits & _MASK_COMPRESSED_PATCH:
				# Zip 2.7: compressed patched data
				raise NotImplementedError("compressed patched data (flag bit 5)")

			if zinfo.flag_bits & _MASK_STRONG_ENCRYPTION:
				# strong encryption
				raise NotImplementedError("strong encryption (flag bit 6)")

			if fheader[_FH_GENERAL_PURPOSE_FLAG_BITS] & _MASK_UTF_FILENAME:
				# UTF-8 filename
				fname_str = fname.decode("utf-8")
			else:
				fname_str = fname.decode(self.metadata_encoding or "cp437")

			# if (zinfo._end_offset is not None and
			# 	zef_file.tell() + zinfo.compress_size > zinfo._end_offset):
			# 	raise BadZipFile(f"Overlapped entries: {zinfo.orig_filename!r} (possible zip bomb)")

			# check for encrypted flag & handle password
			is_encrypted = zinfo.flag_bits & _MASK_ENCRYPTED
			if is_encrypted:
				if not pwd:
					pwd = self.pwd
				if pwd and not isinstance(pwd, bytes):
					raise TypeError("pwd: expected bytes, got %s" % type(pwd).__name__)
				if not pwd:
					raise RuntimeError("File %r is encrypted, password "
										"required for extraction" % name)
			else:
				pwd = None

			return ZipExtFileOverride(zef_file, mode, zinfo, pwd, True)
		except:
			zef_file.close()
			raise

