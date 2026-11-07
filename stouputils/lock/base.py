
# Imports
from __future__ import annotations

# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

import errno
import os
import sys
import time
from contextlib import AbstractContextManager, suppress
from typing import IO, Any

from .shared import LockError, resolve_acquire_defaults, resolve_path, wait_or_raise

if sys.platform == "win32":
	import msvcrt
else:
	import fcntl


def _lock_fd(fd: int, blocking: bool, timeout: float | None) -> None:
	""" Take an exclusive lock on an open file descriptor, waiting for it only when ``blocking`` without a ``timeout``.

	Raises:
		BlockingIOError: If another process holds the lock.
		OSError:         On any other locking failure.
	"""
	wait: bool = blocking and timeout is None
	try:
		if sys.platform == "win32":
			msvcrt.locking(fd, msvcrt.LK_LOCK if wait else msvcrt.LK_NBLCK, 1)
		else:
			fcntl.flock(fd, fcntl.LOCK_EX if wait else fcntl.LOCK_EX | fcntl.LOCK_NB)
	except OSError as exc:
		if exc.errno in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
			raise BlockingIOError from exc
		raise


def _unlock_fd(fd: int) -> None:
	if sys.platform == "win32":
		msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
	else:
		fcntl.flock(fd, fcntl.LOCK_UN)


def _remove_file_if_unlocked(path: str) -> None:
	""" Remove a lock file unless another process holds it, never raising. """
	try:
		fd: int = os.open(path, os.O_RDONLY)
	except OSError:
		return
	try:
		_lock_fd(fd, blocking=False, timeout=None)
	except OSError:
		os.close(fd)
		return
	os.close(fd)
	with suppress(OSError):
		os.remove(path)


def _worker(lp: str, op: str, idx: int, start_delay: float = 0.0) -> None: # pyright: ignore[reportUnusedFunction]
	""" Module-level helper used by doctests as a multiprocessing target.

	``start_delay`` allows deterministic arrival ordering in multiprocessing
	doctests where OS process scheduling can otherwise reorder contenders.
	"""
	from stouputils.lock import LockFifo
	if start_delay > 0:
		time.sleep(start_delay)
	with LockFifo(lp, timeout=2):
		with open(op, "a") as f:
			f.write(f"{idx}\n")
		time.sleep(0.01)


def _hold(path: str) -> None: # pyright: ignore[reportUnusedFunction]
	""" Module-level helper used by doctests as a multiprocessing target.

	This creates a small readiness marker file while holding the lock so
	doctests can reliably detect when the child process has acquired it
	(useful on Windows spawn semantics).
	"""
	from stouputils.lock import LockFifo
	ready = f"{path}.held"
	try:
		with LockFifo(path, timeout=2):
			with open(ready, "w") as f:
				f.write("1")
			time.sleep(1)
	finally:
		with suppress(Exception):
			os.remove(ready)


