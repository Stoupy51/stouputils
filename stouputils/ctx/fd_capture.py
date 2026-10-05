""" Copying into a log what reaches the stdout and stderr file descriptors without going through ``sys.stdout``.

C extensions, ``os.system`` and child processes that do not capture their output write straight to the descriptors,
so replacing ``sys.stdout`` never sees them. FdCapture points the descriptors at a pseudo-terminal, or a pipe when the
output is not a terminal, and a thread copies what arrives both to the real terminal and into the log.
"""

# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import codecs
import os
import sys
import threading
from contextlib import suppress
from dataclasses import dataclass, field
from typing import IO, Any

from ..print.output_stream import TeeMultiOutput, TeeTarget

# Constants
READ_SIZE: int = 65536
""" Bytes read from a descriptor at once. """


# Classes
@dataclass
class FdChannel:
	""" One redirected descriptor: where it pointed before, and the end the reader thread reads it from. """
	fd: int
	""" Descriptor redirected, 1 for stdout or 2 for stderr. """
	saved: int
	""" Copy of what the descriptor pointed to before, the real terminal. """
	reader: int
	""" Read end of the pseudo-terminal or pipe the descriptor now points to. """
	target: TeeTarget
	""" Log output receiving the text, with a line state of its own so stdout and stderr lines never merge. """
	decoder: codecs.IncrementalDecoder = field(default_factory=lambda: codecs.getincrementaldecoder("utf-8")(errors="replace"))


class FdCapture:
	""" Copy everything written to the stdout and stderr descriptors into a log file, the terminal still showing it.

	Python's own output reaches the descriptors too, so the log receives every line in the order it was written.
	The reader thread never stops on an error, since a full pipe would block every later write of the program.

	Args:
		file:          Log file receiving the text.
		strip_colors:  Whether the log receives the text without ANSI colors.
		ignore_lineup: Whether the log receives what a terminal ends up showing, see :class:`~stouputils.print.LineState`.
	"""
	def __init__(self, file: IO[Any], strip_colors: bool, ignore_lineup: bool) -> None:
		self.file: IO[Any] = file
		self.strip_colors: bool = strip_colors
		self.ignore_lineup: bool = ignore_lineup
		self.channels: list[FdChannel] = []
		""" The two redirected descriptors, empty while not capturing """
		self.thread: threading.Thread | None = None
		""" Thread copying what the descriptors receive """

	@staticmethod
	def unsupported_reason() -> str | None:
		""" Why the descriptors cannot be captured here, None when they can. """
		if os.name == "nt":
			return "Windows has no pseudo-terminal to keep the console behaving as one"
		if "ipykernel" in sys.modules:
			return "Jupyter already forwards the descriptors to the notebook"
		if threading.current_thread() is not threading.main_thread():
			return "the descriptors belong to the whole process, which only the main thread speaks for"
		with suppress(Exception):
			stream: Any = sys.stdout.files[0] if isinstance(sys.stdout, TeeMultiOutput) else sys.stdout
			if stream.fileno() == 1:
				return None
		return "Python's stdout does not write to descriptor 1"

	def start(self) -> None:
		""" Point stdout and stderr at the reader thread. """
		flush_all()
		self.channels = [self.redirect(fd) for fd in (1, 2)]
		self.thread = threading.Thread(target=self.copy_forever, name="stouputils-fd-capture", daemon=True)
		self.thread.start()

	def stop(self) -> None:
		""" Give the descriptors back, then let the reader thread copy what is left before it ends. """
		flush_all()
		for channel in self.channels:
			os.dup2(channel.saved, channel.fd)
		if self.thread is not None:
			self.thread.join(timeout=2.0)
		for channel in self.channels:
			channel.target.write(channel.decoder.decode(b"", final=True))
			channel.target.finish()
			for fd in (channel.reader, channel.saved):
				with suppress(OSError):
					os.close(fd)
		self.channels, self.thread = [], None

	def redirect(self, fd: int) -> FdChannel:
		""" Point a descriptor at a new pseudo-terminal, or pipe when it is not a terminal, keeping a copy of the old one. """
		saved: int = os.dup(fd)
		if os.isatty(fd):
			import pty
			reader, writer = pty.openpty()
			copy_terminal_settings(saved, writer)
		else:
			reader, writer = os.pipe()
		os.dup2(writer, fd)
		os.close(writer)
		target = TeeTarget(self.file, strip_colors=self.strip_colors, ignore_lineup=self.ignore_lineup)
		return FdChannel(fd=fd, saved=saved, reader=reader, target=target)

	def copy_forever(self) -> None:
		""" Copy what each descriptor receives until every writer is gone. """
		import selectors
		with selectors.DefaultSelector() as selector:
			for channel in self.channels:
				selector.register(channel.reader, selectors.EVENT_READ, channel)
			while selector.get_map():
				for key, _ in selector.select():
					channel: FdChannel = key.data
					if not self.copy_once(channel):
						selector.unregister(channel.reader)

	def copy_once(self, channel: FdChannel) -> bool:
		""" Copy one read of a descriptor to the terminal and the log.

		Returns:
			False once nothing writes to the descriptor any more.
		"""
		try:
			data: bytes = os.read(channel.reader, READ_SIZE)
		except OSError:
			return False
		if not data:
			return False
		with suppress(Exception):
			write_all(channel.saved, data)
		with suppress(Exception):
			channel.target.write(channel.decoder.decode(data))
			channel.target.flush()
		return True


# Functions
def flush_all() -> None:
	""" Flush Python's streams and the C library's, so what they hold goes through the descriptors now. """
	for stream in (sys.stdout, sys.stderr):
		with suppress(Exception):
			stream.flush()
	with suppress(Exception):
		import ctypes
		ctypes.CDLL(None).fflush(None)


def copy_terminal_settings(terminal: int, pseudo_terminal: int) -> None:
	""" Give a pseudo-terminal the size of the real one, and stop it turning newlines into ``\\r\\n``. """
	import fcntl
	import termios
	with suppress(OSError):
		fcntl.ioctl(pseudo_terminal, termios.TIOCSWINSZ, fcntl.ioctl(terminal, termios.TIOCGWINSZ, b"\0" * 8))
	with suppress(termios.error):
		attributes = termios.tcgetattr(pseudo_terminal)
		attributes[1] &= ~termios.OPOST
		termios.tcsetattr(pseudo_terminal, termios.TCSANOW, attributes)


def write_all(fd: int, data: bytes) -> None:
	""" Write every byte to a descriptor, which a single os.write does not promise. """
	view: memoryview = memoryview(data)
	while view:
		view = view[os.write(fd, view):]

