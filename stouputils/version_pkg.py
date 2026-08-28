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
	""" Packages whose dependencies were already printed once, collapsed into one line on the next occurrence. """

	@staticmethod
	def version_of(package_name: str) -> str:
		""" Installed version of a package, empty when it is not installed.

		Args:
			package_name: Name of the package
		Returns:
			Version of the package, ex: "1.0.0"
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
			requirement: Requirement as written in the metadata, ex: "msgspec[toml,yaml]>=0.20.0"
		Returns:
			Name of the required package, ex: "msgspec"
		"""
		name: str = requirement
		for separator in (">", "<", "=", "[", ";"):
			name = name.split(separator)[0]
		return name.strip()

	@classmethod
	def dependencies_of(cls, package_name: str, with_extras: bool = True) -> list[str]:
		""" Sorted names of the packages a package depends on, without duplicates.

		Args:
			package_name: Name of the package
			with_extras:  Whether the dependencies of the optional extras are included
		Returns:
			Names of the dependencies, ex: ["numpy", "tqdm"]
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
			length: Width of the separators, in characters
		Returns:
			Separator holding the Python version, and plain separator
		"""
		python_version: str = f" Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} "
		left_dashes: int = (length - len(python_version)) // 2
		right_dashes: int = length - len(python_version) - left_dashes
		return "─" * left_dashes + python_version + "─" * right_dashes, "─" * length

	@property
	def minimum_width(self) -> int:
		""" Width leaving at least five dashes on each side of the Python version. """
		return len(f" Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} ") + 10

	def package_line(self, package_name: str, version: str, suffix: str = "") -> str:
		""" Build the line describing one package.

		Args:
			package_name: Name of the package
			version:      Version of the package
			suffix:       Text written after the version, ex: the already shown marker
		Returns:
			Colored line, ex: "stouputils  v1.0.0"
		"""
		return f"{self.primary_color}{package_name}  {self.secondary_color}v{version}{suffix}{Cfg.RESET}"

	def already_shown_line(self, package_names: list[str]) -> str:
		""" Build the line collapsing every dependency whose own tree was printed earlier.

		Args:
			package_names: Names of the packages already printed
		Returns:
			Colored line, ex: "Already shown ^: markdown, pygments"
		"""
		return f"{Cfg.YELLOW}Already shown ^: {self.primary_color}{', '.join(package_names)}{Cfg.RESET}"

	@staticmethod
	def indent_block(lines: list[str], is_last: bool) -> list[str]:
		""" Hang a subtree under its parent, the first line carrying the connector.

		Args:
			lines:   Lines of the subtree, indented relative to its own root
			is_last: Whether the subtree is the last child of its parent
		Returns:
			Lines indented relative to the parent
		Examples:
			>>> VersionPrinter.indent_block(["numpy", "└── tqdm"], is_last=False)
			['├── numpy', '│   └── tqdm']
			>>> VersionPrinter.indent_block(["numpy", "└── tqdm"], is_last=True)
			['└── numpy', '    └── tqdm']
		"""
		connector: str = "└── " if is_last else "├── "
		extension: str = "    " if is_last else "│   "
		return [connector + lines[0], *(extension + line for line in lines[1:])]

	def render_tree(self, package_name: str, visited: frozenset[str] = frozenset(), depth: int = 0) -> list[str]:
		""" Render a package and its dependencies, indented relative to that package.

		Dependencies whose own tree was printed earlier are collapsed into a single line at the end,
		since repeating their name, version and marker on one line each drowns the ones worth reading.

		Args:
			package_name: Name of the package to render
			visited:      Packages already rendered in this branch, to stop cycles
			depth:        Current depth, the main package being at 0
		Returns:
			Lines of the subtree, the package itself being the first one
		"""
		version: str = self.version_of(package_name)
		if not version:
			return []

		lines: list[str] = [self.package_line(package_name, version)]
		self.fully_displayed.add(package_name)
		if depth >= self.max_depth - 1:
			return lines

		branch: frozenset[str] = visited | {package_name}
		blocks: list[list[str]] = []
		already_shown: list[str] = []
		for dependency in self.dependencies_of(package_name):
			if dependency in branch or not self.version_of(dependency):
				continue

			# A dependency printed by an earlier sibling only becomes known as such once that sibling is rendered
			if dependency in self.fully_displayed:
				already_shown.append(dependency)
			else:
				blocks.append(self.render_tree(dependency, branch, depth + 1))
		if already_shown:
			blocks.append([self.already_shown_line(already_shown)])

		for index, block in enumerate(blocks):
			lines.extend(self.indent_block(block, is_last=index == len(blocks) - 1))
		return lines

	def print_tree(self, package_name: str) -> None:
		""" Print a package and its dependencies as a tree, walking each branch once.

		Args:
			package_name: Name of the package to print
		"""
		print("\n".join(self.render_tree(package_name)))

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
				print(self.package_line(f"{name}{spacing}", version))
				print(f"{self.primary_color}{separator}{Cfg.RESET}")
			else:
				print(self.package_line(f"{name}{spacing}", version))

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
		main_package:    Name of the main package to show version for
		primary_color:   Color to use for the primary package name (defaults to cyan)
		secondary_color: Color to use for the secondary package names (defaults to green)
		max_depth:       Maximum depth for dependency tree (<= 2 for flat, >=3 for tree)
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

