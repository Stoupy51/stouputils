"""
This module provides utility functions for printing package version information
in a structured format, including the main package and its dependencies.

Functions:

- :py:func:`show_version`: Print the version of the main package and its dependencies.
"""

# Lazy imports (PEP 810), ignored before Python 3.15
from .lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import sys
from contextlib import suppress
from dataclasses import dataclass, field

from .config import StouputilsConfig as Cfg


# Classes
@dataclass
class VersionPrinter:
	""" Prints a package and its dependencies, either as a flat list or as a tree.

	Examples:
		>>> VersionPrinter.dependency_name('msgspec[toml,yaml]>=0.20.0')
		'msgspec'
		>>> VersionPrinter.dependency_name('numpy; python_version >= "3.14"')
		'numpy'
	"""
	main_package: str = "stouputils"
	""" Package the report starts from. """
	primary_color: str = Cfg.CYAN
	""" Color of the package names and the separators. """
	secondary_color: str = Cfg.GREEN
	""" Color of the version numbers. """
	max_depth: int = 2
	""" Depth of the dependency tree, 2 or less printing a flat list instead. """
	fully_displayed: set[str] = field(default_factory=set[str])
	""" Packages whose dependencies were already printed once, marked as such on the next occurrence. """

	@staticmethod
	def version_of(package_name: str) -> str:
		""" Installed version of a package, empty when it is not installed.

		Args:
			package_name (str): Name of the package
		Returns:
			str: Version of the package, ex: "1.0.0"
		"""
		from importlib.metadata import version
		try:
			return version(package_name).split("version: ")[-1]
		except Exception:
			return ""

	@staticmethod
	def dependency_name(requirement: str) -> str:
		""" Name of the package a requirement refers to, without its version, extras or markers.

		Args:
			requirement (str): Requirement as written in the metadata, ex: "msgspec[toml,yaml]>=0.20.0"
		Returns:
			str: Name of the required package, ex: "msgspec"
		"""
		name: str = requirement
		for separator in (">", "<", "=", "[", ";"):
			name = name.split(separator)[0]
		return name.strip()

	@classmethod
	def dependencies_of(cls, package_name: str, with_extras: bool = True) -> list[str]:
		""" Sorted names of the packages a package depends on, without duplicates.

		Args:
			package_name (str):  Name of the package
			with_extras  (bool): Whether the dependencies of the optional extras are included
		Returns:
			list[str]: Names of the dependencies, ex: ["numpy", "tqdm"]
		"""
		from importlib.metadata import requires
		try:
			requirements: list[str] = requires(package_name) or []
			if not with_extras:
				requirements = [requirement for requirement in requirements if "extra ==" not in requirement]
			return sorted({cls.dependency_name(requirement) for requirement in requirements})
		except Exception:
			return []

	def separators(self, length: int) -> tuple[str, str]:
		""" Build the two separator lines framing the main package.

		Args:
			length (int): Width of the separators, in characters
		Returns:
			tuple[str, str]: Separator holding the Python version, and plain separator
		"""
		python_version: str = f" Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} "
		left_dashes: int = (length - len(python_version)) // 2
		right_dashes: int = length - len(python_version) - left_dashes
		return "─" * left_dashes + python_version + "─" * right_dashes, "─" * length

	@property
	def minimum_width(self) -> int:
		""" Width leaving at least five dashes on each side of the Python version. """
		return len(f" Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} ") + 10

	def print_package(self, package_name: str, version: str, prefix: str = "", suffix: str = "") -> None:
		""" Print one package line.

		Args:
			package_name (str): Name of the package
			version      (str): Version of the package
			prefix       (str): Text written before the package name, ex: the tree branches
			suffix       (str): Text written after the version, ex: the already shown marker
		"""
		print(f"{prefix}{self.primary_color}{package_name}  {self.secondary_color}v{version}{suffix}{Cfg.RESET}")

	def print_node(self, package_name: str, version: str, prefix: str, is_last: bool, depth: int) -> bool:
		""" Print the line of one node of the tree.

		Args:
			package_name (str):  Name of the package
			version      (str):  Version of the package
			prefix       (str):  Branches already drawn on the left of this package
			is_last      (bool): Whether the package is the last child of its parent
			depth        (int):  Current depth, the main package being at 0
		Returns:
			bool: Whether the dependencies of this package are worth walking
		"""
		if depth == 0:
			self.print_package(package_name, version)
			return True

		connector: str = "└── " if is_last else "├── "
		if package_name in self.fully_displayed:
			self.print_package(package_name, version, prefix + connector, f" {Cfg.YELLOW}[Already shown ^]")
			return False

		self.print_package(package_name, version, prefix + connector)
		return True

	def print_tree(
		self, package_name: str, prefix: str = "", is_last: bool = True, visited: set[str] | None = None, depth: int = 0
	) -> None:
		""" Print a package and its dependencies as a tree, walking each branch once.

		Args:
			package_name (str):         Name of the package to print
			prefix       (str):         Branches already drawn on the left of this package
			is_last      (bool):        Whether the package is the last child of its parent
			visited      (set[str]):    Packages already printed in this branch, to stop cycles
			depth        (int):         Current depth, the main package being at 0
		"""
		visited = set() if visited is None else visited
		if package_name in visited or depth > self.max_depth - 1:
			return
		visited.add(package_name)

		version: str = self.version_of(package_name)
		if not version:
			return

		if not self.print_node(package_name, version, prefix, is_last, depth):
			return

		# The children hang under the current node, so their prefix depends on the current node being last
		dependencies: list[str] = [dep for dep in self.dependencies_of(package_name) if self.version_of(dep)]
		extension: str = "    " if is_last else "│   "
		for index, dependency in enumerate(dependencies):
			child_prefix: str = prefix + extension if depth > 0 else ""
			self.print_tree(dependency, child_prefix, index == len(dependencies) - 1, visited.copy(), depth + 1)

		self.fully_displayed.add(package_name)

	def print_flat(self) -> None:
		""" Print the main package and its direct dependencies as an aligned list. """
		versions: list[tuple[str, str]] = [
			(name, self.version_of(name))
			for name in (self.main_package, *self.dependencies_of(self.main_package, with_extras=False))
		]
		versions = [(name, version) for name, version in versions if version]

		longest_name: int = max(len(name) for name, _ in versions)
		width: int = max(self.minimum_width, longest_name + max(len(version) for _, version in versions) + 4)
		separator_with_python, separator = self.separators(width)

		for name, version in versions:
			spacing: str = " " * (longest_name - len(name))
			if name == self.main_package:
				print(f"{self.primary_color}{separator_with_python}{Cfg.RESET}")
				self.print_package(f"{name}{spacing}", version)
				print(f"{self.primary_color}{separator}{Cfg.RESET}")
			else:
				self.print_package(f"{name}{spacing}", version)

	def show(self) -> None:
		""" Print the whole report, as a tree or as a flat list depending on the requested depth. """
		if self.max_depth < 3:
			self.print_flat()
			return

		separator_with_python, separator = self.separators(self.minimum_width)
		print(f"{self.primary_color}{separator_with_python}{Cfg.RESET}")
		self.print_tree(self.main_package)
		print(f"{self.primary_color}{separator}{Cfg.RESET}")


