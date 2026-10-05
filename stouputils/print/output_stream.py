
# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import re
from contextlib import suppress
from typing import IO, Any

from .utils import remove_colors

# Regular expression to detect LINE_UP escape sequences (e.g., "\x1b[1A" or "\x1b[2B")
LINEUP_RE: re.Pattern[str] = re.compile(r'\x1b\[\d*[AB]|\r')


# TeeMultiOutput class to duplicate output to multiple file-like objects
class TeeMultiOutput:
	""" File-like object that duplicates output to multiple file-like objects.

	Args:
		*files:        One or more file-like objects that have write and flush methods
		strip_colors:  Strip ANSI color codes from output sent to non-stdout/stderr files
		ascii_only:    Replace non-ASCII characters with their ASCII equivalents for non-stdout/stderr files
		ignore_lineup: Ignore lines containing LINE_UP escape sequence in non-terminal outputs
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
			The encoding, ex: "utf-8", "ascii", "latin1", etc.
		"""
		try:
			return self.files[0].encoding   # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownVariableType]
		except (IndexError, AttributeError):
			return "utf-8"

	def write(self, obj: str) -> int:
		""" Write the object to all files while stripping colors if needed.

		Args:
			obj: String to write
		Returns:
			Number of characters written to the first file
		"""
		terminal_text: str = remove_colors(obj) if self.strip_colors else obj
		file_text: str | None = self.file_text(terminal_text)
		counts: list[int | None] = [self.write_to(f, terminal_text, file_text) for f in self.files]
		self.files = tuple(f for f, count in zip(self.files, counts, strict=True) if count is not None)
		return (counts[0] or 0) if counts else 0

	@staticmethod
	def write_to(f: IO[Any], terminal_text: str, file_text: str | None) -> int | None:
		""" Write to one file the text its kind receives, a terminal or anything else.

		Returns:
			Characters written, or None when the file is closed and has to be dropped.
		"""
		try:
			if getattr(f, "closed", False):
				return None
			text: str | None = terminal_text if hasattr(f, "isatty") and f.isatty() else file_text
			return 0 if text is None else f.write(text) or 0

		# ValueError is raised when writing to a closed file
		except ValueError:
			return None
		except Exception:
			return 0

	def file_text(self, text: str) -> str | None:
		""" What a non-terminal file receives, None when the text only moves a terminal cursor and lineups are ignored. """
		if self.ignore_lineup and LINEUP_RE.search(text):
			return None
		if not self.ascii_only:
			return text
		return "".join(c if ord(c) < 128 else "?" for c in text.replace("█", "#"))

	def flush(self) -> None:
		for f in self.files:
			with suppress(Exception):
				f.flush()

	def fileno(self) -> int:
		""" Return the file descriptor of the first file. """
		return self.files[0].fileno() if hasattr(self.files[0], "fileno") else 0

	def isatty(self) -> bool:
		""" Return True if the first file is a terminal/console. """
		return hasattr(self.files[0], "isatty") and self.files[0].isatty()

