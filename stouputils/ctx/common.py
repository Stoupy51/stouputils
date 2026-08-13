
# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
from contextlib import AbstractAsyncContextManager, AbstractContextManager


# Abstract base class for context managers supporting both sync and async usage
class AbstractBothContextManager[T](AbstractContextManager[T], AbstractAsyncContextManager[T]):
    """ Abstract base class for context managers that support both synchronous and asynchronous usage. """
    pass

