
# Imports
from contextlib import AbstractAsyncContextManager, AbstractContextManager


# Abstract base class for context managers supporting both sync and async usage
class AbstractBothContextManager[T](AbstractContextManager[T], AbstractAsyncContextManager[T]):
    """ Abstract base class for context managers that support both synchronous and asynchronous usage. """
    pass

