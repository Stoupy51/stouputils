""" The rules ``stouputils check`` knows, the settings a project tunes them with, and the violations they report. """

# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import tomllib
from collections.abc import Collection, Iterable, Iterator
from dataclasses import dataclass, field
from fnmatch import fnmatchcase
from functools import cache
from pathlib import Path
from typing import Self

# Constants
RULES: dict[str, str] = {
	"banned-characters": "Long dashes, ellipsis, multiplication sign, arrows, curly quotes and box-drawing comment banners",
	"final-newlines": "A file not ending with the configured number of newline characters",
	"initial-newlines": "A file not starting with the configured number of newline characters",
	"tab-indentation": "Python code indented with a space instead of tabs",
	"space-alignment": "Python code aligned with a tab after the first character instead of spaces",
	"stranded-fragment": "A line break in a comment or docstring leaving a few words of a clause alone",
	"split-span": "Inline code or a quote opened on one line of a comment or docstring and closed on another",
	"long-comment": "A block of consecutive comment lines over the limit",
	"examples-header": "An ``Examples:`` header above doctests, which ``>>>`` already marks",
	"typed-argument": "An ``Args:`` entry repeating the type the signature carries",
	"long-docstring": "A function or class docstring over the line limit, its code-block and image directives left out",
	"module-docstring-position": "A module docstring below line 1",
	"constant-comment": "A module constant documented by a trailing comment instead of a docstring below it",
	"syntax-error": "A Python file the tokenizer or the parser rejects",
	"unused-ignore": "A suppression comment naming no rule, an unknown one, or one it does not silence",
}
""" Every rule by the name ``ignore`` takes, with what it reports. """

# Classes
@dataclass(frozen=True, order=True)
class Violation:
	""" One rule broken at one line, or on every checked line of a range. """

	line: int
	rule: str
	message: str
	end_line: int | None = field(default=None, compare=False)
	""" Last line of the range, None for a single line. """

	@property
	def span(self) -> str:
		""" The line, or the range of lines, as written in a report.

		>>> Violation(3, "long-comment", "").span, Violation(3, "tab-indentation", "", end_line=9).span
		('3', '3-9')
		"""
		return f"{self.line}-{self.end_line}" if self.end_line else str(self.line)


@dataclass(frozen=True)
class Suppression:
	""" Rules a ``# stp: ignore[...]`` or ``# stouputils: ignore[...]`` comment silences, and on which lines.

	>>> suppression = Suppression(line=4, rules=("long-docstring",), lines=range(2, 5))
	>>> suppression.covers(Violation(2, "long-docstring", "")), suppression.covers(Violation(2, "long-comment", ""))
	(True, False)
	>>> Suppression(line=1, rules=("long-comment",), lines=None).covers(Violation(90, "long-comment", ""))
	True
	"""

	line: int
	""" Line of the comment, where a rule it does not use is reported. """
	rules: tuple[str, ...]
	lines: range | None
	""" Lines whose violations it silences, None for the whole file. """

	def covers(self, violation: Violation) -> bool:
		""" Whether this comment silences the violation. """
		return violation.rule in self.rules and (self.lines is None or violation.line in self.lines)

	@staticmethod
	def unused(suppressions: Iterable["Suppression"], violations: Collection[Violation]) -> Iterator[Violation]:
		""" An ``unused-ignore`` for every rule a comment names without silencing anything.

		>>> found = [Violation(3, "long-docstring", "")]
		>>> stale = Suppression(line=3, rules=("long-docstring", "long-comment", "tabs"), lines=range(1, 4))
		>>> [v.message for v in Suppression.unused([stale], found)]
		["'long-comment' silences nothing here", "unknown rule 'tabs'"]
		>>> [v.message for v in Suppression.unused([Suppression(line=1, rules=(), lines=None)], found)]
		['names no rule, write ignore[rule-name]']
		"""
		for suppression in suppressions:
			if not suppression.rules:
				yield Violation(suppression.line, "unused-ignore", "names no rule, write ignore[rule-name]")
			for rule in suppression.rules:
				if rule not in RULES:
					yield Violation(suppression.line, "unused-ignore", f"unknown rule {rule!r}")
				elif not any(violation.rule == rule and suppression.covers(violation) for violation in violations):
					yield Violation(suppression.line, "unused-ignore", f"{rule!r} silences nothing here")


