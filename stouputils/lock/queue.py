
# Imports
from __future__ import annotations

import os
import time
import uuid
from typing import TYPE_CHECKING, cast

from ..decorators import abstract

if TYPE_CHECKING:
    import redis


class BaseTicketQueue:
    """ Base API for ticket queues. """

    @abstract
    def register(self) -> tuple[int, str]:
        raise NotImplementedError

    @abstract
    def is_head(self, ticket: int) -> bool:
        raise NotImplementedError

    @abstract
    def remove(self, member: str) -> None:
        raise NotImplementedError

    @abstract
    def cleanup_stale(self) -> None:
        raise NotImplementedError

    @abstract
    def is_empty(self) -> bool:
        """ Return True if the queue currently has no waiting members.

        Implementations should consider the concrete storage details (e.g. on
        filesystem the "seq" file is not considered a queue member).
        """
        raise NotImplementedError

    @abstract
    def maybe_cleanup(self) -> None:
        """ Attempt to remove any on-disk or remote artifacts when the queue is empty.

        This should be a best-effort no-op if other clients are concurrently
        active. Implementations should handle errors internally and not raise.
        """
        raise NotImplementedError


class FileTicketQueue(BaseTicketQueue):
    """ File-system backed ticket queue.

    Tickets are assigned using a small ``seq`` file protected by an exclusive
    lock (via ``fcntl`` on POSIX). Each waiter creates a ticket file named
    ``{ticket:020d}.{pid}.{uuid}`` in the queue directory. The head of the
    sorted directory listing is considered the current owner.

    Examples:
        >>> # Basic filesystem queue behaviour and cleanup
        >>> import tempfile, os, time
        >>> tmp = tempfile.mkdtemp()
        >>> qd = tmp + "/q"
        >>> q = FileTicketQueue(qd, stale_timeout=0.01)
        >>> t1, m1 = q.register()
        >>> t2, m2 = q.register()
        >>> q.is_head(t1)
        True
        >>> q.remove(m1)
        >>> q.is_head(t2)
        True
        >>> # Make the remaining ticket appear stale and cleanup
        >>> p = os.path.join(qd, m2)
        >>> os.utime(p, (0, 0))
        >>> q.cleanup_stale()
        >>> q.is_empty()
        True
        >>> q.maybe_cleanup()
        >>> os.path.exists(qd)
        False
    """

    def __init__(self, queue_dir: str, stale_timeout: float | None = None) -> None:
        self.queue_dir: str = queue_dir
        self.stale_timeout: float | None = stale_timeout
        os.makedirs(queue_dir, exist_ok=True)

    def _get_ticket(self) -> int:
        seq_path: str = os.path.join(self.queue_dir, "seq")
        try:
            import fcntl
            # Ensure seq file exists and atomically increment it
            os.makedirs(self.queue_dir, exist_ok=True)
            with open(seq_path, "a+b") as f:
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
            # Fallback to timestamp + random suffix to reduce collisions
            import random
            return int(time.time() * 1e6) * 1000000 + random.getrandbits(48)

    def register(self) -> tuple[int, str]:
        ticket: int = self._get_ticket()
        fname: str = f"{ticket:020d}.{os.getpid()}.{uuid.uuid4().hex}"
        p: str = os.path.join(self.queue_dir, fname)
        # Create our ticket file
        with open(p, "w") as f:
            f.write(str(time.time()))
        return ticket, fname

    def is_head(self, ticket: int) -> bool:
        try:
            files: list[str] = sorted(os.listdir(self.queue_dir))
        except FileNotFoundError:
            return False
        if not files:
            return False
        try:
            head_ticket: int = int(files[0].split(".")[0])
        except Exception:
            return False
        return head_ticket == ticket

    def remove(self, member: str) -> None:
        try:
            p: str = os.path.join(self.queue_dir, member)
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass

    def cleanup_stale(self) -> None:
        """ Remove stale head ticket if its mtime exceeds the stale timeout. """
        stale: float | None = self.stale_timeout
        if stale is None:
            return
        try:
            files: list[str] = sorted(os.listdir(self.queue_dir))
            if not files:
                return
            head: str = files[0]
            p: str = os.path.join(self.queue_dir, head)
            try:
                mtime: float = os.path.getmtime(p)
            except Exception:
                return
            if time.time() - mtime >= stale:
                try:
                    os.remove(p)
                except Exception:
                    pass
        except Exception:
            pass

    def is_empty(self) -> bool:
        """Return True if the queue directory contains no ticket files.

        The sequence file ``seq`` is ignored when determining emptiness.
        """
        try:
            files: list[str] = sorted(os.listdir(self.queue_dir))
        except Exception:
            return True
        # Exclude the seq file which is used to allocate tickets
        members = [f for f in files if f != "seq"]
        return len(members) == 0

    def maybe_cleanup(self) -> None:
        """ Try to remove sequence file and queue dir if the queue is empty.

        This is a best-effort operation: if other clients are active or a
        race occurs, the function simply returns without raising.
        """
        try:
            if not self.is_empty():
                return
            # Remove seq file if present
            seq_path: str = os.path.join(self.queue_dir, "seq")
            try:
                if os.path.exists(seq_path):
                    os.remove(seq_path)
            except Exception:
                pass
            # Attempt to remove directory if empty
            try:
                os.rmdir(self.queue_dir)
            except Exception:
                pass
        except Exception:
            pass


