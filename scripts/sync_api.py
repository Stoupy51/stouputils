""" Regenerate the mechanical parts of the package layout: re-export lists and lazy import markers.

Explicit re-exports are what makes PEP 810 lazy imports work, since a star import resolves every
deferred name at once. Maintaining those lists by hand is the price, so this script derives them
from the source instead: add a function to a module, run this, and the parent packages follow.

Run ``python scripts/sync_api.py`` to rewrite the tree, or ``--check`` to fail without writing,
which is what CI uses.
"""
# Imports
import ast
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Constants
ROOT: Path = Path(__file__).resolve().parent.parent / "stouputils"
""" Root of the package this script maintains. """

MARKER_HEADER: str = "# Lazy imports (PEP 810), ignored before Python 3.15"
""" Comment introducing the __lazy_modules__ declaration. """

MARKER_MODULE: str = "lazy"
""" Module holding the shared ALWAYS_LAZY marker, which never declares the marker itself. """

INTERNAL: frozenset[str] = frozenset({
	"stouputils.config",
	"stouputils.lazy",
	"stouputils.applications",
	"stouputils.data_science",
	"stouputils.installer",
	"stouputils.mlflow",
})
""" Modules deliberately kept out of the flat namespace, reached through their own import path. """

MARKER_PATTERN: re.Pattern[str] = re.compile(
	rf"{re.escape(MARKER_HEADER)}\nfrom \.+{MARKER_MODULE} import ALWAYS_LAZY\n\n__lazy_modules__ = ALWAYS_LAZY\n\n"
)
""" The generated declaration, matched whole so a partial strip can never leave a duplicate behind. """


# Classes
@dataclass
class Module:
	""" One source file, described well enough to regenerate the parts this script owns. """
	fqn: str
	""" Fully qualified module name, ex: "stouputils.decorators.retrying". """
	path: Path
	""" Source file path. """
	is_package: bool
	""" Whether the file is an __init__.py. """
	defined: list[str] = field(default_factory=list[str])
	""" Public names defined at top level, in source order. """
	explicit_all: list[str] | None = None
	""" Contents of __all__ when the module declares one, which then wins over everything else. """
	reexports: dict[str, tuple[int, int]] = field(default_factory=dict[str, tuple[int, int]])
	""" Re-exported module mapped to the line range of its import statement, 0-indexed and half open. """
	imports: set[str] = field(default_factory=set[str])
	""" Every module this one imports from, whatever form the import takes. """

	@property
	def package(self) -> str:
		""" Name of the package this module lives in. """
		return self.fqn if self.is_package else self.fqn.rsplit(".", 1)[0]


