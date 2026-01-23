""" Simple inter-process locks.

Provides three classes:

- LockFifo: basic cross-process lock using filesystem (POSIX via fcntl, Windows via msvcrt).
- RLockFifo: reentrant per-(process,thread) lock built on top of LockFifo.
- RedisLockFifo: distributed lock using redis (optional dependency).

Usage
-----
>>> import stouputils as stp
>>> with stp.LockFifo("some_directory/my.lock", timeout=5):
...     pass

>>> with stp.RLockFifo("some_directory/my_r.lock", timeout=5):
...     pass

>>> with stp.RedisLockFifo("my_redis_lock", timeout=5):
...     pass
"""
# Imports
from .base import *
from .queue import *
from .re_entrant import *
from .redis_fifo import *
from .shared import *