# Functions
def show_version(
	main_package: str = "stouputils", primary_color: str = Cfg.CYAN, secondary_color: str = Cfg.GREEN, max_depth: int = 2
) -> None:
	""" Print the version of the main package and its dependencies.

	Used by the "stouputils --version" command.

	Args:
		main_package	(str):	Name of the main package to show version for
		primary_color	(str):	Color to use for the primary package name (defaults to cyan)
		secondary_color	(str):	Color to use for the secondary package names (defaults to green)
		max_depth		(int):	Maximum depth for dependency tree (<= 2 for flat, >=3 for tree)
	"""
	VersionPrinter(
		main_package=main_package, primary_color=primary_color, secondary_color=secondary_color, max_depth=max_depth
	).show()

# Show version cli
def show_version_cli() -> None:
	""" Handle the "stouputils --version" CLI command """
	# Determine max depth (flat or tree structure)
	max_depth: int = 2  # Flat by default

	# Check for tree argument
	if "--tree" in sys.argv or "-t" in sys.argv:
		# Find position of tree argument
		pos: int = sys.argv.index("--tree") if "--tree" in sys.argv else sys.argv.index("-t")

		# Check for depth argument
		if pos + 1 < len(sys.argv):
			with suppress(ValueError):
				max_depth = int(sys.argv[pos + 1])
				sys.argv.pop(pos + 1)  # Remove depth argument
		sys.argv.pop(pos)  # Remove the --tree/-t argument

	# Handle specific package argument
	if len(sys.argv) >= 3 and not sys.argv[2].startswith("-"):
		return show_version(sys.argv[2], max_depth=max_depth)

	# Else, show default package version
	return show_version(max_depth=max_depth)

