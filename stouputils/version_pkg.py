"""
This module provides utility functions for printing package version information
in a structured format, including the main package and its dependencies.

Functions:
- show_version: Print the version of the main package and its dependencies.
"""

# Imports
import sys

from .print import CYAN, GREEN, RESET, YELLOW


# Show version function
def show_version(main_package: str = "stouputils", primary_color: str = CYAN, secondary_color: str = GREEN, max_depth: int = 2) -> None:
	""" Print the version of the main package and its dependencies.

	Used by the "stouputils --version" command.

	Args:
		main_package	(str):	Name of the main package to show version for
		primary_color	(str):	Color to use for the primary package name
		secondary_color	(str):	Color to use for the secondary package names
		max_depth		(int):	Maximum depth for dependency tree (<= 2 for flat, >=3 for tree)
	"""
	# Imports
	from importlib.metadata import requires, version
	def ver(package_name: str) -> str:
		try:
			return version(package_name)
		except Exception:
			return ""

	def get_deps(package_name: str) -> list[str]:
		""" Get the list of dependency names for a package """
		try:
			deps: list[str] = requires(package_name) or []
			# Remove duplicates while preserving order, then sort
			unique_deps: list[str] = list(dict.fromkeys([
				dep
					.split(">")[0]
					.split("<")[0]
					.split("=")[0]
					.split("[")[0]
					.split(";")[0]
					.strip()
				for dep in deps
			]))
			return sorted(unique_deps)
		except Exception:
			return []

	def print_tree(package_name: str, prefix: str = "", is_last: bool = True, visited: set[str] | None = None, fully_displayed: set[str] | None = None, depth: int = 0, max_depth: int = 3) -> None:
		""" Recursively print the dependency tree """
		if visited is None:
			visited = set()
		if fully_displayed is None:
			fully_displayed = set()

		# Prevent infinite recursion and limit depth
		if package_name in visited or depth > max_depth:
			return
		visited.add(package_name)

		# Get version
		v: str = ver(package_name).split("version: ")[-1]
		if not v:
			return

		# Determine the tree characters
		connector: str = "└── " if is_last else "├── "

		# Check if this package was already fully displayed
		already_shown: bool = package_name in fully_displayed

		# Print current package
		if depth == 0:
			print(f"{primary_color}{package_name}  {secondary_color}v{v}{RESET}")
		else:
			if already_shown:
				print(f"{prefix}{connector}{primary_color}{package_name}  {secondary_color}v{v} {YELLOW}[Already shown ^]{RESET}")
				# Still mark as fully displayed even when already shown
				fully_displayed.add(package_name)
				return
			else:
				print(f"{prefix}{connector}{primary_color}{package_name}  {secondary_color}v{v}{RESET}")

		# Get dependencies
		deps: list[str] = get_deps(package_name)

		# Filter dependencies that will actually be displayed (have a version)
		valid_deps: list[str] = [dep for dep in deps if ver(dep)]

		# Print dependencies recursively
		for i, dep in enumerate(valid_deps):
			# Determine if this is the last element to display
			is_last_dep: bool = (i == len(valid_deps) - 1)

			# Extension is based on whether the CURRENT node is last, not the child
			extension: str = "    " if is_last else "│   "
			new_prefix: str = prefix + extension if depth > 0 else ""
			print_tree(dep, new_prefix, is_last_dep, visited.copy(), fully_displayed, depth + 1, max_depth)

		# Mark this package as fully displayed (with all its dependencies)
		fully_displayed.add(package_name)

	# Get Python version header
	python_version: str = f" Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} "

	if max_depth >= 3:
		# Display as tree structure
		minimum_separator_length: int = len(python_version) + 10
		separator_length: int = minimum_separator_length
		python_text_length: int = len(python_version)
		left_dashes: int = (separator_length - python_text_length) // 2
		right_dashes: int = separator_length - python_text_length - left_dashes
		separator_with_python: str = "─" * left_dashes + python_version + "─" * right_dashes
		separator: str = "─" * separator_length

		print(f"{primary_color}{separator_with_python}{RESET}")
		print_tree(main_package, max_depth=max_depth - 1)
		print(f"{primary_color}{separator}{RESET}")
	else:
		# Display as flat list (original behavior)
		deps: list[str] = requires(main_package) or []
		dep_names: list[str] = sorted([
			dep
				.split(">")[0]
				.split("<")[0]
				.split("=")[0]
				.split("[")[0]
			for dep in deps
		])
		all_deps: list[tuple[str, str]] = [
			(x, ver(x).split("version: ")[-1])
			for x in (main_package, *dep_names)
		]
		all_deps = [pair for pair in all_deps if pair[1]]  # Filter out packages with no version found
		longest_name_length: int = max(len(name) for name, _ in all_deps)
		longest_version_length: int = max(len(ver) for _, ver in all_deps)

		minimum_separator_length: int = len(python_version) + 10	# Always at least 5 dashes on each side
		separator_length: int = max(minimum_separator_length, longest_name_length + longest_version_length + 4)
		python_text_length: int = len(python_version)
		left_dashes: int = (separator_length - python_text_length) // 2
		right_dashes: int = separator_length - python_text_length - left_dashes
		separator_with_python: str = "─" * left_dashes + python_version + "─" * right_dashes
		separator: str = "─" * separator_length

		for pkg, v in all_deps:
			pkg_spacing: str = " " * (longest_name_length - len(pkg))

			# Highlight the main package with a different style
			if pkg == main_package:
				print(f"{primary_color}{separator_with_python}{RESET}")
				print(f"{primary_color}{pkg}{pkg_spacing}  {secondary_color}v{v}{RESET}")
				print(f"{primary_color}{separator}{RESET}")
			else:
				print(f"{primary_color}{pkg}{pkg_spacing}  {secondary_color}v{v}{RESET}")
	return

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
			try:
				max_depth = int(sys.argv[pos + 1])
				sys.argv.pop(pos + 1)  # Remove depth argument
			except ValueError:
				pass  # Keep default if conversion fails
		sys.argv.pop(pos)  # Remove the --tree/-t argument

	# Handle specific package argument
	if len(sys.argv) >= 3 and not sys.argv[2].startswith("-"):
		return show_version(sys.argv[2], max_depth=max_depth)

	# Else, show default package version
	return show_version(max_depth=max_depth)

