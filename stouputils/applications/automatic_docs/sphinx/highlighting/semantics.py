""" Recovery of the token distinctions Pygments' Python lexer does not make.

An editor colours ``task: str = "all"`` in three different ways because its grammar knows that ``task`` is a
variable, ``str`` a type and ``"all"`` a string.
Pygments only knows the third: it tags an identifier as ``Name.Function`` or ``Name.Class`` when a literal ``def``
or ``class`` introduces it, and emits a bare ``Name`` for every call, annotation, attribute and argument.

This module restores the missing distinctions as a stream filter rather than as a lexer subclass, because a filter
also reaches the Python nested inside a doctest block, which ``PythonConsoleLexer`` lexes with its own instance.
Being purely lexical, it follows the same conventions an editor's grammar uses before a type checker weighs in:
a name followed by a parenthesis is a call, and a CamelCase name is a type.
"""
# Lazy imports (PEP 810), ignored before Python 3.15
from .....lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import re
from collections.abc import Iterable, Iterator

from pygments.filter import Filter
from pygments.lexer import Lexer
from pygments.token import (
	Keyword,
	Name,
	Text,
	_TokenType as TokenType,  # pyright: ignore[reportPrivateUsage]
)

# Constants
TYPE_BUILTINS: frozenset[str] = frozenset({
	"bool", "bytearray", "bytes", "classmethod", "complex", "dict", "enumerate", "filter", "float", "frozenset",
	"int", "list", "map", "memoryview", "object", "property", "range", "reversed", "set", "slice", "staticmethod",
	"str", "super", "tuple", "type", "zip",
})
""" Builtins Python implements as classes, which an editor colours as types while ``print`` or ``len`` stay functions. """

DECLARATION_KEYWORDS: frozenset[str] = frozenset({"class", "def", "lambda"})
""" Keywords that introduce a binding, coloured apart from control flow the way ``def`` differs from ``return``. """

CAMEL_CASE: re.Pattern[str] = re.compile(r"_{0,2}[A-Z][A-Za-z0-9_]*[a-z][A-Za-z0-9_]*")
""" A leading capital plus a lowercase somewhere after it, which keeps ``DataContext`` apart from ``TINY_DEBUG``. """


# Classes
class VSCodeSemanticFilter(Filter):
	""" Refine ``Name`` and ``Keyword`` tokens so a palette can colour calls, types and declarations apart.
	Examples:
		>>> from pygments.lexers.python import PythonLexer
		>>> lexer = PythonLexer()
		>>> lexer.add_filter(VSCodeSemanticFilter())
		>>> for token, text in lexer.get_tokens("ctx = DataContext(load(x))"):
		...     if text.strip():
		...         print(f"{text:<12} {token}")
		ctx          Token.Name
		=            Token.Operator
		DataContext  Token.Name.Class
		(            Token.Punctuation
		load         Token.Name.Function
		(            Token.Punctuation
		x            Token.Name
		)            Token.Punctuation
		)            Token.Punctuation
	"""

	def retype(self, ttype: TokenType, value: str) -> tuple[TokenType, str]:
		""" Refine a token that needs no lookahead to classify.

		Args:
			ttype: Token type the lexer produced
			value: Text the token covers
		Returns:
			The token, refined when it deserves it
		Examples:
			>>> from pygments.token import Keyword, Name
			>>> VSCodeSemanticFilter().retype(Name.Builtin, "str")
			(Token.Name.Class, 'str')
			>>> VSCodeSemanticFilter().retype(Name.Builtin, "print")
			(Token.Name.Builtin, 'print')
			>>> VSCodeSemanticFilter().retype(Keyword, "def")
			(Token.Keyword.Declaration, 'def')
		"""
		if ttype is Name.Builtin and value in TYPE_BUILTINS:
			return Name.Class, value
		if ttype is Keyword and value in DECLARATION_KEYWORDS:
			return Keyword.Declaration, value
		return ttype, value

	def classify_name(self, value: str, following: str) -> TokenType:
		""" Decide what a bare ``Name`` really is, given the next significant text.

		A type wins over a call so that ``DataContext(ctx)`` reads as a constructor rather than as a function.

		Args:
			value:     The identifier itself
			following: Text of the next non-whitespace token, empty at the end of the stream
		Returns:
			The refined token type
		Examples:
			>>> VSCodeSemanticFilter().classify_name("DataContext", "(")
			Token.Name.Class
			>>> VSCodeSemanticFilter().classify_name("load_split", "(")
			Token.Name.Function
			>>> VSCodeSemanticFilter().classify_name("task", "=")
			Token.Name
		"""
		if CAMEL_CASE.fullmatch(value):
			return Name.Class
		if following.startswith("("):
			return Name.Function
		return Name

	def filter(self, lexer: Lexer | None, stream: Iterable[tuple[TokenType, str]]) -> Iterator[tuple[TokenType, str]]:
		""" Rewrite the token stream, holding each ``Name`` back until the next significant token is known.

		Args:
			lexer:  Lexer that produced the stream, unused
			stream: Pairs of token type and text
		Returns:
			The rewritten pairs
		"""
		pending: str = ""
		spacing: list[tuple[TokenType, str]] = []
		for ttype, value in stream:
			if pending and ttype not in Text:
				yield self.classify_name(pending, value), pending
				yield from spacing
				pending, spacing = "", []
			if pending:
				spacing.append((ttype, value))
			elif ttype is Name:
				pending = value
			else:
				yield self.retype(ttype, value)

		# A trailing name has nothing after it, so it can only be classified on its own spelling
		if pending:
			yield self.classify_name(pending, ""), pending
			yield from spacing