@dataclass(frozen=True)
class CheckConfig:
	""" Settings of the ``[tool.stouputils.check]`` table of a ``pyproject.toml``, keys spelled with dashes.

	>>> CheckConfig(ignore=["tab-indentation", "space-alignment"]).final_newlines
	{'.py': 2, '.json': 1, '.md': 2, '.yml': 2, '.yaml': 2}
	>>> CheckConfig().initial_newlines
	{'.md': 1, '.yml': 1, '.yaml': 1, '.mcfunction': 1}
	>>> CheckConfig(per_file_ignores={"*.json": ["tabs"]})  # doctest: +ELLIPSIS
	Traceback (most recent call last):
		...
	ValueError: Unknown rules in ignore: ['tabs'], the known ones are banned-characters, ...
	"""

	ignore: Collection[str] = ()
	""" Rules left unchecked, by their name in :data:`RULES`. """
	per_file_ignores: dict[str, list[str]] = field(default_factory=dict[str, list[str]])
	""" Rules left unchecked in the files a glob matches, relative to ``root``, or anywhere when it holds no slash. """
	root: Path = Path()
	""" Directory of the ``pyproject.toml`` the settings come from, which ``per_file_ignores`` patterns are relative to. """
	final_newlines: dict[str, int] = field(default_factory=lambda: {".py": 2, ".json": 1, ".md": 2, ".yml": 2, ".yaml": 2})
	""" Exact number of newline characters a file ends with, by suffix, replacing the defaults as a whole. """
	initial_newlines: dict[str, int] = field(default_factory=lambda: {".md": 1, ".yml": 1, ".yaml": 1, ".mcfunction": 1})
	""" Exact number of newline characters a file starts with, by suffix, replacing the defaults as a whole. """
	docstring_max_lines: int = 15
	""" Longest docstring of a function or a class, doctests included, ``.. code-block::`` and ``.. image::`` directives left out. """
	comment_max_lines: int = 2
	""" Longest block of consecutive comment lines. """
	fragment_max_words: int = 3
	""" Most words a clause cut by a line break may leave alone on one side of it. """

	def __post_init__(self) -> None:
		named: set[str] = {*self.ignore, *(rule for rules in self.per_file_ignores.values() for rule in rules)}
		if unknown := sorted(named - RULES.keys()):
			raise ValueError(f"Unknown rules in ignore: {unknown}, the known ones are {', '.join(RULES)}")

	def ignored_rules(self, path: Path) -> set[str]:
		""" Rules left unchecked in one file: the global ones and those of every ``per_file_ignores`` pattern it matches.

		>>> patterns = {"tests/**": ["final-newlines"], "*.json": ["banned-characters"]}
		>>> config = CheckConfig(ignore=["long-comment"], per_file_ignores=patterns)
		>>> sorted(config.ignored_rules(Path("tests/fixture/data.json")))
		['banned-characters', 'final-newlines', 'long-comment']
		>>> sorted(config.ignored_rules(Path("src/tests.py")))
		['long-comment']
		"""
		resolved: Path = path.resolve()
		root: Path = self.root.resolve()
		relative: str = resolved.relative_to(root).as_posix() if resolved.is_relative_to(root) else resolved.as_posix()
		matched: list[list[str]] = [
			rules for pattern, rules in self.per_file_ignores.items()
			if fnmatchcase(relative, pattern) or ("/" not in pattern and fnmatchcase(resolved.name, pattern))
		]
		return {*self.ignore, *(rule for rules in matched for rule in rules)}

	@classmethod
	@cache
	def for_directory(cls, directory: Path) -> Self:
		""" Settings of the nearest ``pyproject.toml`` holding the table, looking upward like ruff, defaults without one. """
		for folder in (directory, *directory.parents):
			pyproject: Path = folder / "pyproject.toml"
			if not pyproject.is_file():
				continue
			settings: dict[str, dict[str, dict[str, object]]] = tomllib.loads(pyproject.read_text(encoding="utf-8")).get("tool", {})
			table: dict[str, object] | None = settings.get("stouputils", {}).get("check")
			if table is not None:
				return cls(root=folder, **{key.replace("-", "_"): value for key, value in table.items()})  # pyright: ignore[reportArgumentType]
		return cls()