class RedisTicketQueue(BaseTicketQueue):
    """ Redis-backed ticket queue using INCR + ZADD.

    Member format: ``{ticket}:{token}:{ts_ms}`` where ``ts_ms`` is the
    insertion timestamp in milliseconds. The ZSET score is the ticket number
    which provides ordering. This class performs stale head cleanup based on
    the provided stale timeout.

    Examples:
        >>> # Basic Redis queue behaviour (requires a local redis server)
        >>> import time
        >>> import redis
        >>> client = redis.Redis()
        >>> name = "doctest:rq"
        >>> # Ensure clean start
        >>> _ = client.delete(f"{name}:queue")
        >>> _ = client.delete(f"{name}:seq")
        >>> q = RedisTicketQueue(name, client, stale_timeout=0.01)
        >>> t1, m1 = q.register()
        >>> t2, m2 = q.register()
        >>> q.is_head(t1)
        True
        >>> q.remove(m1)
        >>> q.is_head(t2)
        True
        >>> q.remove(m2)
        >>> q.maybe_cleanup()
        >>> print(client.exists(f"{name}:queue") == 0 and client.exists(f"{name}:seq") == 0)
        True
    """

    def __init__(self, name: str, client: redis.Redis | None = None, stale_timeout: float | None = None) -> None:
        self.name: str = name
        self.client: redis.Redis | None = client
        self.stale_timeout: float | None = stale_timeout

    def ensure_client(self) -> redis.Redis:
        if self.client is None:
            import redis
            self.client = redis.Redis()
        return self.client

    def register(self) -> tuple[int, str]:
        client: redis.Redis = self.ensure_client()
        # redis-py may have a partly unknown return type; cast to int for Pylance
        ticket: int = cast(int, client.incr(f"{self.name}:seq"))
        ts_ms: int = int(time.monotonic() * 1000)
        token: str = uuid.uuid4().hex
        member: str = f"{ticket}:{token}:{ts_ms}"
        client.zadd(f"{self.name}:queue", {member: ticket})
        return ticket, member

    def is_head(self, ticket: int) -> bool:
        client: redis.Redis = self.ensure_client()
        # zrange may return an Awaitable or a list of bytes; cast to list[bytes]
        head = cast(list[bytes], client.zrange(f"{self.name}:queue", 0, 0))  # type: ignore[reportUnknownMemberType]
        if not head:
            return False
        head_member: str = head[0].decode()
        try:
            head_ticket: int = int(head_member.split(":")[0])
        except Exception:
            return False
        return head_ticket == ticket

    def remove(self, member: str) -> None:
        try:
            client: redis.Redis = self.ensure_client()
            client.zrem(f"{self.name}:queue", member)
        except Exception:
            pass

    def cleanup_stale(self) -> None:
        stale: float | None = self.stale_timeout
        if stale is None:
            return
        try:
            client: redis.Redis = self.ensure_client()
            # zrange may return an Awaitable or a list of bytes; cast to list[bytes]
            head = cast(list[bytes], client.zrange(f"{self.name}:queue", 0, 0))  # type: ignore[reportUnknownMemberType]
            if not head:
                return
            head_member: str = head[0].decode()
            parts: list[str] = head_member.split(":" )
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

    def is_empty(self) -> bool:
        try:
            client: redis.Redis = self.ensure_client()
            cnt = cast(int, client.zcard(f"{self.name}:queue"))
            return cnt == 0
        except Exception:
            # On error assume non-empty to avoid aggressive cleanup
            return False

    def maybe_cleanup(self) -> None:
        """Attempt to remove Redis keys used by the queue when it is empty.

        This is best effort: if concurrent clients are active the operation may
        be a no-op.
        """
        try:
            if not self.is_empty():
                return
            client: redis.Redis = self.ensure_client()
            try:
                client.delete(f"{self.name}:queue")
                client.delete(f"{self.name}:seq")
            except Exception:
                pass
        except Exception:
            pass
