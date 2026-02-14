
# Imports
from typing import IO, Any

from ..config import StouputilsConfig as Cfg
from .utils import remove_colors


# TeeMultiOutput class to duplicate output to multiple file-like objects
class TeeMultiOutput:
	""" File-like object that duplicates output to multiple file-like objects.

	Args:
		*files         (IO[Any]):  One or more file-like objects that have write and flush methods
		strip_colors   (bool):     Strip ANSI color codes from output sent to non-stdout/stderr files
		ascii_only     (bool):     Replace non-ASCII characters with their ASCII equivalents for non-stdout/stderr files
		ignore_lineup  (bool):     Ignore lines containing LINE_UP escape sequence in non-terminal outputs

	Examples:
		>>> import sys
		>>> f = open("logfile.txt", "w")
		>>> sys.stdout = TeeMultiOutput(sys.stdout, f)
		>>> print("Hello World")  # Output goes to both console and file
		Hello World
		>>> f.close()	# TeeMultiOutput will handle any future writes to closed files gracefully
	"""
	def __init__(
		self, *files: IO[Any], strip_colors: bool = True, ascii_only: bool = True, ignore_lineup: bool = True
	) -> None:
		# Flatten any TeeMultiOutput instances in files
		flattened_files: list[IO[Any]] = []
		for file in files:
			if isinstance(file, TeeMultiOutput):
				flattened_files.extend(file.files)
			else:
				flattened_files.append(file)

		self.files: tuple[IO[Any], ...] = tuple(flattened_files)
		""" File-like objects to write to """
		self.strip_colors: bool = strip_colors
		""" Whether to strip ANSI color codes from output sent to non-stdout/stderr files """
		self.ascii_only: bool = ascii_only
		""" Whether to replace non-ASCII characters with their ASCII equivalents for non-stdout/stderr files """
		self.ignore_lineup: bool = ignore_lineup
		""" Whether to ignore lines containing LINE_UP escape sequence in non-terminal outputs """

	@property
	def encoding(self) -> str:
		""" Get the encoding of the first file, or "utf-8" as fallback.

		Returns:
			str: The encoding, ex: "utf-8", "ascii", "latin1", etc.
		"""
		try:
			return self.files[0].encoding	# type: ignore
		except (IndexError, AttributeError):
			return "utf-8"

	def write(self, obj: str) -> int:
		""" Write the object to all files while stripping colors if needed.

		Args:
			obj (str): String to write
		Returns:
			int: Number of characters written to the first file
		"""
		files_to_remove: list[IO[Any]] = []
		num_chars_written: int = 0
		for i, f in enumerate(self.files):
			try:
				# Check if file is closed
				if hasattr(f, "closed") and f.closed:
					files_to_remove.append(f)
					continue

				# Check if this file is a terminal/console or a regular file
				content: str = obj
				if not (hasattr(f, "isatty") and f.isatty()):
					# Non-terminal files get processed content (stripped colors, ASCII-only, etc.)

					# Skip content if it contains LINE_UP and ignore_lineup is True
					if self.ignore_lineup and (Cfg.LINE_UP in content or "\r" in content):
						continue

					# Strip colors if needed
					if self.strip_colors:
						content = remove_colors(content)

					# Replace Unicode block characters with ASCII equivalents
					# Replace other problematic Unicode characters as needed
					if self.ascii_only:
						content = content.replace('█', '#')
						content = ''.join(c if ord(c) < 128 else '?' for c in content)

				# Write content to file
				if i == 0:
					num_chars_written = f.write(content)
				else:
					f.write(content)

			except ValueError:
				# ValueError is raised when writing to a closed file
				files_to_remove.append(f)
			except Exception:
				pass

		# Remove closed files from the list
		if files_to_remove:
			self.files = tuple(f for f in self.files if f not in files_to_remove)
		return num_chars_written

	def flush(self) -> None:
		""" Flush all files. """
		for f in self.files:
			try:
				f.flush()
			except Exception:
				pass

	def fileno(self) -> int:
		""" Return the file descriptor of the first file. """
		return self.files[0].fileno() if hasattr(self.files[0], "fileno") else 0

