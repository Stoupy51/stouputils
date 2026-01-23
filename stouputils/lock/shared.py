
# Imports
import os
import tempfile

from ..io import clean_path


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

