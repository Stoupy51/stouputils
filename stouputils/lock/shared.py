
# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import os
import tempfile
import time

from ..io.path import clean_path


class LockError(RuntimeError):
	""" Base lock error. """
class LockTimeoutError(TimeoutError, LockError):
	""" Raised when a lock could not be acquired within ``timeout`` seconds. """


def resolve_path(path: str) -> str:
	""" Resolve a lock file path, placing it in the system temporary directory if only a name is given.

	>>> import os, tempfile
	>>> p = resolve_path('foo.lock')
	>>> os.path.basename(p) == 'foo.lock'
	True
	"""
	path = clean_path(path)
	name = os.path.basename(path)
	if name == path:
		path = f"{tempfile.gettempdir()}/{name}"
	os.makedirs(os.path.dirname(path), exist_ok=True)
	return path


def resolve_acquire_defaults(
	blocking_arg: bool | None,
	timeout_arg: float | None,
	check_interval_arg: float | None,
	default_blocking: bool,
	default_timeout: float | None,
	default_check_interval: float,
) -> tuple[bool, float | None, float, float | None]:
	""" Resolve acquire() parameter defaults and compute the deadline.

	Returns:
		(blocking, timeout, check_interval, deadline)
	"""
	blocking: bool = default_blocking if blocking_arg is None else blocking_arg
	timeout: float | None = default_timeout if timeout_arg is None else timeout_arg
	check_interval: float = default_check_interval if check_interval_arg is None else check_interval_arg
	deadline: float | None = None if timeout is None else (time.monotonic() + timeout)
	return blocking, timeout, check_interval, deadline


def wait_or_raise(blocking: bool, deadline: float | None, check_interval: float, name: str) -> None:
	""" Sleep one check interval before the next attempt on a busy lock, or raise when waiting is not allowed.

	Args:
		deadline: ``time.monotonic()`` value past which waiting stops, None to wait forever.
		name:     Lock name or path the timeout message reports.
	Raises:
		LockTimeoutError: If ``blocking`` is False or ``deadline`` has passed.

	>>> wait_or_raise(False, None, 0.0, "foo.lock")
	Traceback (most recent call last):
		...
	stouputils.lock.shared.LockTimeoutError: Lock is already held and blocking is False
	>>> wait_or_raise(True, 0.0, 0.0, "foo.lock")
	Traceback (most recent call last):
		...
	stouputils.lock.shared.LockTimeoutError: Timeout while waiting for lock 'foo.lock'
	"""
	if not blocking:
		raise LockTimeoutError("Lock is already held and blocking is False")
	if deadline is not None and time.monotonic() >= deadline:
		raise LockTimeoutError(f"Timeout while waiting for lock '{name}'")
	time.sleep(check_interval)