class LockFifo(AbstractContextManager["LockFifo"]):
	""" A simple cross-platform inter-process lock backed by a file.

	This implementation supports optional Fifo ordering via a small ticket queue
	stored alongside the lock file. Fifo is enabled by default to avoid starvation.
	Fifo behaviour is implemented with a small sequence file and
	per-ticket files in ``<lockpath>.queue/``.

	Args:
		name:               Lock filename or path. If a simple name is given,
			it is created in the system temporary directory.
		timeout:            Seconds to wait for the lock. ``None`` means block indefinitely.
		blocking:           Whether to block until acquired (subject to ``timeout``).
		check_interval:     Interval between lock attempts, in seconds.
		fifo:               Whether to enforce Fifo ordering (default: True).
		fifo_stale_timeout: Seconds after which a ticket is considered stale; if ``None`` the lock's ``timeout`` value will be used.

	Raises:
		:py:exc:`LockTimeoutError`: If the lock could not be acquired within the timeout (LockError & TimeoutError subclass)
		:py:exc:`LockError`: On unexpected locking errors. (RunTimeError subclass)

	>>> # Basic context-manager usage (Fifo enabled by default)
	>>> with LockFifo("my.lock", timeout=1):
	...     pass

	>>> # Explicit acquire/release
	>>> lock = LockFifo("my.lock", timeout=1)
	>>> lock.acquire()
	>>> lock.release()

	>>> # Doctest: simple multi-process Fifo check (fast and deterministic)
	>>> import tempfile, multiprocessing, time
	>>> tmpdir = tempfile.mkdtemp()
	>>> lockpath = tmpdir + "/t.lock"
	>>> out = tmpdir + "/out.txt"
	>>> # Worker function is module-level: `_worker`
	>>> # (Defined at module scope so it can be pickled on Windows)
	>>> procs = []
	>>> for i in range(3):
	...     p = multiprocessing.Process(target=_worker, args=(lockpath, out, i, i * 0.05))
	...     p.start(); procs.append(p)
	>>> for p in procs: p.join(1)
	>>> with open(out) as f: print([int(x) for x in f.read().splitlines()])
	[0, 1, 2]

	>>> # Doctest: cleanup of artifacts on close
	>>> import tempfile, os
	>>> tmp = tempfile.mkdtemp()
	>>> p = tmp + "/tlock"
	>>> l = LockFifo(p, timeout=1)
	>>> l.acquire(); l.release(); l.close()
	>>> import os
	>>> # The lock file should not remain on any platform after close()
	>>> assert not os.path.exists(p)
	>>> assert not os.path.exists(p + ".queue")

	>>> # Non-Fifo fast-path should not create a queue directory
	>>> tmp2 = tempfile.mkdtemp()
	>>> p2 = tmp2 + "/tlock2"
	>>> l2 = LockFifo(p2, fifo=False, timeout=1)
	>>> l2.acquire(); l2.release(); l2.close()
	>>> os.path.exists(p2 + ".queue")
	False

	>>> # Attempting a non-blocking acquire while another process holds the lock raises LockTimeoutError
	>>> import multiprocessing, time
	>>> # Hold function is module-level: `_hold`
	>>> # (Defined at module scope so it can be pickled on Windows)
	>>> p = multiprocessing.Process(target=_hold, args=(p2,))
	>>> p.start()
	>>> import time, os
	>>> deadline = time.time() + 1.0
	>>> while not os.path.exists(p2 + ".held") and time.time() < deadline:
	...     time.sleep(0.01)
	>>> from stouputils.lock import LockTimeoutError
	>>> l3 = LockFifo(p2, timeout=1)
	>>> try:
	...     l3.acquire(blocking=False)
	... except LockTimeoutError:
	...     print("timeout")
	... finally:
	...     p.terminate(); p.join()
	timeout
	"""

	def __init__(
		self,
		name: str,
		timeout: float | None = None,
		blocking: bool = True,
		check_interval: float = 0.05,
		fifo: bool = True,
		fifo_stale_timeout: float | None = None
	) -> None:
		self.path: str = resolve_path(name)
		""" The lock file path. """
		self.timeout: float | None = timeout
		""" Maximum time to wait for the lock, in seconds. None means wait indefinitely. """
		self.blocking: bool = blocking
		""" Whether to block until the lock is acquired (subject to ``timeout``). """
		self.check_interval: float = check_interval
		""" Interval between lock acquisition attempts, in seconds. """
		self.file: IO[bytes] | None = None
		""" The underlying file object. """
		self.fd: int | None = None
		""" The underlying file descriptor. """
		self.is_locked: bool = False
		""" Whether the lock is currently held. """
		self.member: str | None = None
		""" The name of our ticket file in the queue directory when using Fifo. """

		# Fifo queue configuration
		self.fifo: bool = fifo
		""" Whether Fifo ordering is enabled (default True). """
		self.fifo_stale_timeout: float | None = fifo_stale_timeout
		""" Seconds to consider a ticket stale and eligible for cleanup. If ``None``,
		the lock's ``timeout`` value will be used; if that is also ``None``,
		no stale cleanup will be performed. """
		self.queue_dir: str = f"{self.path}.queue"
		""" Directory used to store queue metadata and ticket files. """
		try:
			# Ensure queue directory exists early to avoid races on first get_ticket
			if self.fifo:
				os.makedirs(self.queue_dir, exist_ok=True)
				# Create a ticket queue backend instance
				from .queue import FileTicketQueue
				stale_timeout = self.fifo_stale_timeout if self.fifo_stale_timeout is not None else self.timeout
				self.queue = FileTicketQueue(self.queue_dir, stale_timeout=stale_timeout)
			else:
				self.queue = None
		except Exception:
			# Swallow errors; queue is optional
			self.queue = None

	def get_ticket(self) -> int:
		""" Obtain a monotonically increasing ticket number. Delegates to the queue backend when available. """
		if self.queue is not None:
			return self.queue.get_ticket()
		# Fallback: timestamp + random suffix to reduce collisions
		import uuid
		return int(time.time() * 1e6) * 1000000 + int(uuid.uuid4().hex[:6], 16)

	def _cleanup_stale_tickets(self) -> None:
		""" Remove stale ticket files from the queue directory. Delegates to the queue backend. """
		if not self.fifo or self.queue is None:
			return
		self.queue.cleanup_stale()

	def perform_lock(self, blocking: bool, timeout: float | None, check_interval: float) -> None:
		""" Take the OS lock on the lock file, retrying until the deadline. Used by both Fifo and non-Fifo paths. """
		deadline: float | None = None if timeout is None else (time.monotonic() + timeout)

		# Open file if not already opened
		if self.fd is None:
			self.file = open(self.path, "a+b")  # noqa: SIM115
			self.fd = self.file.fileno()

		while True:
			try:
				_lock_fd(self.fd, blocking, timeout)
				self.is_locked = True
				return
			except BlockingIOError:
				pass
			except OSError as exc:
				raise LockError(str(exc)) from exc
			wait_or_raise(blocking, deadline, check_interval, self.path)

	def acquire(self, timeout: float | None = None, blocking: bool | None = None, check_interval: float | None = None) -> None:
		""" Acquire the lock, optionally using Fifo ordering.

		When Fifo is enabled (default), a ticket file is created and the caller
		waits until its ticket becomes head of the queue before attempting the actual underlying lock.
		This avoids starvation by ensuring waiters are
		served in arrival order.
		"""
		# Use instance defaults if parameters not provided
		blocking, timeout, check_interval, deadline = resolve_acquire_defaults(
			blocking, timeout, check_interval, self.blocking, self.timeout, self.check_interval
		)

		if not self.fifo or self.queue is None:
			# Fast path: original behaviour
			return self.perform_lock(blocking, timeout, check_interval)

		# Fifo path using queue backend
		ticket, member = self.queue.register()
		self.member = member

		try:
			while True:
				self.queue.cleanup_stale()
				if self.queue.is_head(ticket):
					# The ticket stays in the queue until release, which is what keeps the lock exclusive
					return self.perform_lock(blocking, timeout, check_interval)
				wait_or_raise(blocking, deadline, check_interval, self.path)
		finally:
			# Ensure our ticket is removed if we timed out or an unexpected error occurred
			with suppress(Exception):
				if not self.is_locked:
					self.queue.remove(self.member)
					self.member = None

	def release(self) -> None:
		""" Release the lock. """
		if not self.is_locked:
			return
		with suppress(OSError):
			if self.fd is not None:
				_unlock_fd(self.fd)

		# Ensure internal state is updated even if unlocking failed
		self.is_locked = False
		# Perform some cleanup of stale tickets
		with suppress(Exception):
			self._cleanup_stale_tickets()
		# Remove our ticket file now that we're fully released (if using Fifo)
		with suppress(Exception):
			if self.fifo and self.queue is not None and self.member is not None:
				try:
					self.queue.remove(self.member)
				finally:
					self.member = None
		# Keep file open for potential re-acquire; do not remove file

	def __enter__(self) -> LockFifo:
		self.acquire()
		return self

	def __exit__(self, exc_type: type | None, exc: BaseException | None, tb: Any | None) -> None:
		self.release()

	def close(self) -> None:
		""" Release and close underlying file descriptor.

		Also attempts best-effort cleanup of queue artifacts and the lock file
		itself when it is safe to do so (no waiting clients and the lock is not held).
		This avoids leaving behind ``<lock>.queue/`` and ``<lock>``
		files when they are no longer in use.
		"""
		with suppress(Exception):
			self.release()
		if self.file is not None:
			with suppress(Exception):
				self.file.close()
			self.file = None
			self.fd = None

		# Best-effort cleanup of queue artifacts
		with suppress(Exception):
			if self.fifo and self.queue is not None:
				with suppress(Exception):
					self.queue.cleanup_stale()
				with suppress(Exception):
					self.queue.maybe_cleanup()

		# Try to remove the lock file itself when it is safe to do so. Best-effort.
		with suppress(Exception):
			if not self.is_locked:
				_remove_file_if_unlocked(self.path)

	def __del__(self) -> None:
		self.close()

	def __repr__(self) -> str:
		return f"<LockFifo path={self.path!r} locked={self.is_locked}>"

