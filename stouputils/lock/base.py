
# Imports
from __future__ import annotations

import errno
import time
from contextlib import AbstractContextManager
from typing import IO, Any

from .shared import LockError, LockTimeoutError, resolve_path


class LockFifo(AbstractContextManager["LockFifo"]):
    """ A simple cross-platform inter-process lock backed by a file.

    This implementation supports optional Fifo ordering via a small ticket queue
    stored alongside the lock file. Fifo is enabled by default to avoid
    starvation. Fifo behaviour is implemented with a small sequence file and
    per-ticket files in ``<lockpath>.queue/``. On platforms without fcntl the
    implementation falls back to a timestamp-based ticket.

    Args:
        name               (str):           Lock filename or path. If a simple name is given,
            it is created in the system temporary directory.
        timeout            (float | None):  Seconds to wait for the lock. ``None`` means block indefinitely.
        blocking           (bool):          Whether to block until acquired (subject to ``timeout``).
        check_interval     (float):         Interval between lock attempts, in seconds.
        fifo               (bool):          Whether to enforce Fifo ordering (default: True).
        fifo_stale_timeout (float | None):  Seconds after which a ticket is considered stale; if ``None`` the lock's ``timeout`` value will be used.

    Raises:
        LockTimeoutError: If the lock could not be acquired within the timeout (LockError & TimeoutError subclass)
        LockError: On unexpected locking errors. (RunTimeError subclass)

    Examples:
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
        >>> def _worker(lp, op, idx):
        ...     from stouputils.lock import LockFifo
        ...     with LockFifo(lp, timeout=2):
        ...         with open(op, "a") as f:
        ...             f.write(f"{idx}\\n")
        ...         time.sleep(0.01)
        >>> procs = []
        >>> for i in range(3):
        ...     p = multiprocessing.Process(target=_worker, args=(lockpath, out, i))
        ...     p.start(); procs.append(p); time.sleep(0.05)
        >>> for p in procs: p.join(1)
        >>> with open(out) as f: print([int(x) for x in f.read().splitlines()])
        [0, 1, 2]

        >>> # Doctest: cleanup of artifacts on close
        >>> import tempfile, os
        >>> tmp = tempfile.mkdtemp()
        >>> p = tmp + "/tlock"
        >>> l = LockFifo(p, timeout=1)
        >>> l.acquire(); l.release(); l.close()
        >>> os.path.exists(p)
        False
        >>> os.path.exists(p + ".queue")
        False

        >>> # Non-Fifo fast-path should not create a queue directory
        >>> tmp2 = tempfile.mkdtemp()
        >>> p2 = tmp2 + "/tlock2"
        >>> l2 = LockFifo(p2, fifo=False, timeout=1)
        >>> l2.acquire(); l2.release(); l2.close()
        >>> os.path.exists(p2 + ".queue")
        False

        >>> # Attempting a non-blocking acquire while another process holds the lock raises LockTimeoutError
        >>> import multiprocessing, time
        >>> def _hold(path):
        ...     from stouputils.lock import LockFifo
        ...     with LockFifo(path, timeout=2):
        ...         time.sleep(1)
        >>> p = multiprocessing.Process(target=_hold, args=(p2,))
        >>> p.start(); time.sleep(0.05)
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

        # Fifo queue configuration
        self.fifo: bool = fifo
        """ Whether Fifo ordering is enabled (default True). """
        self.fifo_stale_timeout: float | None = fifo_stale_timeout
        """ Seconds to consider a ticket stale and eligible for cleanup. If ``None``,
        the lock's ``timeout`` value will be used; if that is also ``None``, no
        stale cleanup will be performed. """
        self.queue_dir: str = f"{self.path}.queue"
        """ Directory used to store queue metadata and ticket files. """
        try:
            # Ensure queue directory exists early to avoid races on first get_ticket
            if self.fifo:
                import os as _os
                _os.makedirs(self.queue_dir, exist_ok=True)
                # Create a ticket queue backend instance
                from .queue import FileTicketQueue
                self.queue = FileTicketQueue(self.queue_dir, stale_timeout=self.fifo_stale_timeout if self.fifo_stale_timeout is not None else self.timeout)
            else:
                self.queue = None
        except Exception:
            # Swallow errors; queue is optional
            self.queue = None

    def _get_ticket(self) -> int:
        """ Obtain a monotonically increasing ticket number.

        Uses a small sequence file protected by an exclusive lock (fcntl) when
        available. When fcntl is not available, falls back to a timestamp-based
        ticket (still monotonic enough on typical systems).
        """
        import os
        import uuid
        # Sequence file path
        seq_path: str = os.path.join(self.queue_dir, "seq")
        try:
            # Prefer fcntl-based atomic increment on POSIX
            import fcntl
            # Ensure queue dir exists
            os.makedirs(self.queue_dir, exist_ok=True)
            with open(seq_path, "a+b") as f:
                # Acquire exclusive lock while reading/updating sequence
                fcntl.flock(f, fcntl.LOCK_EX)
                f.seek(0)
                data: str = f.read().decode().strip()
                seq: int = int(data) if data else 0
                seq += 1
                f.seek(0)
                f.truncate(0)
                f.write(str(seq).encode())
                f.flush()
                fcntl.flock(f, fcntl.LOCK_UN)
            return seq
        except Exception:
            # Fallback: timestamp + random suffix to reduce collisions
            return int(time.time() * 1e6) * 1000000 + int(uuid.uuid4().hex[:6], 16)

    def _cleanup_stale_tickets(self) -> None:
        """ Remove stale ticket files from the queue directory.

        A ticket is considered stale when its mtime is older than the effective
        stale timeout. If ``self.fifo_stale_timeout`` is ``None``, the lock's
        ``timeout`` value is used; if that is also ``None``, no cleanup is
        performed.
        """
        if not self.fifo:
            return
        # Determine effective stale timeout (seconds)
        stale: float | None = self.fifo_stale_timeout if self.fifo_stale_timeout is not None else self.timeout
        if stale is None:
            return
        try:
            import os
            files: list[str] = sorted(os.listdir(self.queue_dir))
            if not files:
                return
            head: str = files[0]
            p: str = os.path.join(self.queue_dir, head)
            try:
                mtime: float = os.path.getmtime(p)
            except FileNotFoundError:
                return
            # Use wall-clock epoch time to compare with mtime
            age: float = time.time() - mtime
            if age >= stale:
                try:
                    os.remove(p)
                except Exception:
                    pass
        except Exception:
            pass

    def perform_lock(self, blocking: bool, timeout: float | None, check_interval: float) -> None:
        """ Core platform-specific lock acquisition. This contains the original
        flock-based implementation and is used both by Fifo and non-Fifo
        paths.
        """
        deadline: float | None = None if timeout is None else (time.monotonic() + timeout)

        # Open file if not already opened
        if self.fd is None:
            self.file = open(self.path, "a+b")
            self.fd = self.file.fileno()

        # Define platform-specific locking functions
        def lock_linux() -> None:
            import fcntl
            flags: int = fcntl.LOCK_EX
            if not blocking or timeout is not None:
                flags |= fcntl.LOCK_NB
            fcntl.flock(self.fd, flags) # type: ignore

        def lock_windows() -> None:
            import msvcrt
            mode = msvcrt.LK_NBLCK if not blocking or timeout is not None else msvcrt.LK_LOCK # type: ignore
            msvcrt.locking(self.fd, mode, 1)  # type: ignore

        # Main loop
        while True:
            blocked: bool = False
            for lock_func in (lock_linux, lock_windows):
                try:
                    lock_func()
                    self.is_locked = True
                    return
                except (ImportError, ModuleNotFoundError):
                    continue
                except BlockingIOError:
                    blocked = True  # Lock is already held
                    break
                except OSError as exc:
                    # Translate common busy errors to retry
                    if getattr(exc, "errno", None) in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
                        blocked = True
                        break
                    else:
                        raise LockError(str(exc)) from exc
            if not blocked:
                raise LockError("Could not acquire lock: unsupported platform")

            # If we reach here, lock was busy
            if not blocking:
                raise LockTimeoutError("Lock is already held and blocking is False")
            if deadline is not None and time.monotonic() >= deadline:
                raise LockTimeoutError(f"Timeout while waiting for lock '{self.path}'")
            time.sleep(check_interval)

    def acquire(self, timeout: float | None = None, blocking: bool | None = None, check_interval: float | None = None) -> None:
        """ Acquire the lock, optionally using Fifo ordering.

        When Fifo is enabled (default), a ticket file is created and the caller
        waits until its ticket becomes head of the queue before attempting the
        actual underlying lock. This avoids starvation by ensuring waiters are
        served in arrival order.
        """
        # Use instance defaults if parameters not provided
        if blocking is None:
            blocking = self.blocking
        if timeout is None:
            timeout = self.timeout
        if check_interval is None:
            check_interval = self.check_interval
        deadline: float | None = None if timeout is None else (time.monotonic() + timeout)

        if not self.fifo or self.queue is None:
            # Fast path: original behaviour
            return self.perform_lock(blocking, timeout, check_interval)

        # Fifo path using queue backend
        ticket, member = self.queue.register()

        try:
            while True:
                # Cleanup stale head ticket if needed
                self.queue.cleanup_stale()
                if not self.queue.is_head(ticket):
                    if not blocking:
                        raise LockTimeoutError("Lock is already held and blocking is False")
                    if deadline is not None and time.monotonic() >= deadline:
                        raise LockTimeoutError(f"Timeout while waiting for lock '{self.path}'")
                    time.sleep(check_interval)
                    continue
                # We're head of the queue; attempt to acquire underlying lock
                self.perform_lock(blocking, timeout, check_interval)
                # We obtained OS lock; remove ticket file (we hold the lock now)
                try:
                    self.queue.remove(member)
                except Exception:
                    pass
                return
        finally:
            # Ensure our ticket is removed if we timed out or an unexpected error occurred
            try:
                self.queue.remove(member)
            except Exception:
                pass

    def release(self) -> None:
        """ Release the lock. """
        if not self.is_locked:
            return
        def unlock_linux() -> None:
            import fcntl
            if self.fd is not None:
                fcntl.flock(self.fd, fcntl.LOCK_UN)
        def unlock_windows() -> None:
            import msvcrt
            if self.fd is not None:
                msvcrt.locking(self.fd, msvcrt.LK_UNLCK, 1) # type: ignore
        for unlock_func in (unlock_linux, unlock_windows):
            try:
                unlock_func()
                break
            except Exception:
                pass

        # Ensure internal state is updated even if unlocking failed
        self.is_locked = False
        # Perform some cleanup of stale tickets
        try:
            self._cleanup_stale_tickets()
        except Exception:
            pass
        # Keep file open for potential re-acquire; do not remove file

    def __enter__(self) -> LockFifo:
        self.acquire()
        return self

    def __exit__(self, exc_type: type | None, exc: BaseException | None, tb: Any | None) -> None:
        self.release()

    def close(self) -> None:
        """ Release and close underlying file descriptor.

        Also attempts best-effort cleanup of queue artifacts and the lock file
        itself when it is safe to do so (no waiting clients and the lock is not
        held). This avoids leaving behind ``<lock>.queue/`` and ``<lock>``
        files when they are no longer in use.
        """
        try:
            self.release()
        except Exception:
            pass
        finally:
            if self.file is not None:
                try:
                    self.file.close()
                except Exception:
                    pass
                self.file = None
                self.fd = None

        # Best-effort cleanup of queue artifacts
        try:
            if self.fifo and hasattr(self, "queue") and self.queue is not None:
                try:
                    self.queue.cleanup_stale()
                except Exception:
                    pass
                try:
                    self.queue.maybe_cleanup()
                except Exception:
                    pass
        except Exception:
            pass

        # Try to remove the lock file itself when it is safe to do so. This
        # uses a non-blocking fcntl test lock on POSIX: if we can acquire the
        # lock, nobody else is holding it and we may remove the file. If the
        # platform does not support fcntl we skip this step to avoid races.
        try:
            if not self.is_locked:
                import os
                try:
                    import fcntl
                except Exception:
                    fcntl = None
                if fcntl is not None:
                    try:
                        fd = os.open(self.path, os.O_RDONLY)
                    except FileNotFoundError:
                        fd = None
                    if fd is not None:
                        try:
                            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                            try:
                                os.close(fd)
                            except Exception:
                                pass
                            try:
                                os.remove(self.path)
                            except Exception:
                                pass
                        except (BlockingIOError, OSError):
                            try:
                                os.close(fd)
                            except Exception:
                                pass
                        except Exception:
                            try:
                                os.close(fd)
                            except Exception:
                                pass
        except Exception:
            pass

    def __del__(self) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"<LockFifo path={self.path!r} locked={self.is_locked}>"

