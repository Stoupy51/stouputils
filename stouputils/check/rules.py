""" The rules ``stouputils check`` knows, the settings a project tunes them with, and the violations they report. """

# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import tomllib
from collections.abc import Collection
from dataclasses import dataclass, field
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
	"long-docstring": "A function or class docstring over the line limit",
	"module-docstring-position": "A module docstring below line 1",
	"constant-comment": "A module constant documented by a trailing comment instead of a docstring below it",
	"syntax-error": "A Python file the tokenizer or the parser rejects",
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
class CheckConfig:
	""" Settings of the ``[tool.stouputils.check]`` table of a ``pyproject.toml``, keys spelled with dashes.

	>>> CheckConfig(ignore=["tab-indentation", "space-alignment"]).final_newlines
	{'.py': 2, '.json': 1, '.md': 2}
	>>> CheckConfig().initial_newlines
	{'.md': 1, '.mcfunction': 1}
	>>> CheckConfig(ignore=["tabs"])  # doctest: +ELLIPSIS
	Traceback (most recent call last):
		...
	ValueError: Unknown rules in ignore: ['tabs'], the known ones are banned-characters, ...
	"""

	ignore: Collection[str] = ()
	""" Rules left unchecked, by their name in :data:`RULES`. """
	final_newlines: dict[str, int] = field(default_factory=lambda: {".py": 2, ".json": 1, ".md": 2, ".yml": 2, ".yaml": 2})
	""" Exact number of newline characters a file ends with, by suffix, replacing the defaults as a whole. """
	initial_newlines: dict[str, int] = field(default_factory=lambda: {".md": 1, ".yml": 1, ".yaml": 1, ".mcfunction": 1})
	""" Exact number of newline characters a file starts with, by suffix, replacing the defaults as a whole. """
	docstring_max_lines: int = 15
	""" Longest docstring of a function or a class, doctests included. """
	comment_max_lines: int = 2
	""" Longest block of consecutive comment lines. """
	fragment_max_words: int = 3
	""" Most words a clause cut by a line break may leave alone on one side of it. """

	def __post_init__(self) -> None:
		if unknown := sorted(set(self.ignore) - RULES.keys()):
			raise ValueError(f"Unknown rules in ignore: {unknown}, the known ones are {', '.join(RULES)}")

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
				return cls(**{key.replace("-", "_"): value for key, value in table.items()})  # pyright: ignore[reportArgumentType]
		return cls()

