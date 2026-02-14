""" Inter-process locks implementing First-In-First-Out (FIFO).

Source:

- https://en.wikipedia.org/wiki/File_locking
- https://en.wikipedia.org/wiki/Starvation_%28computer_science%29
- https://en.wikipedia.org/wiki/FIFO_and_LIFO_accounting

Provides three classes:

- :py:class:`~base.LockFifo`: basic cross-process lock using filesystem (POSIX via fcntl, Windows via msvcrt).
- :py:class:`~re_entrant.RLockFifo`: reentrant per-(process,thread) lock built on top of :py:class:`~base.LockFifo`.
- :py:class:`~redis_fifo.RedisLockFifo`: distributed lock using redis (optional dependency).

Usage
-----
>>> import stouputils as stp
>>> with stp.LockFifo("some_directory/my.lock", timeout=5):
...     pass

>>> with stp.RLockFifo("some_directory/my_r.lock", timeout=5):
...     pass

>>> def _redis_example():
...     with stp.RedisLockFifo("my_redis_lock", timeout=5):
...         pass
>>> import os
>>> if os.name != "nt":
...     _redis_example()
"""
# Imports
from .base import *
from .queue import *
from .re_entrant import *
from .redis_fifo import *
from .shared import *