class Analyzer:
	""" Static reader of the package, deliberately never importing it so missing extras cannot break it. """

	@staticmethod
	def fqn_of(path: Path) -> str:
		""" Convert a source path to its fully qualified module name. """
		parts: list[str] = list(path.relative_to(ROOT.parent).parts)
		parts[-1] = parts[-1].removesuffix(".py")
		if parts[-1] == "__init__":
			parts.pop()
		return ".".join(parts)

	@staticmethod
	def resolve(module: Module, level: int, name: str | None) -> str:
		""" Resolve a relative import against the module doing the importing. """
		parts: list[str] = module.package.split(".")
		base: list[str] = parts[: len(parts) - (level - 1)] if level > 1 else parts
		return ".".join([*base, name] if name else base)

	@staticmethod
	def defined_by(node: ast.stmt) -> list[str]:
		""" Return the public names a top level statement binds. """
		match node:
			case ast.FunctionDef() | ast.AsyncFunctionDef() | ast.ClassDef():
				return [node.name] if not node.name.startswith("_") else []
			case ast.TypeAlias():
				return [node.name.id] if not node.name.id.startswith("_") else []
			case ast.Assign():
				return [t.id for t in node.targets if isinstance(t, ast.Name) and not t.id.startswith("_")]
			case ast.AnnAssign():
				target: ast.expr = node.target
				return [target.id] if isinstance(target, ast.Name) and not target.id.startswith("_") else []
			case _:
				return []

	@staticmethod
	def read(path: Path) -> Module:
		""" Parse one source file. """
		module: Module = Module(fqn=Analyzer.fqn_of(path), path=path, is_package=path.name == "__init__.py")
		tree: ast.Module = ast.parse(path.read_text(encoding="utf-8").replace("\r\n", "\n"))
		for node in tree.body:
			module.defined.extend(n for n in Analyzer.defined_by(node) if n not in module.defined)
			if isinstance(node, ast.Assign) and isinstance(node.value, ast.List):
				if any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets):
					module.explicit_all = [
						element.value for element in node.value.elts
						if isinstance(element, ast.Constant) and isinstance(element.value, str)
					]
			if isinstance(node, ast.ImportFrom):
				target: str = Analyzer.resolve(module, node.level, node.module) if node.level else (node.module or "")
				module.imports.add(target)
				# A statement whose every name uses the redundant "name as name" form is a re-export block
				if node.names and all(alias.asname == alias.name for alias in node.names):
					module.reexports[target] = (node.lineno - 1, node.end_lineno or node.lineno)
		return module

	@staticmethod
	def read_all() -> dict[str, Module]:
		""" Parse every source file in the package. """
		return {
			Analyzer.fqn_of(path): Analyzer.read(path)
			for path in sorted(ROOT.rglob("*.py")) if "__pycache__" not in path.parts
		}

	@staticmethod
	def exports_of(fqn: str, modules: dict[str, Module], seen: frozenset[str] = frozenset()) -> list[str]:
		""" Return every public name a module exposes, following its own re-exports. """
		module: Module | None = modules.get(fqn)
		if module is None or fqn in seen:
			return []
		if module.explicit_all is not None:
			return sorted(module.explicit_all)
		names: set[str] = set(module.defined)
		for target in module.reexports:
			names.update(Analyzer.exports_of(target, modules, seen | {fqn}))
		return sorted(names)


class Renderer:
	""" Builder of the two blocks this script owns. """

	@staticmethod
	def sort_key(name: str) -> tuple[int, str]:
		""" Order names the way ruff's isort does, constants first, then classes, then the rest. """
		if name.isupper():
			return (0, name.lower())
		return (1 if name[:1].isupper() else 2, name.lower())

	@staticmethod
	def reexport(target: str, package: str, names: list[str], trailing: str) -> list[str]:
		""" Render one explicit re-export statement, in the redundant alias form pyright requires. """
		relative: str = "." + target.removeprefix(package + ".")
		body: list[str] = [f"\t{name} as {name}," for name in sorted(names, key=Renderer.sort_key)]
		return [f"from {relative} import (", *body, f"){trailing}"]

	@staticmethod
	def marker(module: Module) -> list[str]:
		""" Render the lazy import declaration, with the dot depth this module needs. """
		dots: str = "." * len(module.package.split("."))
		return [MARKER_HEADER, f"from {dots}{MARKER_MODULE} import ALWAYS_LAZY", "", "__lazy_modules__ = ALWAYS_LAZY", ""]

	@staticmethod
	def insertion_point(lines: list[str], tree: ast.Module) -> int:
		""" Find where the marker belongs: after any docstring and any __future__ import. """
		point: int = 0
		first: ast.stmt = tree.body[0]
		if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
			point = first.end_lineno or 1
		futures: list[int] = [
			node.end_lineno or node.lineno for node in tree.body
			if isinstance(node, ast.ImportFrom) and node.module == "__future__"
		]
		if futures:
			point = max(point, max(futures))
		elif any(line.strip() == "# Imports" for line in lines[point:]):
			return next(index for index in range(point, len(lines)) if lines[index].strip() == "# Imports")
		while point < len(lines) and not lines[point].strip():
			point += 1
		return point


