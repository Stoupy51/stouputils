
# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import re
import threading
import time
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass, field
from typing import IO, Any, Literal

from .utils import remove_colors

# Constants
# Regular expression to detect the escape sequences moving the cursor up or down a line (e.g., "\x1b[1A" or "\x1b[2B")
LINEUP_RE: re.Pattern[str] = re.compile(r'\x1b\[\d*[AB]')

LINE_TOKENS_RE: re.Pattern[str] = re.compile(r"(\n|\r|\x1b\[\d*[AB])")
""" Splits a text around what moves a terminal cursor: newlines, carriage returns and line moves. """

REDRAW_CHECKPOINT_SECONDS: float = 60.0
""" Interval at which a file receives the current state of a line still being redrawn, such as a long progress bar. """


# Classes
@dataclass
class LineState:
	""" Where a non-terminal output stands in the line one thread is writing, so it receives what a terminal ends up showing.

	Text is held until its line ends or the stream is flushed, like a terminal's line-buffered stdout.
	Lines from several threads therefore never cut into each other.
	A line drawn again after a carriage return, such as a progress bar, is written once in its final state,
	plus every ``checkpoint_seconds`` while it lasts.
	A line starting with a cursor move rewrites the previous one, as stouputils does for a repeated message,
	and the last of such a series is written when the series ends.

	>>> state = LineState()
	>>> state.feed("\\r 10%") + state.feed("\\r100%\\n") + state.feed("done\\n")
	'100%\\ndone\\n'
	>>> state.feed("same\\n") + state.feed("\\x1b[1Asame (x2)\\n") + state.feed("\\x1b[1Asame (x3)\\n") + state.feed("other\\n")
	'same\\nsame (x3)\\nother\\n'
	>>> state.feed("Processing..."), state.flush(), state.feed(" done\\n")
	('', 'Processing...', ' done\\n')
	"""
	checkpoint_seconds: float = REDRAW_CHECKPOINT_SECONDS
	mode: Literal["start", "text", "redraw", "repeat"] = "start"
	""" What the current line is: not started, plain text, drawn again after a carriage return, or rewriting the previous line. """
	buffer: str = ""
	""" Text of the current line not written yet, its last drawing for a redrawn line. """
	shown: bool = False
	""" Whether a flush already wrote the start of the current line. """
	carriage: bool = False
	""" Whether a carriage return came since the last text, so the next text draws the line again. """
	held_repeat: str = ""
	""" Last line of a series of rewrites, written once the series ends. """
	since: float = 0.0
	""" ``time.monotonic()`` of the last checkpoint of a redrawn line. """

	def feed(self, text: str) -> str:
		""" What the output receives of the text, given the lines before it. """
		return "".join(self.take(token) for token in LINE_TOKENS_RE.split(text) if token)

	def take(self, token: str) -> str:
		""" What the output receives of one token: a newline, a carriage return, a line move or plain text. """
		if token == "\n":
			return self.end_line()
		if token == "\r":
			self.carriage = True
		elif LINEUP_RE.fullmatch(token) is None:
			return self.draw(token)
		elif self.mode == "start":
			self.mode = "repeat"
		return ""

	def draw(self, token: str) -> str:
		""" Add text to the current line, a carriage return before it starting the drawing over. """
		released: str = self.release_repeat() if self.mode == "start" else ""
		if self.carriage and self.mode in ("start", "text"):
			self.mode, self.since = "redraw", time.monotonic()
		elif self.mode == "start":
			self.mode = "text"
		self.buffer = token if self.carriage else self.buffer + token
		self.carriage = False
		if self.mode == "redraw" and time.monotonic() - self.since >= self.checkpoint_seconds:
			self.since = time.monotonic()
			return released + self.new_line() + f"{self.buffer}\n"
		return released

	def end_line(self) -> str:
		""" Close the current line on a newline. """
		if self.mode == "repeat":
			self.held_repeat, self.mode, self.buffer, self.carriage = self.buffer, "start", "", False
			return ""
		released: str = self.release_repeat() if self.mode == "start" else ""
		line: str = (self.new_line() if self.mode == "redraw" else "") + self.buffer
		self.mode, self.buffer, self.carriage, self.shown = "start", "", False, False
		return f"{released}{line}\n"

	def flush(self) -> str:
		""" The unwritten text of a plain line, which a terminal shows on flush, so a step announced without newline shows. """
		if self.mode != "text":
			return ""
		flushed, self.buffer, self.shown = self.buffer, "", True
		return flushed

	def new_line(self) -> str:
		""" A newline ending the start of the line a flush already wrote, before a drawing that cannot erase it. """
		ended: str = "\n" if self.shown else ""
		self.shown = False
		return ended

	def release_repeat(self) -> str:
		""" The last line of a finished series of rewrites, written once. """
		released: str = f"{self.held_repeat}\n" if self.held_repeat else ""
		self.held_repeat = ""
		return released

	def finish(self) -> str:
		""" What the output still has to receive when the stream ends. """
		remaining: str = self.release_repeat() + self.buffer
		self.mode, self.buffer, self.carriage, self.shown = "start", "", False, False
		return remaining


