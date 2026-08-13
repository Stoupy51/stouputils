""" Marker that defers every import of a module under PEP 810.

Python 3.15 decides whether an import is lazy by evaluating ``name in __lazy_modules__``, and the
specification only requires that object to support ``__contains__``. Answering yes to everything
keeps the declaration down to one shared marker per module, instead of a list that has to be kept
in step with every import statement. Older Python versions ignore ``__lazy_modules__`` entirely.

Star imports, ``__future__`` imports and imports inside a ``try`` block stay eager whatever this
marker says, since PEP 810 refuses to defer those.
"""


# Classes
class AlwaysLazy:
	""" Container that reports every module name as deferrable. """

	def __contains__(self, name: str) -> bool:
		""" Report the module as deferrable, whichever module it is.

		Args:
			name (str): Fully qualified name of the module being imported
		Returns:
			bool: Always True

		Examples:
			>>> "json" in AlwaysLazy()
			True
			>>> "stouputils.decorators" in AlwaysLazy()
			True
		"""
		return True


# Constants
ALWAYS_LAZY: AlwaysLazy = AlwaysLazy()
""" Shared marker assigned to __lazy_modules__ at the top of every module in the package. """