class Syncer:
	""" Rewriter keeping every generated block in step with the source. """

	@staticmethod
	def strip_marker(text: str, fqn: str) -> str:
		""" Drop a previously generated marker block, matching it whole so nothing is left behind. """
		stripped: str = MARKER_PATTERN.sub("", text)
		if "__lazy_modules__" in stripped:
			raise SystemExit(f"{fqn} declares __lazy_modules__ by hand, remove it and let this script own it")
		return stripped

	@staticmethod
	def sync(module: Module, modules: dict[str, Module]) -> str | None:
		""" Produce the new source for one module, or None when nothing needs to change. """
		with module.path.open(encoding="utf-8", newline="") as file:
			original: str = file.read()
		newline: str = "\r\n" if "\r\n" in original else "\n"
		lines: list[str] = original.replace("\r\n", "\n").split("\n")

		# Two submodules can define the same name, so the alphabetically last one keeps it.
		# That is the module a star import used to leave standing, and it stays stable once isort sorts the blocks.
		owner: dict[str, str] = {}
		for target in sorted(module.reexports):
			if target not in modules:
				raise SystemExit(f"{module.fqn} re-exports {target!r}, which does not exist")
			owner.update(dict.fromkeys(Analyzer.exports_of(target, modules), target))

		# Refresh the blocks from the bottom up, so the earlier line numbers stay valid
		for target, (start, end) in sorted(module.reexports.items(), key=lambda item: item[1], reverse=True):
			comment: re.Match[str] | None = re.search(r"\s*#.*$", lines[end - 1])
			trailing: str = comment.group(0) if comment else ""
			names: list[str] = [name for name, holder in owner.items() if holder == target]
			lines[start:end] = Renderer.reexport(target, module.package, names, trailing)

		if module.fqn != f"{ROOT.name}.{MARKER_MODULE}":
			lines = Syncer.strip_marker("\n".join(lines), module.fqn).split("\n")
			offset: int = Renderer.insertion_point(lines, ast.parse("\n".join(lines)))
			lines = [*lines[:offset], *Renderer.marker(module), *lines[offset:]]

		updated: str = "\n".join(lines).replace("\n", newline)
		return updated if updated != original else None

	@staticmethod
	def collisions(modules: dict[str, Module]) -> list[str]:
		""" Report submodules whose name shadows a name their own package binds.

		Such a module cannot be deferred: the import system overwrites the unresolved binding with
		the module object, so the package ends up exposing a module where a function is expected.
		"""
		problems: list[str] = []
		for fqn in modules.keys():
			children: set[str] = {other.rsplit(".", 1)[-1] for other in modules if other.rsplit(".", 1)[0] == fqn}
			for name in sorted(children & set(Analyzer.exports_of(fqn, modules))):
				problems.append(f"{fqn}.{name} is both a submodule and an exported name, rename the module")
		return problems

	@staticmethod
	def unexported(modules: dict[str, Module]) -> list[str]:
		""" Report modules no package re-exports, so a new one is not silently left out of the API.

		Packages driving their exports through __all__ manage their own children, and the modules
		listed in INTERNAL are kept out of the flat namespace on purpose.
		"""
		reexported: set[str] = {target for module in modules.values() for target in module.reexports}
		forgotten: list[str] = []
		for fqn, module in sorted(modules.items()):
			parent: Module | None = modules.get(fqn.rsplit(".", 1)[0])
			if fqn in reexported or fqn in INTERNAL or fqn == ROOT.name or not module.defined:
				continue
			if parent is None or parent.explicit_all is not None:
				continue
			forgotten.append(fqn)
		return forgotten


# Functions
def main() -> int:
	""" Sync the tree, or check it, depending on the command line. """
	check_only: bool = "--check" in sys.argv
	modules: dict[str, Module] = Analyzer.read_all()

	problems: list[str] = Syncer.collisions(modules)
	for problem in problems:
		print(f"error: {problem}")

	changed: list[str] = []
	for fqn, module in modules.items():
		updated: str | None = Syncer.sync(module, modules)
		if updated is not None:
			changed.append(fqn)
			if not check_only:
				with module.path.open("w", encoding="utf-8", newline="") as file:
					file.write(updated)

	for fqn in Syncer.unexported(modules):
		print(f"note: {fqn} is not re-exported by any package, add it by hand if that is wrong")

	if check_only and changed:
		print(f"\nerror: {len(changed)} modules are out of sync, run: python scripts/sync_api.py")
		for fqn in changed:
			print(f"    {fqn}")
	elif changed:
		print(f"\n{len(changed)} modules updated")
	else:
		print("\nalready in sync")
	return 1 if problems or (check_only and changed) else 0


if __name__ == "__main__":
	raise SystemExit(main())

