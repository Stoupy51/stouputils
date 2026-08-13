""" Consistency check for packages that re-export their submodules explicitly.

Explicit re-exports are what makes PEP 810 lazy imports possible, since a star import resolves
every deferred name at once. The cost is that a new public function is easy to forget in the
parent package, so this module compares each submodule against the package that re-exports it.
"""
# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import importlib
import pkgutil
from types import ModuleType


# Functions
def module_public_names(module: ModuleType) -> list[str]:
	""" List the public names a module defines itself, ignoring anything it merely imported.

	Only objects carrying a __module__ are considered, so plain constants are out of scope.

	Args:
		module (ModuleType): Module to inspect
	Returns:
		list[str]: Names defined by that module, sorted

	Examples:
		>>> from stouputils.all_doctests import reexports
		>>> module_public_names(reexports)
		['find_missing_reexports', 'module_public_names']
	"""
	return sorted(
		name for name, value in vars(module).items()
		if not name.startswith("_") and getattr(value, "__module__", None) == module.__name__
	)


def find_missing_reexports(package: ModuleType) -> dict[str, list[str]]:
	""" Find names a submodule defines that its parent package does not expose at all.

	A submodule the parent exposes nothing from counts as deliberately internal and is skipped,
	which is how modules such as :py:mod:`stouputils.config` stay out of the flat namespace.
	A name the parent already binds to a sibling's definition is a plain naming clash, not a
	missing re-export, so it is not reported here either.
	Submodules that cannot be imported are skipped, since optional dependencies may be absent.

	Args:
		package (ModuleType): Root package to walk
	Returns:
		dict[str, list[str]]: Missing names, keyed by the submodule that defines them

	Examples:
		>>> import stouputils
		>>> find_missing_reexports(stouputils)
		{}
	"""
	missing: dict[str, list[str]] = {}
	for found in pkgutil.walk_packages(package.__path__, prefix=f"{package.__name__}.", onerror=lambda _: None):
		try:
			module: ModuleType = importlib.import_module(found.name)
			parent: ModuleType = importlib.import_module(found.name.rsplit(".", 1)[0])
		except ImportError:
			continue
		names: list[str] = module_public_names(module)
		reachable: list[str] = [name for name in names if hasattr(parent, name)]
		if reachable and len(reachable) != len(names):
			missing[found.name] = [name for name in names if name not in reachable]
	return missing
