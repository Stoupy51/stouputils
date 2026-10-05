
# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import re
import threading
from contextlib import suppress
from typing import IO, Any

from .utils import remove_colors

# Regular expression to detect the escape sequences moving the cursor up or down a line (e.g., "\x1b[1A" or "\x1b[2B")
LINEUP_RE: re.Pattern[str] = re.compile(r'\x1b\[\d*[AB]')


# TeeMultiOutput class to duplicate output to multiple file-like objects
class TeeMultiOutput:
	""" File-like object that duplicates output to multiple file-like objects.

	Args:
		*files:        One or more file-like objects that have write and flush methods
		strip_colors:  Strip ANSI color codes from output sent to non-stdout/stderr files
		ascii_only:    Replace non-ASCII characters with their ASCII equivalents for non-stdout/stderr files
		ignore_lineup: Write to non-terminal outputs what a terminal ends up showing: a line redrawn with carriage returns,
			such as a progress bar, once in its final state, and nothing that moves the cursor to another line
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
		""" Whether non-terminal outputs receive the final state of redrawn lines and no cursor movement """
		self.pending: str = ""
		""" Unfinished last line that non-terminal outputs receive once it ends, when ignore_lineup is set """
		self.pending_lock: threading.Lock = threading.Lock()
		""" Keeps two threads writing at once from losing each other's text in ``pending`` """

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
		""" What a non-terminal file receives of the text, None when nothing.

		With ignore_lineup, only finished lines come out, each in the state its last carriage return left it,
		and a text moving the cursor to another line gives nothing.
		"""
		if self.ignore_lineup:
			if LINEUP_RE.search(text):
				return None
			with self.pending_lock:
				*lines, unfinished = (self.pending + text).split("\n")
				self.pending = last_drawing(unfinished) + "\r" * unfinished.endswith("\r")
			text = "".join(f"{last_drawing(line)}\n" for line in lines)
		return self.ascii_text(text) or None

	def flush_pending(self) -> None:
		""" Write the unfinished last line to the non-terminal files, as when the stream ends. """
		with self.pending_lock:
			text: str = self.ascii_text(last_drawing(self.pending))
			self.pending = ""
		if text:
			for f in self.files:
				self.write_to(f, "", text)

	def ascii_text(self, text: str) -> str:
		""" The text with its non-ASCII characters replaced when ascii_only is set. """
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


def last_drawing(line: str) -> str:
	""" What a terminal shows of a line redrawn with carriage returns: the text after the last one that something followed.

	>>> last_drawing("\\r 10%\\r 50%\\r100%"), last_drawing("done\\r"), last_drawing("plain")
	('100%', 'done', 'plain')
	"""
	return line.rstrip("\r").rsplit("\r", 1)[-1]

