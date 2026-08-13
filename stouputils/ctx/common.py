
# Lazy imports (PEP 810), ignored before Python 3.15
__lazy_modules__: frozenset[str] = frozenset({
	"contextlib",
})

# Imports
from contextlib import AbstractAsyncContextManager, AbstractContextManager


# Abstract base class for context managers supporting both sync and async usage
class AbstractBothContextManager[T](AbstractContextManager[T], AbstractAsyncContextManager[T]):
    """ Abstract base class for context managers that support both synchronous and asynchronous usage. """
    pass

