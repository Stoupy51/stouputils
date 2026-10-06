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
import builtins
from pathlib import Path
from typing import Any

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
	""" Names an ``__init__.py`` re-exports from each module beside it, keyed by module name, empty when the file does not exist.

	A re-export is an ``import x as x`` or a name listed in ``__all__``, the convention type checkers follow.
	A plain import is the package using a helper of its own, which stays out of its API.
	"""
	if not init.exists():
		return {}
	tree: ast.Module = ast.parse(init.read_text(encoding="utf-8"))
	listed: set[str] = dunder_all(tree)
	exported: dict[str, list[str]] = {}
	for node in ast.walk(tree):
		if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module:
			names: list[str] = [alias.name for alias in node.names if alias.asname == alias.name or alias.name in listed]
			if names:
				exported.setdefault(node.module, []).extend(names)
	return exported

def dunder_all(tree: ast.Module) -> set[str]:
	""" Names a module lists in ``__all__``.

	>>> sorted(dunder_all(ast.parse("__all__ = ['b', 'a']")))
	['a', 'b']
	"""
	assignments: list[ast.Assign] = [node for node in ast.walk(tree) if isinstance(node, ast.Assign)]
	return {
		element.value
		for node in assignments if "__all__" in [getattr(target, "id", "") for target in node.targets]
		for element in getattr(node.value, "elts", []) if isinstance(element, ast.Constant) and isinstance(element.value, str)
	}

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

def drop_overloads() -> None:
	""" Make autodoc show the signature of a function's implementation instead of one line per ``@overload`` above it.

	Autodoc reads the overloads from the module analyzer it caches, and only skips them along with every annotation of the site.
	"""
	from sphinx.pycode import ModuleAnalyzer
	analyze = ModuleAnalyzer.analyze

	def analyze_without_overloads(self: ModuleAnalyzer) -> None:
		analyze(self)
		self.overloads.clear()
	ModuleAnalyzer.analyze = analyze_without_overloads

def exact_builtin_references(app: Any, doctree: Any) -> None:
	""" Handler for ``doctree-read`` keeping the builtin names of annotations, like ``type``, from linking to project objects.

	Sphinx looks up an annotation by suffix whenever its node carries ``refspecific``, which it always does, even set to False.
	A builtin then resolves to every attribute of the project sharing its name, and links to the first one.
	"""
	from sphinx.addnodes import pending_xref
	for node in doctree.findall(pending_xref):
		if node.get("refdomain") == "py" and node.get("refspecific") is False and hasattr(builtins, node["reftarget"]):
			del node["refspecific"]

