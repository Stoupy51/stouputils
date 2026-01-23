
# Imports
from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable
from contextlib import AbstractContextManager
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import redis

from .shared import LockError, LockTimeoutError


class SimpleRedisLock(AbstractContextManager["SimpleRedisLock"]):
    """ A Redis-backed inter-process lock (requires `redis`).

    This lock provides optional FIFO fairness (enabled by default) and is
    implemented using atomic Redis primitives. Acquisition of the underlying
    lock uses an owner token and `SET NX` (with optional PX expiry when a
    timeout/TTL is specified). When FIFO is enabled the implementation uses
    a small ticket queue using `INCR` + `ZADD` and only the queue head attempts
    to `SET NX`. Release uses an atomic Lua script to ensure only the token
    owner can delete the lock key.

    Notes:
      - The lock stores a locally-generated random token; releasing without the
        correct token has no effect on the remote key.
      - When FIFO is enabled, queue entries are removed when the client acquires
        the lock; stale queue entries (from crashed clients) are removed lazily
        when their age exceeds ``fifo_stale_timeout`` (defaults to ``timeout`` if
        ``None``).
      - This class raises ``ImportError`` if the ``redis`` package is not
        installed and raises ``LockTimeoutError`` / ``LockError`` for runtime
        acquisition errors.

    Args:
        name               (str):           Redis key name used for the lock.
        redis_client       (redis.Redis | None): Optional Redis client. A client is created lazily if not provided.
        timeout            (float | None):  Maximum time to wait for the lock and (when provided) the lock TTL used by ``SET PX`` in seconds. ``None`` means block indefinitely and no automatic expiry.
        blocking           (bool):          Whether to block until acquired (subject to ``timeout``).
        check_interval     (float):         Poll interval while waiting for the lock, in seconds.
        fifo               (bool):          Whether to enforce FIFO ordering using a ZSET queue (default: True).
        fifo_stale_timeout (float | None):  Seconds after which a queue entry is considered stale; if ``None`` the lock's ``timeout`` value will be used; if both are ``None``, no stale cleanup is performed.

    Raises:
        ImportError: If the ``redis`` package is not installed.
        LockTimeoutError: If the lock cannot be acquired within ``timeout``.
        LockError: On unexpected redis errors.

    Examples:
        >>> # Safe usage example that will not fail doctest when redis isn't installed
        >>> try:
        ...     with SimpleRedisLock('test:lock', timeout=1):
        ...         pass
        ... except ImportError:
        ...     pass

        >>> # Non-FIFO usage example
        >>> try:
        ...     with SimpleRedisLock('test:lock', fifo=False, timeout=1):
        ...         pass
        ... except ImportError:
        ...     pass
    """  # noqa: E501

    RELEASE_SCRIPT: str = """
    if redis.call('get', KEYS[1]) == ARGV[1] then
        return redis.call('del', KEYS[1])
    else
        return 0
    end
    """

    def __init__(
        self,
        name: str,
        redis_client: redis.Redis | None = None,
        timeout: float | None = None,
        blocking: bool = True,
        check_interval: float = 0.05,
        fifo: bool = True,
        fifo_stale_timeout: float | None = None
    ) -> None:
        try:
            import redis  # type: ignore  # noqa: F401
        except (ImportError, ModuleNotFoundError) as e:
            raise ImportError("`redis` package is not installed; Please install it to use SimpleRedisLock.") from e
        self.name: str = name
        self.client: redis.Redis | None = redis_client
        self.timeout: float | None = timeout
        self.blocking: bool = blocking
        self.check_interval: float = check_interval
        self.fifo: bool = fifo
        self.fifo_stale_timeout: float | None = fifo_stale_timeout
        self.token: str | None = None
        self._queue_member: str | None = None

    def ensure_client(self) -> redis.Redis:
        """ Ensure a ``redis.Redis`` client is available (lazy creation). """
        if self.client is None:
            import redis
            self.client = redis.Redis()
        return self.client

    def _cleanup_stale_queue(self) -> None:
        """ Remove a stale head member from the queue if it exceeds the stale timeout. """
        if not self.fifo:
            return
        # Determine effective stale timeout (seconds)
        stale: float | None = self.fifo_stale_timeout if self.fifo_stale_timeout is not None else self.timeout
        if stale is None:
            return
        client: redis.Redis = self.ensure_client()
        try:
            head: Awaitable[Any] | Any = client.zrange(f"{self.name}:queue", 0, 0) # type: ignore
            if not head:
                return
            head_member = str(head[0].decode()) # type: ignore
            # member format: ticket:token:ts_ms
            parts: list[str] = head_member.split(":")
            if len(parts) < 3:
                return
            ts_ms: int = int(parts[2])
            age: float = (time.monotonic() * 1000) - ts_ms
            if age >= (stale * 1000):
                try:
                    client.zrem(f"{self.name}:queue", head_member)
                except Exception:
                    pass
        except Exception:
            pass

    def acquire(self, timeout: float | None = None, blocking: bool | None = None, check_interval: float | None = None) -> None:
        """ Acquire the Redis lock.

        When FIFO is enabled (default), this function obtains a ticket via INCR
        and registers it in a ZSET. The client waits until its ticket is the
        head of the queue and then attempts to SET NX the lock key.
        """
        # Use instance defaults if parameters not provided
        if blocking is None:
            blocking = self.blocking
        if timeout is None:
            timeout = self.timeout
        if check_interval is None:
            check_interval = self.check_interval
        deadline: float | None = None if timeout is None else (time.monotonic() + timeout)
        self.client = self.ensure_client()
        token: str = uuid.uuid4().hex

        # Non-FIFO fast path
        if not self.fifo:
            while True:
                px: int | None = None if timeout is None else int((timeout or 0) * 1000)
                try:
                    ok: Any = self.client.set(self.name, token, nx=True, px=px)
                except Exception as exc:
                    raise LockError(str(exc)) from exc
                if ok:
                    self.token = token
                    return
                if not blocking:
                    raise LockTimeoutError("Lock is already held and blocking is False")
                if deadline is not None and time.monotonic() >= deadline:
                    raise LockTimeoutError(f"Timeout while waiting for redis lock '{self.name}'")
                time.sleep(check_interval)

        # FIFO path
        try:
            # Register ticket
            ticket = int(self.client.incr(f"{self.name}:seq")) # type: ignore
            ts_ms = int(time.monotonic() * 1000)
            member: str = f"{ticket}:{token}:{ts_ms}"
            self.client.zadd(f"{self.name}:queue", {member: ticket})
            self._queue_member = member

            while True:
                # Cleanup stale head if necessary
                self._cleanup_stale_queue()
                head: Awaitable[Any] | Any = self.client.zrange(f"{self.name}:queue", 0, 0) # type: ignore
                if not head:
                    # no head yet; wait
                    if not blocking:
                        raise LockTimeoutError("Lock is already held and blocking is False")
                    if deadline is not None and time.monotonic() >= deadline:
                        raise LockTimeoutError(f"Timeout while waiting for redis lock '{self.name}'")
                    time.sleep(check_interval)
                    continue
                head_member = head[0].decode()
                head_ticket = int(head_member.split(":")[0])
                if head_ticket != ticket:
                    if not blocking:
                        raise LockTimeoutError("Lock is already held and blocking is False")
                    if deadline is not None and time.monotonic() >= deadline:
                        raise LockTimeoutError(f"Timeout while waiting for redis lock '{self.name}'")
                    time.sleep(check_interval)
                    continue
                # We're head; attempt to SET NX
                px = None if timeout is None else int((timeout or 0) * 1000)
                try:
                    ok: Any = self.client.set(self.name, token, nx=True, px=px)
                except Exception as exc:
                    raise LockError(str(exc)) from exc
                if ok:
                    self.token = token
                    try:
                        # Remove our queue entry; we hold the lock now
                        self.client.zrem(f"{self.name}:queue", member)
                        self._queue_member = None
                    except Exception:
                        pass
                    return
                # Someone else took the lock despite us being head; wait and retry
                if not blocking:
                    raise LockTimeoutError("Lock is already held and blocking is False")
                if deadline is not None and time.monotonic() >= deadline:
                    raise LockTimeoutError(f"Timeout while waiting for redis lock '{self.name}'")
                time.sleep(check_interval)
        except Exception:
            # On error, ensure we remove our queue entry if present
            try:
                if self._queue_member is not None:
                    self.client.zrem(f"{self.name}:queue", self._queue_member)
                    self._queue_member = None
            except Exception:
                pass
            raise


    def release(self) -> None:
        """ Release the lock if currently owned by this instance.

        Uses an atomic Lua script to check that the stored token matches the
        key value and deletes it only when owned. Additionally removes any
        lingering queue entry for this client.
        """
        if not self.token:
            return
        self.client = self.ensure_client()

        try:
            # Use eval to run atomic check-and-del
            self.client.eval(self.RELEASE_SCRIPT, 1, self.name, self.token)
        finally:
            # Ensure local state cleared and remove any queue entry we may have left
            try:
                if self._queue_member is not None:
                    self.client.zrem(f"{self.name}:queue", self._queue_member)
            except Exception:
                pass
            self._queue_member = None
            self.token = None

    def __enter__(self) -> SimpleRedisLock:
        self.acquire()
        return self

    def __exit__(self, exc_type: type | None, exc: BaseException | None, tb: Any | None) -> None:
        self.release()

