""" Simple inter-process locks.

Provides three classes:

- SimpleLock: basic cross-process lock using filesystem (POSIX via fcntl, Windows via msvcrt).
- SimpleRLock: reentrant per-(process,thread) lock built on top of SimpleLock.
- SimpleRedisLock: distributed lock using redis (optional dependency).

Usage
-----
>>> import stouputils as stp
>>> with stp.SimpleLock("my.lock", timeout=5):
...     pass

>>> with stp.SimpleRLock("some_directory/my_r.lock", timeout=5):
...     pass

>>> with stp.SimpleRedisLock("my_redis_lock", timeout=5):
...     pass
"""
# Imports
from .simple import *
from .simple_r import *
from .simple_redis import *

