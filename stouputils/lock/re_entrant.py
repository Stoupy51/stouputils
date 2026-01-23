
# Imports
import os
from typing import ClassVar

from .base import LockFifo


class RLockFifo(LockFifo):
    """ A re-entrant cross-process lock backed by a file.

    This lock is re-entrant for the same owner, where owner identity is the
    tuple ``(path, pid, thread_id)``. Repeated calls to :meth:`acquire` by the
    same owner increment an internal counter; only the final :meth:`release`
    will release the underlying file lock managed by :class:`LockFifo`.

    Key behaviour:
      - Owner identity: (path, pid, thread_id)
      - Reentrancy applies only within the same thread of the same process.
        Other threads or processes will block (or raise ``LockTimeoutError``)
        according to the lock's timeout and blocking parameters.
      - Implemented on top of :class:`LockFifo` and shares its constructor
        parameters and error semantics.

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
        >>> with RLockFifo("my.lock", timeout=5):
        ...     # critical section
        ...     pass

        >>> lock = RLockFifo("my.lock")
        >>> lock.acquire()
        >>> lock.acquire()  # re-entrant acquire by same thread/process
        >>> lock.release()
        >>> lock.release()  # underlying lock released here

        >>> # Reentrancy with Fifo enabled should not create multiple tickets
        >>> lock = RLockFifo("my_r.lock", fifo=True, timeout=1)
        >>> lock.acquire()
        >>> lock.acquire()
        >>> lock.release()
        >>> lock.release()

        >>> # Cleanup behaviour: after closing a re-entrant lock the queue should be removed when empty
        >>> import tempfile, os
        >>> tmp = tempfile.mkdtemp()
        >>> p = tmp + "/rlock"
        >>> r = RLockFifo(p, fifo=True, timeout=1)
        >>> r.acquire(); r.acquire(); r.release(); r.release(); r.close()
        >>> os.path.exists(p + ".queue")
        False
    """
    owners: ClassVar[dict[tuple[str, int, int], int]] = {}
    """ Mapping of owner keys to re-entrant acquisition counts. """

    def __init__(
        self,
        name: str,
        timeout: float | None = None,
        blocking: bool = True,
        check_interval: float = 0.05,
        fifo: bool = True,
        fifo_stale_timeout: float | None = None
    ) -> None:
        """ Initialize the re-entrant lock and compute owner key.

        The attribute ``self.key`` is a tuple ``(path, pid, thread_id)`` used to
        track ownership and re-entrant acquisition counts in the
        :class:`owners` mapping.
        """
        super().__init__(name, timeout=timeout, blocking=blocking, check_interval=check_interval, fifo=fifo, fifo_stale_timeout=fifo_stale_timeout)
        self.key: tuple[str, int, int] = (self.path, os.getpid(), __import__("threading").get_ident())

    def acquire(self, timeout: float | None = None, blocking: bool | None = None, check_interval: float | None = None) -> None:
        """ Acquire the lock with re-entrancy for the same owner.

        If the current owner (same ``self.key``) already holds the lock, the
        internal counter is incremented and the underlying file lock is not
        re-acquired. Otherwise this delegates to :meth:`LockFifo.acquire`.
        """
        cnt: int = self.owners.get(self.key, 0)
        if cnt > 0:
            self.owners[self.key] = cnt + 1
            return
        super().acquire(timeout=timeout, blocking=blocking, check_interval=check_interval)
        self.owners[self.key] = 1

    def release(self) -> None:
        """ Release the lock for this owner.

        Decrements the re-entrant counter for the current owner and only when
        the counter reaches zero the underlying :class:`LockFifo` is released.
        """
        cnt: int = self.owners.get(self.key, 0)
        if cnt <= 1:
            # last release: release underlying lock
            try:
                super().release()
            finally:
                self.owners.pop(self.key, None)
        else:
            self.owners[self.key] = cnt - 1