@dataclass
class TeeTarget:
	""" One output of a :class:`TeeMultiOutput`, with how it is written to and which thread it listens to. """
	file: IO[Any]
	thread: int | None = None
	""" Thread identifier whose writes alone it receives, None for every thread. """
	strip_colors: bool = True
	ascii_only: bool = True
	""" Whether non-ASCII characters are replaced, when the output is not a terminal. """
	ignore_lineup: bool = True
	""" Whether the output receives what a terminal ends up showing, when it is not a terminal itself. """
	lines: dict[int, LineState] = field(default_factory=dict[int, LineState])
	""" The line each writing thread is at, by thread identifier. """
	lock: threading.Lock = field(default_factory=threading.Lock)
	""" Keeps two threads writing at once from mixing up ``lines``. """
	terminal: bool = field(init=False)
	""" Whether the output is a terminal, read once since asking costs a system call. """

	def __post_init__(self) -> None:
		try:
			self.terminal = hasattr(self.file, "isatty") and self.file.isatty()
		except ValueError:
			self.terminal = False

	def write(self, obj: str) -> int | None:
		""" Write the text as this output receives it.

		Returns:
			Characters written, or None when the output is closed and has to be dropped.
		"""
		try:
			if getattr(self.file, "closed", False):
				return None
			text: str = remove_colors(obj) if self.strip_colors and "\x1b" in obj else obj
			if not self.terminal:
				text = self.file_text(text, LineState.feed)
			return (self.file.write(text) or 0) if text else 0

		# ValueError is raised when writing to a closed file
		except ValueError:
			return None
		except Exception:
			return 0

	def flush(self) -> None:
		""" Flush the output, writing first the line the current thread left unfinished. """
		with suppress(Exception):
			if not self.terminal and not getattr(self.file, "closed", False):
				text: str = self.file_text("", lambda line, _: line.flush())
				if text:
					self.file.write(text)
			self.file.flush()

	def finish(self) -> None:
		""" Write what every thread's current line still holds back, as when the stream ends. """
		with self.lock:
			text: str = self.ascii_text("".join(line.finish() for line in self.lines.values()))
		if text and not getattr(self.file, "closed", False):
			with suppress(Exception):
				self.file.write(text)

	def file_text(self, text: str, step: Callable[[LineState, str], str]) -> str:
		""" What a non-terminal output receives of the text, ``step`` reading it with the current thread's line. """
		if self.ignore_lineup:
			with self.lock:
				text = step(self.lines.setdefault(threading.get_ident(), LineState()), text)
		return self.ascii_text(text)

	def ascii_text(self, text: str) -> str:
		""" The text with its non-ASCII characters replaced when ascii_only is set. """
		if not self.ascii_only or text.isascii():
			return text
		return "".join(c if ord(c) < 128 else "?" for c in text.replace("█", "#"))


# TeeMultiOutput class to duplicate output to multiple file-like objects
class TeeMultiOutput:
	""" File-like object that duplicates output to multiple file-like objects.

	Outputs can be added and removed while it is in place, each one listening to every thread or to a single one.

	Args:
		*files:        One or more file-like objects that have write and flush methods
		strip_colors:  Strip ANSI color codes from output sent to these files
		ascii_only:    Replace non-ASCII characters with their ASCII equivalents for non-stdout/stderr files
		ignore_lineup: Write to non-terminal outputs what a terminal ends up showing, see :class:`LineState`
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
		self.targets: tuple[TeeTarget, ...] = tuple(
			TeeTarget(inner, strip_colors=strip_colors, ascii_only=ascii_only, ignore_lineup=ignore_lineup)
			for file in files
			for inner in (file.files if isinstance(file, TeeMultiOutput) else (file,))
		)
		""" Outputs written to, the first one standing for the stream this object replaces """
		self.removable: bool = False
		""" Whether :class:`~stouputils.ctx.LogToFile` put it in place, and takes it away with the last file it holds """

	@property
	def files(self) -> tuple[IO[Any], ...]:
		""" File-like objects written to """
		return tuple(target.file for target in self.targets)

	@property
	def encoding(self) -> str:
		""" Get the encoding of the first file, or "utf-8" as fallback.
		Returns:
			The encoding, ex: "utf-8", "ascii", "latin1", etc.
		"""
		try:
			return self.targets[0].file.encoding   # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownVariableType]
		except (IndexError, AttributeError):
			return "utf-8"

	def write(self, obj: str) -> int:
		""" Write the object to every output listening to the current thread.

		Args:
			obj: String to write
		Returns:
			Number of characters written to the first file
		"""
		thread: int = threading.get_ident()
		targets: tuple[TeeTarget, ...] = self.targets
		counts: list[int | None] = [target.write(obj) if target.thread in (None, thread) else 0 for target in targets]
		if None in counts:
			closed: set[int] = {id(target) for target, count in zip(targets, counts, strict=True) if count is None}
			self.targets = tuple(target for target in self.targets if id(target) not in closed)
		return (counts[0] or 0) if counts else 0

	def add_file(
		self, file: IO[Any], thread: int | None = None, strip_colors: bool = True, ascii_only: bool = True, ignore_lineup: bool = True
	) -> None:
		""" Start writing to one more output.

		Args:
			thread: Thread identifier whose writes alone it receives, None for every thread.
		"""
		target = TeeTarget(file, thread=thread, strip_colors=strip_colors, ascii_only=ascii_only, ignore_lineup=ignore_lineup)
		self.targets = (*self.targets, target)

	def remove_file(self, file: IO[Any]) -> None:
		""" Stop writing to an output, after giving it what its current line still holds back. """
		for target in self.targets:
			if target.file is file:
				target.finish()
		self.targets = tuple(target for target in self.targets if target.file is not file)

	def flush(self) -> None:
		for target in self.targets:
			target.flush()

	def fileno(self) -> int:
		""" Return the file descriptor of the first file. """
		return self.targets[0].file.fileno() if hasattr(self.targets[0].file, "fileno") else 0

	def isatty(self) -> bool:
		""" Return True if the first file is a terminal/console. """
		return hasattr(self.targets[0].file, "isatty") and self.targets[0].file.isatty()

