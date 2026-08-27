""" Word by word coloring used by the print helpers.

Every predicate here works on a single whitespace separated token, so the caller only has to split
the text once and join the results back.
"""
# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import builtins
import re
from dataclasses import dataclass
from typing import ClassVar

from ..config import StouputilsConfig as Cfg


# Classes
@dataclass
class WordColorizer:
	""" Colors the tokens of a text, one word at a time.

	Examples:
		>>> WordColorizer().colorize_text("Found 42 items") == f"Found {Cfg.MAGENTA}42{Cfg.RESET} items"
		True
	"""
	color: str = Cfg.MAGENTA
	""" ANSI color code applied to every recognized token. """

	EXCEPTION_NAMES: ClassVar[frozenset[str]] = frozenset(
		name for name in dir(builtins)
		if isinstance(getattr(builtins, name, None), type) and issubclass(getattr(builtins, name), BaseException)
	)
	""" Every built-in exception name, colored in bold. """
	BUILTIN_FUNCTIONS: ClassVar[frozenset[str]] = frozenset(
		name for name in dir(builtins)
		if callable(getattr(builtins, name, None))
		and not (isinstance(getattr(builtins, name, None), type) and issubclass(getattr(builtins, name), BaseException))
	)
	""" Every built-in callable that is not an exception. """
	KEYWORDS: ClassVar[frozenset[str]] = frozenset({"class", "dtype", "type"})
	""" Words always colored, whatever they look like. """

	AFFIX_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"^(\W*)(.*?)(\W*)$", re.ASCII)
	""" Splits a token into leading punctuation, core text and trailing punctuation. """
	QUOTED_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"^(\W*?)('[^']*'|\"[^\"]*\")(\W*)$")
	""" Matches a token holding a quoted string, ex: "'some name':". """
	NUMBER_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"(\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)")
	""" Matches a number anywhere inside a token, ex: the two numbers of "scale=(0.5,". """
	WORD_SPLIT_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"(\s+)")
	""" Splits a text into tokens, keeping the whitespace as tokens of its own. """

	def wrap(self, text: str, bold: bool = False) -> str:
		""" Surround a text with the color code and the reset code.

		Args:
			text (str):  Text to color
			bold (bool): Whether the text is also written in bold
		Returns:
			str: Colored text
		"""
		return f"{Cfg.BOLD if bold else ''}{self.color}{text}{Cfg.RESET}"

	@staticmethod
	def is_filepath(word: str) -> bool:
		""" Check if a word looks like a file path.

		Args:
			word (str): Token to check, quotes included
		Returns:
			bool: Whether the token looks like a path

		Examples:
			>>> WordColorizer.is_filepath("./data.csv"), WordColorizer.is_filepath("batches/images")
			(True, False)
		"""
		clean_word: str = word.strip("\"'")

		if "/" in clean_word or "\\" in clean_word:

			# Has a file extension (2-4 chars after last dot)
			parts: list[str] = clean_word.split(".")
			if "." in clean_word and len(parts) >= 2 and 2 <= len(parts[-1]) <= 4:
				return True

			# Without an extension, ask for more components to avoid false positives like "batches/images"
			separator: str = "/" if "/" in clean_word else "\\"
			parts = clean_word.split(separator)
			if len(parts) >= 3 or (len(parts) >= 2 and parts[0] in ("", ".", "..")):
				return True

		# Windows absolute path (C:\, D:\, etc.) or unix absolute path
		return (len(clean_word) > 3 and clean_word[1:3] == ":\\") or clean_word.startswith("/")

	@staticmethod
	def is_number(word: str) -> bool:
		""" Check if a word is a number.

		Args:
			word (str): Token to check
		Returns:
			bool: Whether the token parses as a float

		Examples:
			>>> WordColorizer.is_number("3.0e+10"), WordColorizer.is_number("42ms")
			(True, False)
		"""
		try:
			float(word)
			return True
		except ValueError:
			return False

	@staticmethod
	def alphanumeric_of(word: str) -> str:
		""" Keep only the alphanumeric characters of a word, ex: "(ValueError:" gives "ValueError". """
		return "".join(character for character in word if character.isalnum())

	@staticmethod
	def function_name_of(word: str) -> str:
		""" Function name held by a word, empty when there is none.

		Args:
			word (str): Token to check
		Returns:
			str: Name of the called function, ex: "print" for "print()"

		Examples:
			>>> WordColorizer.function_name_of("print()"), WordColorizer.function_name_of("nothing")
			('print()', '')
		"""
		clean_word: str = word.rstrip(".,;:!?")
		if clean_word.endswith(("()", "(")) or clean_word in WordColorizer.BUILTIN_FUNCTIONS:
			return clean_word
		return ""

	def colorize_function(self, core: str) -> str:
		""" Color the function name held by a token, leaving the rest of the token untouched.

		Args:
			core (str): Token without its leading and trailing punctuation
		Returns:
			str: Token with its function name colored
		"""
		function_name: str = self.function_name_of(core)
		start: int = core.find(function_name)
		if start == -1:
			return self.wrap(core)
		return f"{core[:start]}{self.wrap(function_name)}{core[start + len(function_name):]}"

	def colorize_core(self, core: str) -> str | None:
		""" Color a token stripped from its punctuation, or return None when nothing matches.

		Args:
			core (str): Token without its leading and trailing punctuation
		Returns:
			str | None: Colored token, or None when the token deserves no color
		"""
		if self.is_filepath(core):
			return self.wrap(core)
		if self.alphanumeric_of(core) in self.EXCEPTION_NAMES:
			return self.wrap(core, bold=True)
		if self.is_number(core) or self.alphanumeric_of(core) in self.KEYWORDS:
			return self.wrap(core)
		if self.function_name_of(core):
			return self.colorize_function(core)
		return None

	def colorize_word(self, word: str) -> str:
		""" Color one token, falling back on coloring the numbers it contains.

		Args:
			word (str): Token to color, whitespace included
		Returns:
			str: Colored token
		"""
		if word.isspace():
			return word

		# A whole path is colored as-is, quotes and punctuation included
		if self.is_filepath(word):
			return self.wrap(word)

		quoted: re.Match[str] | None = self.QUOTED_PATTERN.match(word)
		if quoted:
			return f"{quoted.group(1)}{self.wrap(quoted.group(2))}{quoted.group(3)}"

		affixes: re.Match[str] | None = self.AFFIX_PATTERN.match(word)
		prefix, core, suffix = affixes.groups() if affixes else ("", word, "")
		colored_core: str | None = self.colorize_core(core)
		if colored_core is not None:
			return f"{prefix}{colored_core}{suffix}"

		return self.NUMBER_PATTERN.sub(lambda match: self.wrap(match.group()), word)

	def colorize_text(self, text: str) -> str:
		""" Color every token of a text.

		Args:
			text (str): Text to color
		Returns:
			str: Colored text
		"""
		return "".join(self.colorize_word(word) for word in self.WORD_SPLIT_PATTERN.split(text))

