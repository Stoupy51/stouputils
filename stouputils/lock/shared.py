
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

    Examples:
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
        tuple: (blocking, timeout, check_interval, deadline)
    """
    blocking: bool = default_blocking if blocking_arg is None else blocking_arg
    timeout: float | None = default_timeout if timeout_arg is None else timeout_arg
    check_interval: float = default_check_interval if check_interval_arg is None else check_interval_arg
    deadline: float | None = None if timeout is None else (time.monotonic() + timeout)
    return blocking, timeout, check_interval, deadline

