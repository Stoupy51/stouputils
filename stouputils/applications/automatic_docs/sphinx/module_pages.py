""" Generation of the API reference, one page per package.

A page opens with the package docstring, lists its subpackages, then gives each module of the package a section.
When a subpackage's ``__init__.py`` imports names from its modules, those names are its API and the only ones documented,
which leaves out the modules it imports nothing from. The root package's modules are imported by their own path, so they are all kept.
An emoji opening the docstring of a package or module also opens its title, and breeze shows it in the navigation.
"""
# Lazy imports (PEP 810), ignored before Python 3.15
from ....lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import ast
from pathlib import Path

from ....io.path import super_open
from ..docstring import leading_emoji

# Constants
ROOT_TITLE: str = "API reference"
""" Title of the root package's page, which the header shows as a tab. """


# Functions
def write_module_pages(project_dir: str, modules_dir: str) -> None:
	""" Write one reStructuredText page per package of ``project_dir`` into ``modules_dir``, named after its dotted path.

	A folder holding Python files without an ``__init__.py`` counts as a namespace package.
	Packages and modules whose name starts with an underscore are left out.
	"""
	root: Path = Path(project_dir)
	packages: set[Path] = {
		folder
		for module in root.rglob("*.py") if is_public(module.parent.relative_to(root))
		for folder in (module.parent, *module.parent.parents) if folder.is_relative_to(root)
	}
	for package in sorted(packages):
		dotted: str = ".".join((root.name, *package.relative_to(root).parts))
		subpackages: list[str] = [f"{dotted}.{child.name}" for child in sorted(packages) if child.parent == package]
		with super_open(f"{modules_dir}/{dotted}.rst", "w", encoding="utf-8") as f:
			title: str = ROOT_TITLE if package == root else titled(package / "__init__.py")
			exported: dict[str, list[str]] = {} if package == root else exported_names(package / "__init__.py")
			f.write(package_page(package, dotted, title, subpackages, exported))

def is_public(relative_path: Path) -> bool:
	""" Whether no part of a path under the project starts with an underscore or a dot.

	>>> is_public(Path("typing/runtime.py")), is_public(Path("typing/__init__.py")), is_public(Path("__pycache__"))
	(True, False, False)
	"""
	return not any(part.startswith(("_", ".")) for part in relative_path.parts)

def titled(source: Path) -> str:
	""" Name of a module or package, after the emoji opening its docstring if any.

	Args:
		source: The module's file, or the ``__init__.py`` of a package, which may not exist for a namespace package
	"""
	name: str = source.parent.name if source.name == "__init__.py" else source.stem
	docstring: str | None = ast.get_docstring(ast.parse(source.read_text(encoding="utf-8"))) if source.exists() else None
	return f"{emoji} {name}" if (emoji := leading_emoji(docstring)) else name

def exported_names(init: Path) -> dict[str, list[str]]:
	""" Names an ``__init__.py`` imports from each module beside it, keyed by module name, empty when the file does not exist. """
	if not init.exists():
		return {}
	exported: dict[str, list[str]] = {}
	for node in ast.walk(ast.parse(init.read_text(encoding="utf-8"))):
		if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module:
			exported.setdefault(node.module, []).extend(alias.name for alias in node.names)
	return exported

def heading(title: str, underline: str) -> list[str]:
	""" Lines of a reStructuredText heading, underlined twice its length since an emoji takes two columns. """
	return [title, underline * 2 * len(title), ""]

def package_page(package: Path, dotted: str, title: str, subpackages: list[str], exported: dict[str, list[str]]) -> str:
	""" reStructuredText of a package's page.

	Args:
		dotted:      Import path of the package, ex: "stouputils.typing"
		subpackages: Import paths of the packages directly below it, which get pages of their own
		exported:    Names the package imports from each of its modules, documenting every module in full when none matches
	"""
	lines: list[str] = heading(title, "=")
	if (package / "__init__.py").exists():
		lines += [f".. automodule:: {dotted}", ""]
	if subpackages:
		lines += [".. toctree::", "   :maxdepth: 1", "", *(f"   {name}" for name in subpackages), ""]

	modules: list[Path] = sorted(path for path in package.glob("*.py") if is_public(Path(path.name)))
	if any(module.stem in exported for module in modules):
		modules = [module for module in modules if module.stem in exported]
	for module in modules:
		names: list[str] = exported.get(module.stem, ["*"])
		members: list[str] = [] if "*" in names else [f"   :members: {', '.join(names)}"]
		lines += [*heading(titled(module), "-"), f".. automodule:: {dotted}.{module.stem}", *members, ""]
	return "\n".join(lines)

